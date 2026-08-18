# Option 1: Greenfield Stockholm Travel Challenge

Design and build your own Python application that helps someone investigate a
public-transport journey in Stockholm. You receive the idea, prepared static
data, and suggested goals—but no application code.

This is the most independent option. Decide how your application should work,
break the problem into small tasks, and use AI as a programming partner.

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

## Setup

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

You will create the application files yourself. A common launch command is:

```bash
python -m streamlit run app.py
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
