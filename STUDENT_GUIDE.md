# Option 3: Extend the Working MVP

This branch contains a complete, tested Public Transport Stop Explorer. Your
task is to understand the existing application and add at least one meaningful
feature.

## Start here

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pytest
python -m streamlit run app.py
```

The application should start with all tests passing. Make one small change at a
time and rerun the tests after each change.

## Feature ideas

- Search for a station by name.
- Filter map markers by transport type.
- Give transport types different marker colours.
- Compare two stations.
- Save favourite stations during the current session.
- Add a Swedish/English language switch.
- Add a possible direct-connection checker between two stations.
- Improve accessibility or the layout on smaller screens.

## Definition of done

1. Describe the user problem your feature solves.
2. Write observable acceptance criteria.
3. Implement the feature without breaking existing behavior.
4. Add or update at least one automated test.
5. Demonstrate the feature and explain the important code.

## AI prompt template

```text
I am a beginner Python student extending an existing Streamlit application.

My current goal:
[one small goal]

Relevant files:
[list files]

Acceptance criteria:
[list observable behavior]

Please explain the existing code involved, implement only this change, and give
me one command that verifies it.
```

Do not accept code you cannot explain. If AI changes many unrelated files, ask
it to reduce the solution to the smallest necessary change.

