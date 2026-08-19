# Stockholm Public Transport Stop Explorer

A beginner-friendly Python and Streamlit project for exploring public transport
stops in Stockholm. A user will select a stop on a map and see the transport
types, line numbers, and destinations serving it.

## Getting and updating a branch

If you have not downloaded the project yet, clone only the MVP branch:

```bash
git clone --branch option-3-mvp --single-branch https://github.com/Annika-wyt/stockholm-public-transport-stop-explorer.git
cd stockholm-public-transport-stop-explorer
```

If you already cloned the repository, download the latest information for this
branch and switch to it:

```bash
git fetch origin option-3-mvp
git switch option-3-mvp
git pull origin option-3-mvp
```

If Git says the branch does not exist locally, create it from the GitHub branch:

```bash
git switch --track origin/option-3-mvp
```

Confirm that you are on the correct branch:

```bash
git branch --show-current
```

The command should print `option-3-mvp`.

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

## How To Run The App

Open the project folder in VS Code, then open the integrated terminal by
selecting **Terminal > New Terminal**. Make sure the terminal is inside the
`stockholm-public-transport-stop-explorer` folder before running the commands
below.

### What Is a Python Virtual Environment?

A virtual environment is a private place for this project's Python packages.
It keeps packages such as Streamlit separate from packages used by your other
Python projects. The `.venv` folder created below is that private place.

You create the virtual environment once. Each time you open a new VS Code
terminal to work on the project, activate it again before running the app.

### Should I Use `python` or `python3`?

The correct command depends on how Python was installed and configured on your
computer. Check which command works in your VS Code terminal:

```bash
python --version
```

If that command is not found, try:

```bash
python3 --version
```

Use the command that displays a Python version when creating the virtual
environment. After the environment is activated, `python` will normally point
to the Python inside `.venv`.

### Linux

In the VS Code terminal, create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If your computer uses `python`, use `python -m venv .venv` instead.

Install the packages and start the app:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### macOS

In the VS Code terminal, create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If your computer uses `python`, use `python -m venv .venv` instead.

Install the packages and start the app:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### Windows

VS Code normally opens PowerShell on Windows. Create and activate the virtual
environment with:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If your computer uses `python3`, use `python3 -m venv .venv` instead.

Install the packages and start the app:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If you use Command Prompt instead of PowerShell, activate the environment with:

```bat
.venv\Scripts\activate.bat
```

### Run the App Again Later

After the first setup, open a new VS Code terminal and activate the existing
virtual environment. On Linux or macOS, run:

```bash
source .venv/bin/activate
```

On Windows PowerShell, run:

```powershell
.venv\Scripts\Activate.ps1
```

Then start the app:

```bash
python -m streamlit run app.py
```

The app will open in your browser. If it does not open automatically, open the
local URL shown in the terminal. Click a pink station marker to display its
transport types, line numbers, and destinations. Press **Ctrl+C** in the
terminal to stop the app. Run `deactivate` when you want to leave the virtual
environment.

To run the tests while the virtual environment is active:

```bash
python -m pytest tests
```

The application reads only the prepared CSV files in the `data` folder. You do
not need to download or prepare the original national transport data to run it.

## Scope

The application will use static data from the 1 August 2026 GTFS snapshot. It
will not provide live departures, disruption information, or journey planning.
