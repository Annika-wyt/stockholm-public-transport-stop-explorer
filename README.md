# Stockholm Public Transport Stop Explorer

A beginner-friendly Python and Streamlit project for exploring public transport
stops in Stockholm. A user will select a stop on a map and see the transport
types, line numbers, and destinations serving it.

## Project status

Phases 1 through 4 are complete. The project includes the mentor-owned GTFS
preprocessing pipeline, beginner-facing data functions, and the interactive
Streamlit application.

## Project structure

```text
.
├── app.py                     # Streamlit map and results interface
├── transport_data.py          # Student-facing data functions
├── prepare_data.py            # Mentor-owned GTFS preparation
├── requirements.txt
├── pyproject.toml             # Pytest configuration
├── data/
│   ├── stations.csv           # Generated map stations
│   ├── stop_services.csv      # Generated services for each station
│   └── station_groups.csv     # Manual grouping rules for related stops
├── tests/
│   ├── fixtures/
│   ├── test_prepare_data.py
│   └── test_transport_data.py
└── sweden-20260801/           # Original GTFS snapshot
```

## Data files

The application will use two small generated files instead of reading the full
GTFS feed at runtime.

`data/stations.csv`:

```csv
station_id,station_name,latitude,longitude
```

`data/stop_services.csv`:

```csv
station_id,transport_type,line,destination
```

`data/station_groups.csv` is a mentor-maintained input for combining related
GTFS stops into one map station:

```csv
stop_id,station_id,station_name
```

Stops not listed in `station_groups.csv` will keep their original GTFS stop ID.

## Preparing the data

From this directory, run:

```bash
python prepare_data.py
```

The raw national snapshot is intentionally excluded from Git because it is
about 1.1 GB and contains files larger than GitHub permits. Mentors who want to
regenerate the prepared CSVs should place the GTFS files in
`sweden-20260801/`. Students do not need the raw snapshot.

The script:

1. Keeps SL routes (`agency_id` 275) in central Stockholm.
2. Includes metro, commuter and local trains, trams, ferries, and a curated set
   of central bus lines.
3. Reads the large `stop_times.txt` file in chunks.
4. Uses each trip's headsign as its destination.
5. Applies the explicit grouping rules in `data/station_groups.csv`.
6. Removes duplicates and validates the result before writing the app data.

The geographic bounds and selected bus lines are constants near the top of
`prepare_data.py`, making the camp scope easy for mentors to adjust. The script
does not filter by operating date because the explorer describes the static
feed rather than departures on a particular day.

With the supplied snapshot and current settings, the generated dataset contains
283 map stations and 2,038 unique station/type/line/destination combinations.

## Using the prepared data

`transport_data.py` contains the functions students will use from the app:

```python
from transport_data import (
    get_services_for_station,
    get_station,
    get_station_summary,
    group_services_by_type,
    load_services,
    load_stations,
)

stations = load_stations()
services = load_services()

station = get_station(stations, "stockholm-central")
selected = get_services_for_station(services, "stockholm-central")
summary = get_station_summary(selected)
groups = group_services_by_type(selected)
```

The loading functions remove duplicate rows, ignore unusable station rows, and
replace missing labels with readable values such as `Unknown destination`.

## Running the application

Start the local application from this directory:

```bash
python -m streamlit run app.py
```

Then open `http://localhost:8501` if the browser does not open automatically.
Click a pink station marker to display its transport types, line numbers, and
destinations. The application reads only the two prepared CSV files; it does not
load the national GTFS files at runtime.

## Project commands

Use Python 3.10 or newer. On the camp Ubuntu environment, create the virtual
environment explicitly with `python3.10` so it does not use the older system
Python 3.8:

```bash
python3.10 --version
python3.10 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python prepare_data.py
pytest
python -m streamlit run app.py
```

## Scope

The application will use static data from the 1 August 2026 GTFS snapshot. It
will not provide live departures, disruption information, or journey planning.
