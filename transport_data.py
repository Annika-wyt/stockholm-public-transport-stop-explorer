"""Load and query the small CSV files used by the Streamlit application.

These functions are intentionally independent from Streamlit. That keeps the
data logic easy for beginners to read and lets it be tested without starting a
web application.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
STATIONS_FILE = DATA_DIR / "stations.csv"
SERVICES_FILE = DATA_DIR / "stop_services.csv"
LINE_PATTERNS_FILE = DATA_DIR / "line_patterns.csv"

STATION_COLUMNS = ["station_id", "station_name", "latitude", "longitude"]
SERVICE_COLUMNS = ["station_id", "transport_type", "line", "destination"]
LINE_PATTERN_COLUMNS = [
    "pattern_id",
    "route_id",
    "transport_type",
    "line",
    "direction",
    "station_id",
    "station_name",
    "latitude",
    "longitude",
    "stop_sequence",
]

TRANSPORT_TYPE_ORDER = [
    "Metro",
    "Commuter train / Pendeltåg",
    "Local train / Roslagsbanan",
    "Local train / Saltsjöbanan",
    "Local train",
    "Tram",
    "Bus",
    "Ferry",
    "Other",
]


class TransportDataError(ValueError):
    """Raised when an application data file cannot be used safely."""


def _read_csv(file_path: str | Path, required_columns: list[str]) -> pd.DataFrame:
    """Read a CSV as text and give missing-file/column errors clear messages."""

    path = Path(file_path)
    try:
        table = pd.read_csv(path, dtype=str, keep_default_na=False)
    except FileNotFoundError as error:
        raise TransportDataError(f"Data file not found: {path}") from error
    except pd.errors.EmptyDataError as error:
        raise TransportDataError(f"Data file is empty: {path}") from error

    missing_columns = [
        column for column in required_columns if column not in table.columns
    ]
    if missing_columns:
        raise TransportDataError(
            f"{path.name} is missing required columns: {', '.join(missing_columns)}"
        )
    return table[required_columns].copy()


def load_stations(file_path: str | Path = STATIONS_FILE) -> pd.DataFrame:
    """Load valid, unique map stations from ``stations.csv``."""

    stations = _read_csv(file_path, STATION_COLUMNS)
    stations["station_id"] = stations["station_id"].str.strip()
    stations["station_name"] = stations["station_name"].str.strip()
    stations["latitude"] = pd.to_numeric(stations["latitude"], errors="coerce")
    stations["longitude"] = pd.to_numeric(stations["longitude"], errors="coerce")

    valid_rows = (
        stations["station_id"].ne("")
        & stations["latitude"].between(-90, 90, inclusive="both")
        & stations["longitude"].between(-180, 180, inclusive="both")
    )
    stations = stations.loc[valid_rows].copy()
    stations["station_name"] = stations["station_name"].where(
        stations["station_name"].ne(""), "Unknown station"
    )

    return (
        stations.drop_duplicates(subset="station_id", keep="first")
        .reset_index(drop=True)
    )


def load_services(file_path: str | Path = SERVICES_FILE) -> pd.DataFrame:
    """Load, clean, and deduplicate station services."""

    services = _read_csv(file_path, SERVICE_COLUMNS)
    for column in SERVICE_COLUMNS:
        services[column] = services[column].str.strip()

    services = services.loc[services["station_id"].ne("")].copy()
    services["transport_type"] = services["transport_type"].where(
        services["transport_type"].ne(""), "Other"
    )
    services["line"] = services["line"].where(
        services["line"].ne(""), "Unknown line"
    )
    services["destination"] = services["destination"].where(
        services["destination"].ne(""), "Unknown destination"
    )

    return services.drop_duplicates(ignore_index=True)


def load_line_patterns(file_path: str | Path = LINE_PATTERNS_FILE) -> pd.DataFrame:
    """Load ordered station patterns generated from GTFS stop sequences."""

    patterns = _read_csv(file_path, LINE_PATTERN_COLUMNS)
    numeric_columns = {"latitude", "longitude", "stop_sequence"}
    text_columns = [
        column for column in LINE_PATTERN_COLUMNS if column not in numeric_columns
    ]
    for column in text_columns:
        patterns[column] = patterns[column].str.strip()

    patterns["stop_sequence"] = pd.to_numeric(
        patterns["stop_sequence"], errors="coerce"
    )
    patterns["latitude"] = pd.to_numeric(patterns["latitude"], errors="coerce")
    patterns["longitude"] = pd.to_numeric(patterns["longitude"], errors="coerce")
    valid_rows = (
        patterns[text_columns].ne("").all(axis=1)
        & patterns["stop_sequence"].notna()
        & patterns["stop_sequence"].ge(1)
        & patterns["latitude"].between(-90, 90, inclusive="both")
        & patterns["longitude"].between(-180, 180, inclusive="both")
    )
    patterns = patterns.loc[valid_rows].copy()
    patterns["stop_sequence"] = patterns["stop_sequence"].astype(int)
    return (
        patterns.drop_duplicates(subset=["pattern_id", "stop_sequence"])
        .sort_values(["pattern_id", "stop_sequence"], kind="stable")
        .reset_index(drop=True)
    )


def get_station(
    stations: pd.DataFrame, station_id: str
) -> dict[str, object] | None:
    """Return one station as a dictionary, or ``None`` when it is unknown."""

    wanted_id = str(station_id).strip()
    match = stations.loc[stations["station_id"].eq(wanted_id)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def get_services_for_station(
    services: pd.DataFrame, station_id: str
) -> pd.DataFrame:
    """Return all unique services belonging to one station."""

    wanted_id = str(station_id).strip()
    return services.loc[services["station_id"].eq(wanted_id)].reset_index(drop=True)


def group_services_by_type(
    services: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Group services in a consistent, user-friendly transport-type order."""

    available_types = set(services["transport_type"])
    known_types = [
        transport_type
        for transport_type in TRANSPORT_TYPE_ORDER
        if transport_type in available_types
    ]
    other_types = sorted(available_types - set(TRANSPORT_TYPE_ORDER))

    return {
        transport_type: services.loc[
            services["transport_type"].eq(transport_type)
        ].reset_index(drop=True)
        for transport_type in known_types + other_types
    }


