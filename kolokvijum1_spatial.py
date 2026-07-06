import time
from collections import deque
import geohash
import pandas as pd
from auto_simulator import AutoSimulator
from drive_simulator import DriveSimulator, get_route_coordinates, get_route_coords, load_serbian_roads
from datetime import datetime, timedelta

GEOHASH_INDEX = {}


# ------------------------------
# Učitati podatke o nezgodama
# ------------------------------
def encode_geohash(row):
 
    return geohash.encode(row["Latitude"], row["Longitude"], precision=6)


def load_accidents_data():

    global GEOHASH_INDEX

    df = pd.read_excel('dataset/nez-opendata-2022-20230125.xlsx')
    df.columns = ["idNesreca", "Opstina", "Mesto", "Datum i vreme", "Longitude", "Latitude", "Ishod", "Nacin",
                  "Opis nacina nastanka nezgode"]

    df["geohash"] = df.apply(encode_geohash, axis=1)
    df["Datum i vreme"] = pd.to_datetime(df["Datum i vreme"], format="%d.%m.%Y,%H:%M", errors='coerce')
    df.dropna(subset=['Datum i vreme'], inplace=True)
    df["time_index"] = df["Datum i vreme"].dt.strftime("%H:%M")

    GEOHASH_INDEX = df.groupby('geohash').apply(lambda x: x.to_dict('records')).to_dict()
    print(GEOHASH_INDEX)
    print(f"Učitano {len(df)} nezgoda.")
    print(f"Kreiran Geohash Indeks sa {len(GEOHASH_INDEX)} jedinstvenih Geohash zona.")
    return df


pronadjene_nezgode = deque(maxlen=40)


def check_accident_zone(latituda, longituda, datum_voznje):

    global GEOHASH_INDEX

    car_hash = geohash.encode(latituda, longituda, precision=6)
    car_neighbors = geohash.neighbors(car_hash)

    car_neighbors.append(car_hash)

    now = datum_voznje
    if now == "Nije validan":
        now = datetime.now() - timedelta(days=1095)

    nezgode_cnt = 0
    nezgode_u_blizini = []

    for neighbor_hash in car_neighbors:

        if neighbor_hash in GEOHASH_INDEX:

            for row in GEOHASH_INDEX[neighbor_hash]:

                nezgoda_id = row['idNesreca']

                if nezgoda_id not in pronadjene_nezgode:
                    pronadjene_nezgode.append(nezgoda_id)
                    nezgode_u_blizini.append(row)
                    nezgode_cnt += 1

                    print(
                        f"Nesreća {nezgoda_id} je u blizini vozila, geo hash: {row['geohash']}, datum {row['Datum i vreme']}")

                    event_dt = row['Datum i vreme']
                    event_time = row['time_index']

                    # Provera +- 1 sat
                    lower_dt_hour = now.hour - 1
                    upper_dt_hour = now.hour + 1

                    if lower_dt_hour <= event_dt.hour <= upper_dt_hour:
                        print(
                            f"  -> UPOZORENJE: Vremenska blizina (SATI). Nezgodu se desila oko {event_dt.strftime('%H:%M')}, što je +-1h od {now.strftime('%H:%M')}.")

                    # Provera +- 1 mesec (po danima)
                    lower_dt_month = now - timedelta(days=30)
                    upper_dt_month = now + timedelta(days=30)

                    if lower_dt_month <= event_dt <= upper_dt_month:
                        print(
                            f"  -> UPOZORENJE: Vremenska blizina (MESECI). Nezgodu se desila oko {event_dt.strftime('%d.%m')}, što je +-30 dana od {now.strftime('%d.%m')}")

    if 1 <= nezgode_cnt <= 2:
        print(f"Ovo je umereno opasna deonica, ima {nezgode_cnt} nezgoda")
    elif 3 <= nezgode_cnt <= 5:
        print(f"Ovo je opasna deonica, ima {nezgode_cnt} nezgoda")
    elif nezgode_cnt >= 6:
        print(f"Ovo je veoma opasna deonica, ima {nezgode_cnt} nezgoda")


if __name__ == "__main__":

    # ------------------------------
    # Učitaj podatke o nezgodama (i kreiraj indeks)
    # ------------------------------
    df = load_accidents_data()
    # -------------------------------
    # -------------------------------

    start_city = "Prijepolje"
    end_city = "Užice"

    # Inicijalizacija datum varijable
    datum = "Nije validan"

    unos = input("Unesite datum i vreme (format: YYYY-MM-DD HH:MM:SS): , ako ne zelite samo pritisnite enter: ")
    if unos != "":
        try:
            datum = datetime.strptime(unos, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print("Nevalidan format datuma. Koristiće se trenutno vreme.")

    # 1. Učitaj mrežu puteva Srbije
    G = load_serbian_roads()

    print(f"Ucitana mreža puteva Srbije! {len(G.nodes)} čvorova, {len(G.edges)} ivica.")
    # 2. Odredjivanje koordinata pocetka i kraja rute
    orig, dest = get_route_coordinates(start_city, end_city)

    # 3. Odredjivanje rute
    route_coords, route = get_route_coords(G, orig, dest)

    # 4. Inicijalizacija grafičke mape za voznju rutom
    drive_simulator = DriveSimulator(G, edge_color='lightgray', edge_linewidth=0.5)

    # 5. Prikaz mape sa rutom
    drive_simulator.prikazi_mapu(route_coords, route_color='blue', auto_marker_color='ro', auto_marker_size=8)
    # 6. Inicijalizuj simulator kretanja automobila sa brzinom 250 km/h i intervalom od 1 sekunde
    automobil = AutoSimulator(route_coords, speed_kmh=250, interval=1.0)
    automobil.running = True

    print("\n=== Simulacija pokrenuta ===")
    print("Kontrole: Auto se pomera automatski svakih", automobil.interval, "sekundi")
    print("Za zaustavljanje pritisnite Ctrl+C\n")

    interval_simulacije = 1.0  # sekunde
    # 7. Glavna petlja simulacije
    try:
        step_count = 0
        while automobil.running:
            # Pomeri automobil
            auto_current_pos = automobil.move()
            lat, lon = auto_current_pos

            drive_simulator.move_auto_marker(lat, lon, automobil.get_progress_info(), plot_pause=0.01)

            # Pozovi check_accident_zone samo na svakih 5 koraka
            step_count += 1
            if step_count % 5 == 0:
                # -------------------------------
                # -------------------------------
                check_accident_zone(lat, lon, datum)
                # -------------------------------
                # -------------------------------

            # Proveri da li je stigao na kraj
            if automobil.is_finished():
                print("\n=== Automobil je stigao na destinaciju! ===")
                break

            # Čekaj interval pre sledećeg pomeraja
            time.sleep(interval_simulacije)

    except KeyboardInterrupt:
        print("\n\n=== Simulacija prekinuta ===")