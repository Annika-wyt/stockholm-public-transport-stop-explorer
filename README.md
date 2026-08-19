# Option 2: Barebones Stockholm Stop Explorer

This starter project is for students who want structure while still building
the important parts themselves. It includes prepared public-transport data, a
Streamlit page that launches, and small data-loading functions.

Your goal is to turn it into an interactive Public Transport Stop Explorer.

## Getting and updating a branch

If you have not downloaded the project yet, clone only the barebones branch:

```bash
git clone --branch option-2-barebones --single-branch https://github.com/Annika-wyt/stockholm-public-transport-stop-explorer.git
cd stockholm-public-transport-stop-explorer
```

If you already cloned the repository, download the latest information for this
branch and switch to it:

```bash
git fetch origin option-2-barebones
git switch option-2-barebones
git pull origin option-2-barebones
```

If Git says the branch does not exist locally, create it from the GitHub branch:

```bash
git switch --track origin/option-2-barebones
```

Confirm that you are on the correct branch:

```bash
git branch --show-current
```

The command should print `option-2-barebones`.

## What is already provided

- 283 prepared Stockholm stations in `data/stations.csv`
- 2,038 prepared services in `data/stop_services.csv`
- A Streamlit page with a basic, non-selectable map
- Working CSV-loading functions
- Function stubs and checkpoint tests

The large national GTFS source files are not needed.

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
local URL shown in the terminal. Press **Ctrl+C** in the terminal to stop the
app. Run `deactivate` when you want to leave the virtual environment.

To run the tests while the virtual environment is active:

```bash
python -m pytest tests
```

The application reads only the prepared CSV files in the `data` folder. You do
not need to download or prepare the original national transport data to run it.

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
