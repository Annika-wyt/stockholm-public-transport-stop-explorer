"""Tests for the Streamlit application helpers and startup."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from app import MAP_LAYER_ID, build_station_map, get_selected_station_id


PROJECT_DIR = Path(__file__).resolve().parents[1]


def test_selected_station_id_is_read_from_the_map_layer() -> None:
    event = {
        "selection": {
            "objects": {
                MAP_LAYER_ID: [
                    {"station_id": "stockholm-central", "station_name": "Central"}
                ]
            }
        }
    }

    assert get_selected_station_id(event) == "stockholm-central"
    assert get_selected_station_id({"selection": {"objects": {}}}) is None
    assert get_selected_station_id(None) is None


def test_station_map_has_a_pickable_stable_layer() -> None:
    stations = pd.DataFrame(
        [
            {
                "station_id": "station-1",
                "station_name": "Central",
                "latitude": 59.33,
                "longitude": 18.05,
            }
        ]
    )

    chart = build_station_map(stations)

    assert len(chart.layers) == 1
    assert chart.layers[0].id == MAP_LAYER_ID
    assert chart.layers[0].pickable is True


def test_streamlit_app_starts_without_exceptions() -> None:
    app = AppTest.from_file(PROJECT_DIR / "app.py").run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "Stockholm Public Transport Stop Explorer"
    assert "Select one of the pink map markers" in app.info[0].value

