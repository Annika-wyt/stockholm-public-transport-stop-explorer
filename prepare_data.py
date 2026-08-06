"""Create small, beginner-friendly CSV files from the supplied GTFS feed.

This is mentor-owned code. Students should use the generated files in ``data``
instead of loading the multi-million-row GTFS feed in the Streamlit app.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_RAW_DATA_DIR = PROJECT_DIR / "sweden-20260801"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "data"
DEFAULT_STATION_GROUPS = DEFAULT_OUTPUT_DIR / "station_groups.csv"

SL_AGENCY_ID = "275"
STOCKHOLM_BOUNDS = {
    "min_latitude": 59.30,
    "max_latitude": 59.36,
    "min_longitude": 18.00,
    "max_longitude": 18.12,
}

# A small central-city selection keeps the map readable for the camp project.
# Mentors can add or remove line numbers after reviewing the generated map.
CENTRAL_BUS_LINES = frozenset(
    {
        "1",
        "2",
        "3",
        "4",
        "50",
        "53",
        "54",
        "55",
        "57",
        "61",
        "65",
        "66",
        "67",
        "69",
        "72",
        "74",
        "75",
        "76",
    }
)

SUPPORTED_ROUTE_TYPES = frozenset({"106", "401", "700", "900", "1000"})
REQUIRED_GROUP_COLUMNS = {"stop_id", "station_id", "station_name"}


class DataPreparationError(ValueError):
    """Raised when source or generated data does not meet project assumptions."""


def _require_columns(table: pd.DataFrame, columns: Iterable[str], source: str) -> None:
    missing = sorted(set(columns) - set(table.columns))
    if missing:
        raise DataPreparationError(
            f"{source} is missing required columns: {', '.join(missing)}"
        )


def _clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def classify_transport(
    route_type: object, route_long_name: object = "", route_short_name: object = ""
) -> str:
    """Convert the route codes used by this feed into readable labels."""

    code = _clean_text(route_type)
    long_name = _clean_text(route_long_name).casefold()
    short_name = _clean_text(route_short_name)

    if code == "401":
        return "Metro"
    if code == "700":
        return "Bus"
    if code == "900":
        return "Tram"
    if code == "1000":
        return "Ferry"
    if code == "106":
        if "pendeltåg" in long_name:
            return "Commuter train / Pendeltåg"
        if "roslagsbanan" in long_name or short_name.startswith(("27", "28", "29")):
            return "Local train / Roslagsbanan"
        if short_name in {"25", "26"}:
            return "Local train / Saltsjöbanan"
        return "Local train"

    raise DataPreparationError(f"Unsupported route type: {code or '<missing>'}")


def load_all_stops(raw_data_dir: Path) -> pd.DataFrame:
    """Load every stop with valid coordinates from the supplied feed."""

    path = raw_data_dir / "stops.txt"
    stops = pd.read_csv(
        path,
        dtype=str,
        usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"],
    )
    _require_columns(
        stops, {"stop_id", "stop_name", "stop_lat", "stop_lon"}, path.name
    )

    stops["latitude"] = pd.to_numeric(stops["stop_lat"], errors="coerce")
    stops["longitude"] = pd.to_numeric(stops["stop_lon"], errors="coerce")
    invalid_coordinates = stops[["latitude", "longitude"]].isna().any(axis=1)
    if invalid_coordinates.any():
        raise DataPreparationError(
            f"{path.name} contains {int(invalid_coordinates.sum())} invalid coordinates"
        )

    return stops[["stop_id", "stop_name", "latitude", "longitude"]].copy()


def filter_stops_by_bounds(
    stops: pd.DataFrame, bounds: dict[str, float]
) -> pd.DataFrame:
    """Keep stops inside the configured central Explore map area."""

    inside_area = (
        stops["latitude"].between(
            bounds["min_latitude"], bounds["max_latitude"], inclusive="both"
        )
        & stops["longitude"].between(
            bounds["min_longitude"], bounds["max_longitude"], inclusive="both"
        )
    )
    return stops.loc[
        inside_area, ["stop_id", "stop_name", "latitude", "longitude"]
    ].copy()


def load_stops(raw_data_dir: Path, bounds: dict[str, float]) -> pd.DataFrame:
    """Load stops with valid coordinates inside the configured map area."""

    return filter_stops_by_bounds(load_all_stops(raw_data_dir), bounds)


def load_routes(
    raw_data_dir: Path, bus_lines: frozenset[str] = CENTRAL_BUS_LINES
) -> pd.DataFrame:
    """Load SL rail, metro, tram, ferry, and selected central bus routes."""

    path = raw_data_dir / "routes.txt"
    routes = pd.read_csv(
        path,
        dtype=str,
        usecols=[
            "route_id",
            "agency_id",
            "route_short_name",
            "route_long_name",
            "route_type",
        ],
    )
    _require_columns(
        routes,
        {
            "route_id",
            "agency_id",
            "route_short_name",
            "route_long_name",
            "route_type",
        },
        path.name,
    )

    is_sl = routes["agency_id"].eq(SL_AGENCY_ID)
    is_supported = routes["route_type"].isin(SUPPORTED_ROUTE_TYPES)
    is_selected_bus = routes["route_short_name"].isin(bus_lines)
    is_non_bus = routes["route_type"].ne("700")

    routes = routes.loc[is_sl & is_supported & (is_non_bus | is_selected_bus)].copy()
    routes["transport_type"] = routes.apply(
        lambda route: classify_transport(
            route["route_type"],
            route["route_long_name"],
            route["route_short_name"],
        ),
        axis=1,
    )
    return routes[
        [
            "route_id",
            "route_short_name",
            "route_long_name",
            "route_type",
            "transport_type",
        ]
    ]


def load_trips(raw_data_dir: Path, route_ids: set[str]) -> pd.DataFrame:
    """Load only trips belonging to the selected routes."""

    path = raw_data_dir / "trips.txt"
    trips = pd.read_csv(
        path,
        dtype=str,
        usecols=["trip_id", "route_id", "trip_headsign"],
    )
    _require_columns(trips, {"trip_id", "route_id", "trip_headsign"}, path.name)
    return trips.loc[trips["route_id"].isin(route_ids)].copy()


def load_relevant_stop_times(
    raw_data_dir: Path,
    trip_ids: set[str],
    chunk_size: int,
    stop_ids: set[str] | None = None,
) -> pd.DataFrame:
    """Stream stop times for selected trips, optionally limited to stop IDs."""

    path = raw_data_dir / "stop_times.txt"
    matches: list[pd.DataFrame] = []

    chunks = pd.read_csv(
        path,
        dtype=str,
        usecols=["trip_id", "stop_id", "stop_sequence"],
        chunksize=chunk_size,
    )
    for chunk in chunks:
        relevant = chunk["trip_id"].isin(trip_ids)
        if stop_ids is not None:
            relevant &= chunk["stop_id"].isin(stop_ids)
        if relevant.any():
            matches.append(
                chunk.loc[relevant, ["trip_id", "stop_id", "stop_sequence"]]
            )

    if not matches:
        return pd.DataFrame(columns=["trip_id", "stop_id", "stop_sequence"])

    stop_times = pd.concat(matches, ignore_index=True)
    stop_times["stop_sequence"] = pd.to_numeric(
        stop_times["stop_sequence"], errors="coerce"
    )
    if stop_times["stop_sequence"].isna().any():
        raise DataPreparationError("stop_times.txt contains invalid stop_sequence values")
    return stop_times


def build_stop_services(
    stop_times: pd.DataFrame, trips: pd.DataFrame, routes: pd.DataFrame
) -> pd.DataFrame:
    """Join filtered GTFS tables into one deduplicated service table per stop."""

    services = stop_times.merge(trips, on="trip_id", how="inner", validate="many_to_one")
    services = services.merge(
        routes, on="route_id", how="inner", validate="many_to_one"
    )

    short_names = services["route_short_name"].fillna("").str.strip()
    long_names = services["route_long_name"].fillna("").str.strip()
    services["line"] = short_names.where(short_names.ne(""), long_names)
    services["line"] = services["line"].where(
        services["line"].ne(""), "Unknown line"
    )

    destinations = services["trip_headsign"].fillna("").str.strip()
    services["destination"] = destinations.where(
        destinations.ne(""), "Unknown destination"
    )

    result = services[["stop_id", "transport_type", "line", "destination"]]
    return result.drop_duplicates(ignore_index=True)


def load_station_groups(path: Path) -> pd.DataFrame:
    """Load and validate the manually maintained station-group mapping."""

    if not path.exists():
        raise DataPreparationError(f"Station-group file not found: {path}")

    groups = pd.read_csv(path, dtype=str)
    _require_columns(groups, REQUIRED_GROUP_COLUMNS, path.name)
    groups = groups[list(sorted(REQUIRED_GROUP_COLUMNS))].copy()
    groups = groups.dropna(how="all")

    for column in REQUIRED_GROUP_COLUMNS:
        groups[column] = groups[column].fillna("").str.strip()
    incomplete = groups[list(REQUIRED_GROUP_COLUMNS)].eq("").any(axis=1)
    if incomplete.any():
        raise DataPreparationError(
            f"{path.name} contains {int(incomplete.sum())} incomplete grouping rows"
        )
    if groups["stop_id"].duplicated().any():
        raise DataPreparationError(f"{path.name} contains duplicate stop_id values")

    names_per_station = groups.groupby("station_id")["station_name"].nunique()
    if names_per_station.gt(1).any():
        raise DataPreparationError(
            f"{path.name} assigns more than one name to the same station_id"
        )
    return groups


def group_stations(
    stops: pd.DataFrame, stop_services: pd.DataFrame, groups: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply manual groups and create the two application-facing tables."""

    served_stop_ids = set(stop_services["stop_id"])
    assignments = stops.loc[stops["stop_id"].isin(served_stop_ids)].copy()
    assignments = assignments.merge(groups, on="stop_id", how="left")
    assignments["station_id"] = assignments["station_id"].fillna(
        assignments["stop_id"]
    )
    assignments["station_name"] = assignments["station_name"].fillna(
        assignments["stop_name"]
    )

    stations = (
        assignments.groupby(["station_id", "station_name"], as_index=False)
        .agg(latitude=("latitude", "mean"), longitude=("longitude", "mean"))
    )
    stations = stations.assign(
        _sort_name=stations["station_name"].str.casefold()
    ).sort_values(["_sort_name", "station_id"], kind="stable")
    stations = stations.drop(columns="_sort_name").reset_index(drop=True)

    station_lookup = assignments[["stop_id", "station_id"]]
    services = stop_services.merge(
        station_lookup, on="stop_id", how="inner", validate="many_to_one"
    )
    services = services[
        ["station_id", "transport_type", "line", "destination"]
    ].drop_duplicates()
    services = services.sort_values(
        ["station_id", "transport_type", "line", "destination"], kind="stable"
    ).reset_index(drop=True)
    return stations, services


