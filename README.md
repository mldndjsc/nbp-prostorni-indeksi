# Accident-Zone Warnings with a Geohash Spatial Index

![Python](https://img.shields.io/badge/Python-3.13-3776AB)
![pandas](https://img.shields.io/badge/pandas-data-150458)
![OSMnx](https://img.shields.io/badge/OSMnx-road%20network-green)

A driving simulator that warns the driver when the car enters a zone with a history of traffic accidents. More than **33,000 real accidents in Serbia** (official open data, 2022) are indexed with a **geohash spatial index**. A car is then simulated along a real road route, and nearby accidents are looked up in constant time while it drives.

Built for the *Advanced Databases* course (spatial indexing) at the School of Computing (RAF), Belgrade.

---

## How it works

```
accidents (.xlsx)  ──►  geohash (precision 6)  ──►  index: { geohash → [accidents] }
                                                              ▲
road graph (OSM) ──► shortest route ──► car simulator ──► position ──► geohash + 8 neighbours ──► lookup
```

1. **Indexing.** Every accident is encoded as a 6-character geohash, a cell of roughly 1.2 km × 0.6 km. Accidents are grouped into a dictionary keyed by geohash. The 2022 dataset produces about 9,000 non-empty cells.
2. **Routing.** The Serbian road network is loaded from a saved OSMnx graph (`serbia_roads.graphml.xml`). The start and end towns are geocoded with Nominatim, and the shortest route by road length is computed with NetworkX. The default route is Prijepolje → Užice.
3. **Simulation.** The car advances along the route at a configurable speed, using geodesic distances between route points. Its position is drawn live on a map with an OpenStreetMap basemap.
4. **Lookup.** Every few steps, the car's geohash and its **8 neighbouring cells** are checked. A cell edge would otherwise hide accidents just across the boundary. This takes 9 dictionary lookups instead of scanning all 33,000 records.
5. **Warnings.**
   - **Danger level** of the road section by the number of nearby accidents: moderate (1–2), dangerous (3–5), very dangerous (6+).
   - **Time-of-day match:** accidents that happened within ±1 hour of the driving time.
   - **Seasonal match:** accidents within ±30 days of the driving date.
   - Recently reported accidents are kept in a bounded queue, so the same accident is not reported twice.

---

## Tech stack

Python · pandas (+ openpyxl) · python-geohash · OSMnx · NetworkX · geopy (Nominatim, geodesic distance) · Matplotlib · contextily

---

## Running

```bash
git clone https://github.com/mldndjsc/nbp-prostorni-indeksi.git
cd nbp-prostorni-indeksi

pip install pandas openpyxl python-geohash osmnx networkx geopy matplotlib contextily
python kolokvijum1_spatial.py
```

When asked, enter a date and time (`YYYY-MM-DD HH:MM:SS`) for the trip. If you press Enter instead, the current moment three years back is used, to match the 2022 data. A map window opens and the car starts driving. Warnings are printed to the console. Stop with `Ctrl+C`.

> Geocoding (Nominatim) and the map basemap need an internet connection.

---

## Data

`dataset/` contains traffic-accident records published as open data by the Ministry of Interior of Serbia, one file per year. Each record includes the municipality, place, date and time, coordinates, outcome (material damage, injured, fatal) and accident type. The simulator uses the 2022 file.

---

## Project structure

```
├── kolokvijum1_spatial.py     # data loading, geohash index, accident-zone checks, main loop
├── drive_simulator.py         # road graph, geocoding, routing, live map
├── auto_simulator.py          # car movement along the route
├── serbia_roads.graphml.xml   # saved OSMnx road network of Serbia
└── dataset/                   # accident open data (.xlsx)
```
