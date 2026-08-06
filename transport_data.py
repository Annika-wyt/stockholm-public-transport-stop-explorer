"""Student data functions for the Stockholm Stop Explorer."""

from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "data"
STATIONS_FILE = DATA_DIR / "stations.csv"
SERVICES_FILE = DATA_DIR / "stop_services.csv"


def load_stations(file_path=STATIONS_FILE):
    """Load the prepared stations and convert coordinates into numbers."""

    stations = pd.read_csv(file_path, dtype={"station_id": str})
    stations["latitude"] = pd.to_numeric(stations["latitude"], errors="coerce")
    stations["longitude"] = pd.to_numeric(stations["longitude"], errors="coerce")
    return stations.dropna(subset=["station_id", "latitude", "longitude"])


def load_services(file_path=SERVICES_FILE):
    """Load the prepared services and remove exact duplicate rows."""

    services = pd.read_csv(file_path, dtype=str).fillna("")
    return services.drop_duplicates().reset_index(drop=True)


def get_station(stations, station_id):
    """Return one station as a dictionary, or None if it is not found."""

    # TODO checkpoint 2: filter stations using station_id.
    raise NotImplementedError


def get_services_for_station(services, station_id):
    """Return only the services belonging to one station."""

    # TODO checkpoint 3: filter services using station_id.
    raise NotImplementedError


def group_services_by_type(services):
    """Return a dictionary that groups rows by transport_type."""

    # TODO checkpoint 4: create one DataFrame per transport type.
    raise NotImplementedError


def get_station_summary(services):
    """Count transport types, lines, and destinations."""

    # TODO checkpoint 5: return three useful counts in a dictionary.
    raise NotImplementedError

