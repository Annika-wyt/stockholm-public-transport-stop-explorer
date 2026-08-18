# Stockholm Public Transport Stop Explorer

A beginner-friendly Python and Streamlit project for exploring public transport
stops in Stockholm. A user will select a stop on a map and see the transport
types, line numbers, and destinations serving it.

## Camp branches

This repository contains differentiated starting points for an AI-assisted
programming camp:

- `option-1-greenfield`: a simplified travel-planner brief and prepared data,
  with no solution code.
- `option-2-barebones`: a launching starter app, function TODOs, and checkpoint
  tests.
- `option-3-mvp`: the completed Stop Explorer plus an extension guide.
- `main`: the complete mentor reference, including preprocessing and all tests.

Students can change tracks if they need more or less structure.

## Getting and updating a branch

Fetch the latest branch information first:

```bash
git fetch --all
```

Choose one branch, switch to it, and pull its latest changes.

For the mentor reference:

```bash
git switch main
git pull --ff-only
```

For Option 1:

```bash
git switch option-1-greenfield
git pull --ff-only
```

For Option 2:

```bash
git switch option-2-barebones
git pull --ff-only
```

For Option 3:

```bash
git switch option-3-mvp
git pull --ff-only
```

After `git fetch --all`, Git will normally create a local copy when you switch
to a remote branch for the first time. If it does not, use
`git switch --track origin/<branch-name>`. Replace `origin` if your remote has a
different name; `git remote -v` shows the available names.

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
│   ├── line_patterns.csv      # Ordered stops for unique trip patterns
│   └── station_groups.csv     # Manual grouping rules for related stops
├── tests/
│   ├── fixtures/
│   ├── test_prepare_data.py
│   └── test_transport_data.py
└── sweden-20260801/           # Original GTFS snapshot
```

## Data files

The application uses three small generated files instead of reading the full
GTFS feed at runtime.

`data/stations.csv`:

```csv
station_id,station_name,latitude,longitude
```

`data/stop_services.csv`:

```csv
station_id,transport_type,line,destination
```

`data/line_patterns.csv` preserves GTFS stop order for each unique direction and
trip pattern:

```csv
pattern_id,route_id,transport_type,line,direction,station_id,station_name,latitude,longitude,stop_sequence
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
6. Groups trips with identical ordered station sequences into stable patterns.
7. Removes duplicates and validates the result before writing the app data.

The geographic bounds and selected bus lines are constants near the top of
`prepare_data.py`, making the camp scope easy for mentors to adjust. The script
does not filter by operating date because the explorer describes the static
feed rather than departures on a particular day.

With the supplied snapshot and current settings, the generated dataset contains
283 map stations, 2,038 unique station/type/line/destination combinations, and
567 ordered line patterns containing 9,001 stops.

The 283-station geographic limit applies only to the main Explore map. Ordered
line patterns retain complete routes for the selected lines, including outer
endpoints such as Mörby centrum, Fruängen, and commuter-rail terminals.

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
destinations. The application reads only the four prepared CSV files; it does not
load the national GTFS files at runtime.

The completed interface includes:

- Search for a station by name.
- Filter map markers by transport type.
- Select a transport-type/line pair and display every matching station.
- Select a direction/trip pattern and connect its stations in GTFS stop order.
- Check whether two stations share possible direct services.

The direct-connection result is based on shared static line data. It does not
verify live schedules, direction, disruptions, or travel time and should not be
presented as real-time journey advice.

Line Explorer paths are straight segments between station centres. They use
GTFS `stop_sequence` for order but do not represent exact road, track, or ferry
geometry because the supplied snapshot has no `shapes.txt` file.

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