def get_station_summary(services: pd.DataFrame) -> dict[str, int]:
    """Count transport types, type/line pairs, and known destinations."""

    known_destinations = services.loc[
        services["destination"].ne("Unknown destination"), "destination"
    ]
    return {
        "transport_type_count": int(services["transport_type"].nunique()),
        "line_count": int(
            services[["transport_type", "line"]].drop_duplicates().shape[0]
        ),
        "destination_count": int(known_destinations.nunique()),
    }


def filter_stations_by_transport(
    stations: pd.DataFrame,
    services: pd.DataFrame,
    transport_types: list[str],
) -> pd.DataFrame:
    """Keep stations served by at least one selected transport type."""

    if not transport_types:
        return stations.iloc[0:0].copy()

    matching_station_ids = services.loc[
        services["transport_type"].isin(transport_types), "station_id"
    ].unique()
    return stations.loc[stations["station_id"].isin(matching_station_ids)].reset_index(
        drop=True
    )


def get_stations_for_line(
    stations: pd.DataFrame,
    services: pd.DataFrame,
    transport_type: str,
    line: str,
) -> pd.DataFrame:
    """Return the unique stations served by one transport-type/line pair."""

    matching_station_ids = services.loc[
        services["transport_type"].eq(str(transport_type).strip())
        & services["line"].eq(str(line).strip()),
        "station_id",
    ].unique()
    return stations.loc[stations["station_id"].isin(matching_station_ids)].reset_index(
        drop=True
    )


def get_shared_lines(
    services: pd.DataFrame,
    first_station_id: str,
    second_station_id: str,
) -> pd.DataFrame:
    """Find transport-type/line pairs serving both selected stations."""

    columns = ["transport_type", "line"]
    first_lines = get_services_for_station(services, first_station_id)[columns]
    second_lines = get_services_for_station(services, second_station_id)[columns]

    shared_lines = first_lines.drop_duplicates().merge(
        second_lines.drop_duplicates(), on=columns, how="inner"
    )
    if shared_lines.empty:
        return shared_lines

    type_order = {
        transport_type: index
        for index, transport_type in enumerate(TRANSPORT_TYPE_ORDER)
    }
    shared_lines["_type_order"] = shared_lines["transport_type"].map(
        type_order
    ).fillna(len(type_order))
    return (
        shared_lines.sort_values(
            ["_type_order", "transport_type", "line"], kind="stable"
        )
        .drop(columns="_type_order")
        .reset_index(drop=True)
    )


def get_patterns_for_line(
    line_patterns: pd.DataFrame,
    transport_type: str,
    line: str,
) -> pd.DataFrame:
    """Return ordered-pattern rows for one transport-type/line pair."""

    return line_patterns.loc[
        line_patterns["transport_type"].eq(str(transport_type).strip())
        & line_patterns["line"].eq(str(line).strip())
    ].reset_index(drop=True)


def get_stations_for_pattern(
    line_patterns: pd.DataFrame,
    pattern_id: str,
) -> pd.DataFrame:
    """Return full-route station coordinates in one pattern's stop order."""

    return line_patterns.loc[
        line_patterns["pattern_id"].eq(str(pattern_id).strip())
    ].sort_values("stop_sequence", kind="stable").reset_index(drop=True)
