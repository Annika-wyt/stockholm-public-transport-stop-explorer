"""Checkpoint tests for Option 2 students."""

from pathlib import Path

import pytest

from transport_data import (
    get_services_for_station,
    get_station,
    get_station_summary,
    group_services_by_type,
    load_services,
    load_stations,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_starter_files_load() -> None:
    stations = load_stations(FIXTURES_DIR / "stations.csv")
    services = load_services(FIXTURES_DIR / "stop_services.csv")

    assert not stations.empty
    assert not services.empty
    assert "station_id" in stations.columns
    assert "station_id" in services.columns


@pytest.mark.skip(reason="Checkpoint 2: remove this skip after implementing get_station")
def test_get_station() -> None:
    stations = load_stations(FIXTURES_DIR / "stations.csv")

    station = get_station(stations, "station-1")

    assert station["station_name"] == "Central"
    assert get_station(stations, "missing") is None


@pytest.mark.skip(
    reason="Checkpoint 3: remove this skip after implementing service filtering"
)
def test_get_services_for_station() -> None:
    services = load_services(FIXTURES_DIR / "stop_services.csv")

    selected = get_services_for_station(services, "station-1")

    assert len(selected) == 3
    assert set(selected["station_id"]) == {"station-1"}


@pytest.mark.skip(reason="Checkpoint 4: remove this skip after implementing grouping")
def test_group_services_by_type() -> None:
    services = load_services(FIXTURES_DIR / "stop_services.csv")
    selected = services.loc[services["station_id"].eq("station-1")]

    grouped = group_services_by_type(selected)

    assert set(grouped) == {"Bus", "Metro"}


@pytest.mark.skip(reason="Checkpoint 5: remove this skip after implementing summary")
def test_get_station_summary() -> None:
    services = load_services(FIXTURES_DIR / "stop_services.csv")
    selected = services.loc[services["station_id"].eq("station-1")]

    summary = get_station_summary(selected)

    assert summary == {
        "transport_type_count": 2,
        "line_count": 2,
        "destination_count": 2,
    }

