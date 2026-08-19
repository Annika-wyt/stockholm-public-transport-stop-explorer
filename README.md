# Option 1: Greenfield Stockholm Travel Challenge

Design and build your own Python application that helps someone investigate a
public-transport journey in Stockholm. You receive the idea, prepared static
data, and suggested goals—but no application code.

This is the most independent option. Decide how your application should work,
break the problem into small tasks, and use AI as a programming partner.

## Getting and updating a branch

If you have not downloaded the project yet, clone only the greenfield branch:

```bash
git clone --branch option-1-greenfield --single-branch https://github.com/Annika-wyt/stockholm-public-transport-stop-explorer.git
cd stockholm-public-transport-stop-explorer
```

If you already cloned the repository, download the latest information for this
branch and switch to it:

```bash
git fetch origin option-1-greenfield
git switch option-1-greenfield
git pull origin option-1-greenfield
```

If Git says the branch does not exist locally, create it from the GitHub branch:

```bash
git switch --track origin/option-1-greenfield
```

Confirm that you are on the correct branch:

```bash
git branch --show-current
```

The command should print `option-1-greenfield`.

## The idea

A user selects an origin station and a destination station. The application
looks for transport lines that serve both stations and displays possible direct
connections.

For example:

```text
From: Stockholm Central / T-Centralen
To: Slussen

Possible direct services:
Metro 13
Metro 14
Bus 53
```

If no shared service is found, give the user a clear message instead of
crashing.

## Important scope

This is a simplified, static travel-planner idea. The prepared data can show
that the same line serves two stations, but it does not contain live departures,
travel times, disruptions, or complete ordered route patterns. Describe results
as **possible direct services**, not guaranteed real-time journeys.

A timetable-aware journey planner is outside the minimum project scope.

## Prepared data

`data/stations.csv` contains 283 stations:

```csv
station_id,station_name,latitude,longitude
```

`data/stop_services.csv` contains 2,038 unique service combinations:

```csv
station_id,transport_type,line,destination
```

The files share the `station_id` column. Read IDs as strings so leading zeros or
other formatting cannot be lost.

The original 1.1 GB national GTFS feed is deliberately not included.

## Suggested goals to work toward

- The application launches locally.
- The user can select two different stations.
- Both station names are displayed.
- Possible shared transport-type/line combinations are displayed.
- Duplicate connections are removed.
- A helpful message appears when no direct connection is found.
- Empty or invalid selections do not crash the application.
- At least one important function has an automated test.

## Suggested development milestones

1. Create `app.py` and display a Streamlit title.
2. Load and inspect both CSV files with pandas.
3. Add origin and destination selection boxes.
4. Find services for the origin.
5. Find services for the destination.
6. Match rows using both `transport_type` and `line`.
7. Display possible direct services.
8. Handle identical stations and no-match results.
9. Add a test and improve the interface.

You may organize the code differently if you can explain your design.

## Optional directions

- Add a station map.
- Show all lines at the origin and destination.
- Compare the two stations.
- Filter by transport type.
- Find possible one-transfer connections as an experimental feature.
- Let the user save favourite journeys during the current session.

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

Install the packages:

```bash
python -m pip install -r requirements.txt
```

### macOS

In the VS Code terminal, create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If your computer uses `python`, use `python -m venv .venv` instead.

Install the packages:

```bash
python -m pip install -r requirements.txt
```

### Windows

VS Code normally opens PowerShell on Windows. Create and activate the virtual
environment with:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If your computer uses `python3`, use `python3 -m venv .venv` instead.

Install the packages:

```powershell
python -m pip install -r requirements.txt
```

If you use Command Prompt instead of PowerShell, activate the environment with:

```bat
.venv\Scripts\activate.bat
```

### Run the App

This option does not include an application file because you will create it
yourself. After you create `app.py`, start it with:

```bash
python -m streamlit run app.py
```

The app will open in your browser. If it does not open automatically, open the
local URL shown in the terminal. Press **Ctrl+C** in the terminal to stop the
app.

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

Run `deactivate` when you want to leave the virtual environment.

After you add tests, run them while the virtual environment is active with:

```bash
python -m pytest tests
```

## AI working agreement

- Ask AI to solve one milestone at a time.
- Run the application after each change.
- Paste complete error messages when asking for debugging help.
- Ask AI to explain unfamiliar code in beginner language.
- Keep a short record of your most useful prompts.
- Do not submit code you cannot explain.

Prompt template:

```text
I am a beginner Python student building a simplified public-transport planner.

Current milestone:
[one milestone]

Available CSV columns:
[relevant columns]

Goal for this milestone:
[observable result]

Please suggest the smallest implementation for this milestone, explain it in
beginner language, and give me a command or test that verifies it.
```

## Final demonstration

Show a journey with a possible direct service, a pair without a direct service,
and one error case. Be ready to explain how your application matches lines
between the two stations.