def build_line_patterns(
    stops: pd.DataFrame,
    stop_times: pd.DataFrame,
    trips: pd.DataFrame,
    routes: pd.DataFrame,
    groups: pd.DataFrame,
) -> pd.DataFrame:
    """Create unique ordered station patterns from GTFS trip stop sequences."""

    assignments = stops.merge(groups, on="stop_id", how="left")
    assignments["station_id"] = assignments["station_id"].fillna(
        assignments["stop_id"]
    )
    assignments["station_name"] = assignments["station_name"].fillna(
        assignments["stop_name"]
    )
    station_metadata = (
        assignments.groupby(["station_id", "station_name"], as_index=False)
        .agg(latitude=("latitude", "mean"), longitude=("longitude", "mean"))
    )

    ordered_stops = stop_times.merge(
        trips, on="trip_id", how="inner", validate="many_to_one"
    )
    ordered_stops = ordered_stops.merge(
        routes, on="route_id", how="inner", validate="many_to_one"
    )
    ordered_stops = ordered_stops.merge(
        assignments[["stop_id", "station_id"]],
        on="stop_id",
        how="inner",
        validate="many_to_one",
    )
    ordered_stops = ordered_stops.sort_values(
        ["trip_id", "stop_sequence"], kind="stable"
    )

    pattern_rows: list[dict[str, object]] = []
    seen_patterns: set[tuple[str, str, tuple[str, ...]]] = set()

    for _, trip_stops in ordered_stops.groupby("trip_id", sort=False):
        station_sequence: list[str] = []
        for station_id in trip_stops["station_id"]:
            if not station_sequence or station_sequence[-1] != station_id:
                station_sequence.append(station_id)

        if len(station_sequence) < 2:
            continue

        first_row = trip_stops.iloc[0]
        route_id = _clean_text(first_row["route_id"])
        direction = _clean_text(first_row["trip_headsign"]) or "Unknown destination"
        signature = (route_id, direction, tuple(station_sequence))
        if signature in seen_patterns:
            continue
        seen_patterns.add(signature)

        signature_text = "\x1f".join(
            [route_id, direction, *station_sequence]
        ).encode("utf-8")
        pattern_id = f"pattern-{hashlib.sha1(signature_text).hexdigest()[:12]}"
        line = _clean_text(first_row["route_short_name"])
        if not line:
            line = _clean_text(first_row["route_long_name"]) or "Unknown line"

        for sequence, station_id in enumerate(station_sequence, start=1):
            pattern_rows.append(
                {
                    "pattern_id": pattern_id,
                    "route_id": route_id,
                    "transport_type": first_row["transport_type"],
                    "line": line,
                    "direction": direction,
                    "station_id": station_id,
                    "stop_sequence": sequence,
                }
            )

    columns = [
        "pattern_id",
        "route_id",
        "transport_type",
        "line",
        "direction",
        "station_id",
        "stop_sequence",
    ]
    patterns = pd.DataFrame(pattern_rows, columns=columns)
    if patterns.empty:
        return patterns.assign(
            station_name=pd.Series(dtype=str),
            latitude=pd.Series(dtype=float),
            longitude=pd.Series(dtype=float),
        )
    patterns = patterns.merge(
        station_metadata,
        on="station_id",
        how="inner",
        validate="many_to_one",
    )
    output_columns = [
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
    return patterns[output_columns].sort_values(
        ["transport_type", "line", "direction", "pattern_id", "stop_sequence"],
        kind="stable",
    ).reset_index(drop=True)


def validate_outputs(
    stations: pd.DataFrame,
    services: pd.DataFrame,
    line_patterns: pd.DataFrame,
    min_stations: int = 20,
    max_stations: int = 300,
) -> None:
    """Check the generated tables before replacing application data."""

    _require_columns(
        stations,
        {"station_id", "station_name", "latitude", "longitude"},
        "stations output",
    )
    _require_columns(
        services,
        {"station_id", "transport_type", "line", "destination"},
        "stop-services output",
    )
    _require_columns(
        line_patterns,
        {
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
        },
        "line-patterns output",
    )

    if not min_stations <= len(stations) <= max_stations:
        raise DataPreparationError(
            f"Expected {min_stations}-{max_stations} stations, generated {len(stations)}"
        )
    if stations["station_id"].duplicated().any():
        raise DataPreparationError("Generated station_id values are not unique")
    if stations[["station_id", "station_name"]].isna().any().any():
        raise DataPreparationError("Generated stations contain missing identifiers or names")
    if stations[["latitude", "longitude"]].isna().any().any():
        raise DataPreparationError("Generated stations contain missing coordinates")
    if services.empty:
        raise DataPreparationError("No services were generated")
    if services.isna().any().any():
        raise DataPreparationError("Generated services contain missing values")
    if services.duplicated().any():
        raise DataPreparationError("Generated services contain duplicate rows")
    if line_patterns.empty:
        raise DataPreparationError("No ordered line patterns were generated")
    if line_patterns.isna().any().any():
        raise DataPreparationError("Generated line patterns contain missing values")
    if line_patterns.duplicated(subset=["pattern_id", "stop_sequence"]).any():
        raise DataPreparationError(
            "Generated line patterns contain duplicate pattern sequences"
        )

    unknown_station_ids = set(services["station_id"]) - set(stations["station_id"])
    if unknown_station_ids:
        raise DataPreparationError(
            "Generated services refer to station IDs missing from stations.csv"
        )

    invalid_pattern_coordinates = (
        ~line_patterns["latitude"].between(-90, 90, inclusive="both")
        | ~line_patterns["longitude"].between(-180, 180, inclusive="both")
    )
    if invalid_pattern_coordinates.any():
        raise DataPreparationError(
            "Generated line patterns contain invalid station coordinates"
        )

    for pattern_id, pattern in line_patterns.groupby("pattern_id"):
        expected_sequence = list(range(1, len(pattern) + 1))
        actual_sequence = sorted(pattern["stop_sequence"].astype(int))
        if len(pattern) < 2 or actual_sequence != expected_sequence:
            raise DataPreparationError(
                f"Pattern {pattern_id} does not contain a valid consecutive stop order"
            )


def write_outputs(
    stations: pd.DataFrame,
    services: pd.DataFrame,
    line_patterns: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Write each validated application table with an atomic file replacement."""

    output_dir.mkdir(parents=True, exist_ok=True)
    for table, filename in (
        (stations, "stations.csv"),
        (services, "stop_services.csv"),
        (line_patterns, "line_patterns.csv"),
    ):
        destination = output_dir / filename
        temporary_path = destination.with_suffix(f"{destination.suffix}.tmp")
        try:
            table.to_csv(temporary_path, index=False)
            temporary_path.replace(destination)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


def prepare_data(
    raw_data_dir: Path = DEFAULT_RAW_DATA_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    station_groups_path: Path = DEFAULT_STATION_GROUPS,
    *,
    bounds: dict[str, float] = STOCKHOLM_BOUNDS,
    bus_lines: frozenset[str] = CENTRAL_BUS_LINES,
    chunk_size: int = 500_000,
    min_stations: int = 20,
    max_stations: int = 300,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run the complete preparation pipeline and return the generated tables."""

    raw_data_dir = Path(raw_data_dir)
    output_dir = Path(output_dir)
    station_groups_path = Path(station_groups_path)

    all_stops = load_all_stops(raw_data_dir)
    stops = filter_stops_by_bounds(all_stops, bounds)
    routes = load_routes(raw_data_dir, bus_lines)
    trips = load_trips(raw_data_dir, set(routes["route_id"]))
    all_stop_times = load_relevant_stop_times(
        raw_data_dir,
        set(trips["trip_id"]),
        chunk_size,
    )
    stop_times = all_stop_times.loc[
        all_stop_times["stop_id"].isin(set(stops["stop_id"]))
    ].copy()
    stop_services = build_stop_services(stop_times, trips, routes)
    groups = load_station_groups(station_groups_path)
    stations, services = group_stations(stops, stop_services, groups)
    line_patterns = build_line_patterns(
        all_stops, all_stop_times, trips, routes, groups
    )
    validate_outputs(
        stations, services, line_patterns, min_stations, max_stations
    )
    write_outputs(stations, services, line_patterns, output_dir)
    return stations, services, line_patterns


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare small CSV files for the transport stop explorer."
    )
    parser.add_argument("--raw-data-dir", type=Path, default=DEFAULT_RAW_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--station-groups", type=Path, default=DEFAULT_STATION_GROUPS
    )
    parser.add_argument("--chunk-size", type=int, default=500_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stations, services, line_patterns = prepare_data(
        raw_data_dir=args.raw_data_dir,
        output_dir=args.output_dir,
        station_groups_path=args.station_groups,
        chunk_size=args.chunk_size,
    )

    print(f"Created {len(stations)} stations and {len(services)} services.")
    print(
        f"Created {line_patterns['pattern_id'].nunique()} ordered line patterns "
        f"with {len(line_patterns)} stops."
    )
    print("Transport types:")
    for transport_type, count in services.groupby("transport_type").size().items():
        print(f"  {transport_type}: {count}")
    print(f"Wrote {args.output_dir / 'stations.csv'}")
    print(f"Wrote {args.output_dir / 'stop_services.csv'}")
    print(f"Wrote {args.output_dir / 'line_patterns.csv'}")


if __name__ == "__main__":
    main()
