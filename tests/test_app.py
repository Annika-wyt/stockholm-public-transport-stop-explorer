"""Tests for the Streamlit application helpers and startup."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from app import (
    MAP_LAYER_ID,
    build_line_pattern_map,
    build_station_map,
    get_selected_station_id,
)
from transport_data import get_patterns_for_line, load_line_patterns


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


def test_ordered_line_map_contains_a_path_and_stop_markers() -> None:
    ordered_stations = pd.DataFrame(
        [
            {
                "station_id": "station-1",
                "station_name": "Central",
                "latitude": 59.33,
                "longitude": 18.05,
                "stop_sequence": 1,
            },
            {
                "station_id": "station-2",
                "station_name": "Square",
                "latitude": 59.34,
                "longitude": 18.06,
                "stop_sequence": 2,
            },
        ]
    )

    chart = build_line_pattern_map(ordered_stations)

    assert [layer.id for layer in chart.layers] == ["line-path", "line-stops"]
    assert chart.layers[1].pickable is True


def test_streamlit_app_starts_without_exceptions() -> None:
    app = AppTest.from_file(PROJECT_DIR / "app.py").run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "Stockholm Public Transport Stop Explorer"
    assert "select one of the pink map markers" in app.info[0].value
    assert [tab.label for tab in app.tabs] == [
        "🗺️ Explore",
        "⚖️ Compare",
        "🧭 Line explorer",
        "🔗 Direct connection",
    ]
    assert app.multiselect[0].label == "Filter markers by transport type"
    assert app.selectbox[0].label == "Search for a station"


def test_search_and_direct_connection_work_in_the_running_app() -> None:
    app = AppTest.from_file(PROJECT_DIR / "app.py").run(timeout=10)

    app.selectbox[0].set_value("stockholm-central").run(timeout=10)
    assert not app.exception
    assert "Stockholm Central / T-Centralen" in [
        subheader.value for subheader in app.subheader
    ]

    app.selectbox[4].set_value("stockholm-central")
    app.selectbox[5].set_value("slussen")
    app.run(timeout=10)
    assert not app.exception
    assert any("possible direct service" in message.value for message in app.success)


def test_comparison_and_line_explorer_work_in_the_running_app() -> None:
    app = AppTest.from_file(PROJECT_DIR / "app.py").run(timeout=10)

    app.selectbox[1].set_value("stockholm-central")
    app.selectbox[2].set_value("slussen")
    app.selectbox[3].set_value(("Metro", "10"))
    app.run(timeout=10)

    patterns = get_patterns_for_line(load_line_patterns(), "Metro", "10")
    pattern_id = patterns.iloc[0]["pattern_id"]
    pattern_selector = next(
        selectbox
        for selectbox in app.selectbox
        if selectbox.label == "Select a direction / pattern"
    )
    pattern_selector.set_value(pattern_id).run(timeout=10)

    assert not app.exception
    subheaders = [subheader.value for subheader in app.subheader]
    assert "Stockholm Central / T-Centralen" in subheaders
    assert "Slussen" in subheaders
    assert any(metric.label == "Stations found" for metric in app.metric)
