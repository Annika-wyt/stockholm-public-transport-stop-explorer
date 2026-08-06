"""Tests for the beginner-facing transport data functions."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from transport_data import (
    TransportDataError,
    get_services_for_station,
    get_station,
    get_station_summary,
    group_services_by_type,
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

    assert len(stations) == 283
    assert len(services) == 2_038
    assert get_station(stations, "stockholm-central") is not None
    assert not get_services_for_station(services, "stockholm-central").empty

