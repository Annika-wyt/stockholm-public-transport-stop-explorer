# Option 2: Barebones Stockholm Stop Explorer

This starter project is for students who want structure while still building
the important parts themselves. It includes prepared public-transport data, a
Streamlit page that launches, and small data-loading functions.

Your goal is to turn it into an interactive Public Transport Stop Explorer.

## Getting and updating a branch

Choose only the branch you want to work on. The first time you use it, run the
matching commands below.

For the mentor reference:

```bash
git fetch origin main
git switch main
git pull --ff-only
```

For Option 1:

```bash
git fetch origin option-1-greenfield
git switch --track origin/option-1-greenfield
git pull --ff-only
```

For Option 2:

```bash
git fetch origin option-2-barebones
git switch --track origin/option-2-barebones
git pull --ff-only
```

For Option 3:

```bash
git fetch origin option-3-mvp
git switch --track origin/option-3-mvp
git pull --ff-only
```

Each `git fetch` command above downloads only the named branch. Once the branch
exists locally, update it later with:

```bash
git switch <branch-name>
git pull --ff-only
```

Replace `<branch-name>` with the branch you chose. If your remote is not named
`origin`, replace `origin` with the remote name shown by `git remote -v`.

## What is already provided

- 283 prepared Stockholm stations in `data/stations.csv`
- 2,038 prepared services in `data/stop_services.csv`
- A Streamlit page with a basic, non-selectable map
- Working CSV-loading functions
- Function stubs and checkpoint tests

The large national GTFS source files are not needed.

## Setup

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pytest
python -m streamlit run app.py
```

## Student checkpoints

Complete one checkpoint at a time.

1. Open both CSV files and identify their shared `station_id` column.
2. Implement `get_station()` in `transport_data.py`.
3. Implement `get_services_for_station()`.
4. Implement `group_services_by_type()`.
5. Implement `get_station_summary()`.
6. Replace the basic map with a selectable PyDeck map.
7. Read the selected marker's `station_id`.
8. Display the selected station's lines and destinations.
9. Handle no selection and missing data without crashing.
10. Remove checkpoint test skips as each function is completed.

## Suggested goals to work toward

- The application launches locally.
- At least 20 stations appear on a map.
- A user can select one station.
- The selected station name appears.
- Transport types, lines, and destinations appear.
- Duplicate service combinations are not displayed.
- Missing data does not crash the application.

## Useful prepared-data functions

The intended flow is:

```text
load data
    ↓
select map marker
    ↓
read station_id
    ↓
filter services
    ↓
group and display results
```

## AI prompt template

```text
I am a beginner Python student completing a Streamlit starter project.

My current checkpoint:
[one checkpoint from the list]

Relevant files:
[list files]

Please explain the task, make the smallest change needed for this checkpoint,
and tell me which test skip I can remove to verify it.
```

Run the application and tests after every checkpoint. Do not move on until you
can explain what the new code does.
