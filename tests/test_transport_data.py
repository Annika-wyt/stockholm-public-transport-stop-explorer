"""Tests for the beginner-facing transport data functions."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from transport_data import (
    TransportDataError,
    filter_stations_by_transport,
    get_services_for_station,
    get_patterns_for_line,
    get_shared_lines,
    get_station,
    get_station_summary,
    get_stations_for_line,
    get_stations_for_pattern,
    group_services_by_type,
    load_line_patterns,
    load_services,
    load_stations,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_stations_cleans_invalid_and_duplicate_rows() -> None:
    stations = load_stations(FIXTURES_DIR / "stations.csv")

    assert list(stations["station_id"]) == ["station-1", "station-2", "station-4"]
    assert stations.loc[stations["station_id"].eq("station-4"), "station_name"].item() == (
        "Unknown station"
    )
    assert stations["latitude"].dtype.kind == "f"


def test_load_services_cleans_missing_values_and_duplicates() -> None:
    services = load_services(FIXTURES_DIR / "stop_services.csv")

    assert len(services) == 5
    assert not services.duplicated().any()
    assert "Unknown destination" in set(services["destination"])
    assert "Unknown line" in set(services["line"])
    assert "Other" in set(services["transport_type"])


def test_station_lookup_and_service_filtering() -> None:
    stations = load_stations(FIXTURES_DIR / "stations.csv")
    services = load_services(FIXTURES_DIR / "stop_services.csv")

    station = get_station(stations, "station-1")
    assert station is not None
    assert station["station_name"] == "Central"
    assert get_station(stations, "missing") is None

    selected_services = get_services_for_station(services, "station-1")
    assert len(selected_services) == 3
    assert set(selected_services["transport_type"]) == {"Bus", "Metro"}
    assert get_services_for_station(services, "missing").empty


def test_grouping_and_summary_use_beginner_friendly_results() -> None:
    services = load_services(FIXTURES_DIR / "stop_services.csv")
    selected_services = get_services_for_station(services, "station-1")

    grouped = group_services_by_type(selected_services)
    summary = get_station_summary(selected_services)

    assert list(grouped) == ["Metro", "Bus"]
    assert summary == {
        "transport_type_count": 2,
        "line_count": 2,
        "destination_count": 2,
    }


def test_missing_columns_raise_a_clear_error(tmp_path: Path) -> None:
    broken_file = tmp_path / "broken.csv"
    pd.DataFrame([{"station_id": "station-1"}]).to_csv(broken_file, index=False)

    with pytest.raises(TransportDataError, match="missing required columns"):
        load_stations(broken_file)


def test_real_generated_data_is_queryable() -> None:
    stations = load_stations()
    services = load_services()
    line_patterns = load_line_patterns()

    assert len(stations) == 283
    assert len(services) == 2_038
    assert len(line_patterns) == 3_476
    assert line_patterns["pattern_id"].nunique() == 282
    assert get_station(stations, "stockholm-central") is not None
    assert not get_services_for_station(services, "stockholm-central").empty


def test_ordered_line_patterns_load_and_join_to_station_coordinates() -> None:
    stations = load_stations(FIXTURES_DIR / "stations.csv")
    patterns = load_line_patterns(FIXTURES_DIR / "line_patterns.csv")

    metro_patterns = get_patterns_for_line(patterns, "Metro", "10")
    ordered_stations = get_stations_for_pattern(
        stations, patterns, "metro-pattern"
    )

    assert len(metro_patterns) == 2
    assert list(ordered_stations["station_id"]) == ["station-1", "station-2"]
    assert list(ordered_stations["stop_sequence"]) == [1, 2]


def test_transport_filter_keeps_stations_with_selected_types() -> None:
    stations = pd.DataFrame(
        [
            {"station_id": "a", "station_name": "A"},
            {"station_id": "b", "station_name": "B"},
            {"station_id": "c", "station_name": "C"},
        ]
    )
    services = pd.DataFrame(
        [
            {"station_id": "a", "transport_type": "Metro", "line": "10"},
            {"station_id": "b", "transport_type": "Bus", "line": "1"},
            {"station_id": "c", "transport_type": "Tram", "line": "7"},
        ]
    )

    filtered = filter_stations_by_transport(stations, services, ["Metro", "Tram"])

    assert list(filtered["station_id"]) == ["a", "c"]
    assert filter_stations_by_transport(stations, services, []).empty


def test_line_lookup_returns_unique_matching_stations() -> None:
    stations = pd.DataFrame(
        [
            {"station_id": "a", "station_name": "A"},
            {"station_id": "b", "station_name": "B"},
            {"station_id": "c", "station_name": "C"},
        ]
    )
    services = pd.DataFrame(
        [
            {"station_id": "a", "transport_type": "Metro", "line": "10"},
            {"station_id": "a", "transport_type": "Metro", "line": "10"},
            {"station_id": "b", "transport_type": "Metro", "line": "10"},
            {"station_id": "c", "transport_type": "Bus", "line": "10"},
        ]
    )

    matching = get_stations_for_line(stations, services, "Metro", "10")

    assert list(matching["station_id"]) == ["a", "b"]


def test_shared_lines_match_both_transport_type_and_line() -> None:
    services = pd.DataFrame(
        [
            {"station_id": "a", "transport_type": "Metro", "line": "10"},
            {"station_id": "a", "transport_type": "Bus", "line": "1"},
            {"station_id": "b", "transport_type": "Metro", "line": "10"},
            {"station_id": "b", "transport_type": "Tram", "line": "1"},
            {"station_id": "c", "transport_type": "Bus", "line": "55"},
        ]
    )

    shared = get_shared_lines(services, "a", "b")

    assert shared.to_dict("records") == [
        {"transport_type": "Metro", "line": "10"}
    ]
    assert get_shared_lines(services, "a", "c").empty
