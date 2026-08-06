"""Streamlit interface for the Stockholm Public Transport Stop Explorer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
import pydeck as pdk
import streamlit as st

from transport_data import (
    TRANSPORT_TYPE_ORDER,
    TransportDataError,
    filter_stations_by_transport,
    get_patterns_for_line,
    get_services_for_station,
    get_shared_lines,
    get_station,
    get_station_summary,
    get_stations_for_pattern,
    group_services_by_type,
    load_line_patterns,
    load_services,
    load_stations,
)


MAP_LAYER_ID = "station-points"
STOCKHOLM_VIEW = {
    "latitude": 59.33,
    "longitude": 18.06,
    "zoom": 11.3,
    "pitch": 0,
}

TRANSPORT_ICONS = {
    "Metro": "🚇",
    "Commuter train / Pendeltåg": "🚆",
    "Local train / Roslagsbanan": "🚆",
    "Local train / Saltsjöbanan": "🚆",
    "Local train": "🚆",
    "Tram": "🚊",
    "Bus": "🚌",
    "Ferry": "⛴️",
    "Other": "🚏",
}


@st.cache_data
def load_app_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the small prepared application files once per Streamlit session."""

    return load_stations(), load_services(), load_line_patterns()


def order_transport_types(transport_types: set[str]) -> list[str]:
    """Put known transport types first and unexpected labels alphabetically."""

    known_types = [name for name in TRANSPORT_TYPE_ORDER if name in transport_types]
    return known_types + sorted(transport_types - set(TRANSPORT_TYPE_ORDER))


def build_station_map(
    stations: pd.DataFrame,
    selected_station_id: str | None = None,
) -> pdk.Deck:
    """Build a station map and optionally highlight one selected station."""

    map_data = stations.copy()
    is_selected = map_data["station_id"].eq(selected_station_id)
    map_data["marker_color"] = [
        [37, 99, 235, 240] if selected else [236, 72, 153, 210]
        for selected in is_selected
    ]
    map_data["marker_radius"] = [140 if selected else 90 for selected in is_selected]

    view = STOCKHOLM_VIEW.copy()
    selected_rows = map_data.loc[is_selected]
    if not selected_rows.empty:
        selected_row = selected_rows.iloc[0]
        view.update(
            {
                "latitude": float(selected_row["latitude"]),
                "longitude": float(selected_row["longitude"]),
                "zoom": 13.0,
            }
        )

    station_layer = pdk.Layer(
        "ScatterplotLayer",
        id=MAP_LAYER_ID,
        data=map_data,
        get_position="[longitude, latitude]",
        get_fill_color="marker_color",
        get_line_color=[131, 24, 67, 255],
        get_radius="marker_radius",
        radius_min_pixels=5,
        radius_max_pixels=12,
        line_width_min_pixels=1,
        stroked=True,
        filled=True,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 213, 235, 255],
    )

    return pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(**view),
        layers=[station_layer],
        tooltip={"text": "{station_name}\nClick to explore"},
    )


def build_line_pattern_map(ordered_stations: pd.DataFrame) -> pdk.Deck:
    """Draw an ordered stop pattern as a path with station markers."""

    path = ordered_stations[["longitude", "latitude"]].values.tolist()
    path_layer = pdk.Layer(
        "PathLayer",
        id="line-path",
        data=[{"path": path}],
        get_path="path",
        get_color=[37, 99, 235, 220],
        get_width=6,
        width_min_pixels=4,
        rounded=True,
        pickable=False,
    )
    station_layer = pdk.Layer(
        "ScatterplotLayer",
        id="line-stops",
        data=ordered_stations,
        get_position="[longitude, latitude]",
        get_fill_color=[236, 72, 153, 230],
        get_line_color=[131, 24, 67, 255],
        get_radius=100,
        radius_min_pixels=6,
        radius_max_pixels=12,
        line_width_min_pixels=1,
        stroked=True,
        filled=True,
        pickable=True,
    )
    view = pdk.ViewState(
        latitude=float(ordered_stations["latitude"].mean()),
        longitude=float(ordered_stations["longitude"].mean()),
        zoom=11.5,
        pitch=0,
    )
    return pdk.Deck(
        map_style=None,
        initial_view_state=view,
        layers=[path_layer, station_layer],
        tooltip={"text": "{stop_sequence}. {station_name}"},
    )


def _get_value(container: Any, key: str, default: Any) -> Any:
    """Read a value from either a dictionary or Streamlit's attribute objects."""

    if isinstance(container, Mapping):
        return container.get(key, default)
    return getattr(container, key, default)


def get_selected_station_id(event: Any) -> str | None:
    """Extract the selected station ID from a PyDeck selection event."""

    selection = _get_value(event, "selection", {})
    objects = _get_value(selection, "objects", {})
    selected_objects = _get_value(objects, MAP_LAYER_ID, [])
    if not selected_objects:
        return None

    station_id = _get_value(selected_objects[0], "station_id", "")
    station_id = str(station_id).strip()
    return station_id or None


def station_selectbox(
    label: str,
    stations: pd.DataFrame,
    key: str,
    *,
    on_change: Any = None,
) -> str | None:
    """Display a searchable station select box and return its station ID."""

    station_names = dict(zip(stations["station_id"], stations["station_name"]))
    options = [""] + list(stations["station_id"])
    selected_id = st.selectbox(
        label,
        options,
        format_func=lambda station_id: (
            "Choose a station" if station_id == "" else station_names[station_id]
        ),
        key=key,
        on_change=on_change,
    )
    return selected_id or None


def render_station_details(
    station: dict[str, object], station_services: pd.DataFrame
) -> None:
    """Display one selected station and its grouped service information."""

    st.subheader(str(station["station_name"]))

    if station_services.empty:
        st.warning("No services were found for this station.")
        return

    summary = get_station_summary(station_services)
    metric_columns = st.columns(3)
    metric_columns[0].metric("Transport types", summary["transport_type_count"])
    metric_columns[1].metric("Lines", summary["line_count"])
    metric_columns[2].metric("Destinations", summary["destination_count"])

    grouped_services = group_services_by_type(station_services)
    transport_labels = [
        f"{TRANSPORT_ICONS.get(name, '🚏')} {name}" for name in grouped_services
    ]
    st.caption(" · ".join(transport_labels))

    st.markdown("#### Services")
    for transport_type, type_services in grouped_services.items():
        icon = TRANSPORT_ICONS.get(transport_type, "🚏")
        line_count = type_services["line"].nunique()
        line_word = "line" if line_count == 1 else "lines"

        with st.expander(
            f"{icon} {transport_type} — {line_count} {line_word}",
            expanded=True,
        ):
            display_table = type_services[["line", "destination"]].rename(
                columns={"line": "Line", "destination": "Direction / destination"}
            )
            table_height = min(38 + 35 * len(display_table), 350)
            st.dataframe(
                display_table,
                hide_index=True,
                width="stretch",
                height=table_height,
            )


def render_comparison_card(
    station: dict[str, object], station_services: pd.DataFrame
) -> None:
    """Display compact information for one side of a station comparison."""

    st.subheader(str(station["station_name"]))
    summary = get_station_summary(station_services)
    metric_columns = st.columns(3)
    metric_columns[0].metric("Types", summary["transport_type_count"])
    metric_columns[1].metric("Lines", summary["line_count"])
    metric_columns[2].metric("Destinations", summary["destination_count"])

    grouped_services = group_services_by_type(station_services)
    transport_labels = [
        f"{TRANSPORT_ICONS.get(name, '🚏')} {name}" for name in grouped_services
    ]
    st.caption(" · ".join(transport_labels))

    station_lines = station_services[["transport_type", "line"]].drop_duplicates()
    st.dataframe(
        station_lines.rename(
            columns={"transport_type": "Transport type", "line": "Line"}
        ),
        hide_index=True,
        width="stretch",
        height=min(38 + 35 * len(station_lines), 300),
    )


def render_shared_lines(shared_lines: pd.DataFrame) -> None:
    """Display possible services shared by two stations."""

    if shared_lines.empty:
        st.warning("No possible direct line was found between these stations.")
        return

    st.success(f"Found {len(shared_lines)} possible direct service(s).")
    result = shared_lines.copy()
    result.insert(
        0,
        "Icon",
        result["transport_type"].map(lambda name: TRANSPORT_ICONS.get(name, "🚏")),
    )
    st.dataframe(
        result.rename(
            columns={"transport_type": "Transport type", "line": "Line"}
        ),
        hide_index=True,
        width="stretch",
    )


def render_explore_tab(stations: pd.DataFrame, services: pd.DataFrame) -> None:
    """Render station search, transport filters, map, and station details."""

    available_types = order_transport_types(set(services["transport_type"]))
    filter_column, search_column = st.columns([3, 2])

    with filter_column:
        selected_types = st.multiselect(
            "Filter markers by transport type",
            available_types,
            default=available_types,
            format_func=lambda name: f"{TRANSPORT_ICONS.get(name, '🚏')} {name}",
            key="explore-transport-filter",
        )

    visible_stations = filter_stations_by_transport(
        stations, services, selected_types
    )

    def update_search_selection() -> None:
        st.session_state["explore-selected-station"] = (
            st.session_state.get("explore-station-search") or None
        )

    with search_column:
        searched_station_id = station_selectbox(
            "Search for a station",
            visible_stations,
            "explore-station-search",
            on_change=update_search_selection,
        )

    if "explore-selected-station" not in st.session_state:
        st.session_state["explore-selected-station"] = searched_station_id

    selected_station_id = st.session_state.get("explore-selected-station")
    if selected_station_id not in set(visible_stations["station_id"]):
        selected_station_id = None
        st.session_state["explore-selected-station"] = None

    map_column, details_column = st.columns([3, 2], gap="large")
    with map_column:
        if visible_stations.empty:
            st.warning("Choose at least one transport type to display map markers.")
            map_event = None
        else:
            map_event = st.pydeck_chart(
                build_station_map(visible_stations, selected_station_id),
                on_select="rerun",
                selection_mode="single-object",
                key="station-map",
                height=620,
            )
        st.caption(
            f"Showing {len(visible_stations)} of {len(stations)} stations from the "
            "static 1 August 2026 feed."
        )

    map_station_id = get_selected_station_id(map_event)
    if map_station_id is not None:
        selected_station_id = map_station_id
        st.session_state["explore-selected-station"] = map_station_id

    with details_column:
        st.markdown("### Selected station")
        if selected_station_id is None:
            st.info("Search for a station or select one of the pink map markers.")
        else:
            station = get_station(stations, selected_station_id)
            if station is None:
                st.warning("The selected station could not be found.")
            else:
                station_services = get_services_for_station(
                    services, selected_station_id
                )
                render_station_details(station, station_services)


def render_compare_tab(stations: pd.DataFrame, services: pd.DataFrame) -> None:
    """Render side-by-side summaries for two selected stations."""

    st.write("Choose two stations to compare their transport options.")
    first_selector, second_selector = st.columns(2)
    with first_selector:
        first_id = station_selectbox("First station", stations, "compare-first")
    with second_selector:
        second_id = station_selectbox("Second station", stations, "compare-second")

    if first_id is None or second_id is None:
        st.info("Choose two stations to start the comparison.")
        return
    if first_id == second_id:
        st.warning("Choose two different stations to compare.")
        return

    first_station = get_station(stations, first_id)
    second_station = get_station(stations, second_id)
    if first_station is None or second_station is None:
        st.warning("One of the selected stations could not be found.")
        return

    first_services = get_services_for_station(services, first_id)
    second_services = get_services_for_station(services, second_id)
    first_column, second_column = st.columns(2, gap="large")
    with first_column:
        render_comparison_card(first_station, first_services)
    with second_column:
        render_comparison_card(second_station, second_services)

    st.markdown("#### Lines serving both stations")
    render_shared_lines(get_shared_lines(services, first_id, second_id))


def render_line_tab(
    stations: pd.DataFrame, line_patterns: pd.DataFrame
) -> None:
    """Render all stations associated with a selected line."""

    st.write("Choose a transport type and line to see its stations in this dataset.")
    line_options = line_patterns[["transport_type", "line"]].drop_duplicates()
    line_options["_type_order"] = line_options["transport_type"].map(
        {name: index for index, name in enumerate(TRANSPORT_TYPE_ORDER)}
    ).fillna(len(TRANSPORT_TYPE_ORDER))
    line_options = line_options.sort_values(
        ["_type_order", "transport_type", "line"], kind="stable"
    )
    option_tuples = list(
        line_options[["transport_type", "line"]].itertuples(index=False, name=None)
    )
    selected_line = st.selectbox(
        "Select a line",
        [None] + option_tuples,
        format_func=lambda option: (
            "Choose a line"
            if option is None
            else f"{TRANSPORT_ICONS.get(option[0], '🚏')} {option[0]} — {option[1]}"
        ),
        key="line-explorer-selection",
    )

    if selected_line is None:
        st.info("Choose a line to display its stations.")
        return

    transport_type, line = selected_line
    matching_patterns = get_patterns_for_line(
        line_patterns, transport_type, line
    )
    pattern_summaries = (
        matching_patterns.groupby(["pattern_id", "direction"], as_index=False)
        .agg(station_count=("station_id", "size"))
        .sort_values(["direction", "station_count", "pattern_id"], kind="stable")
    )
    pattern_labels = {
        row.pattern_id: (
            f"{row.direction} — {row.station_count} stations "
            f"({row.pattern_id[-4:]})"
        )
        for row in pattern_summaries.itertuples(index=False)
    }
    selected_pattern_id = st.selectbox(
        "Select a direction / pattern",
        [""] + list(pattern_summaries["pattern_id"]),
        format_func=lambda pattern_id: (
            "Choose a direction / pattern"
            if pattern_id == ""
            else pattern_labels[pattern_id]
        ),
        key=f"line-pattern-{transport_type}-{line}",
    )
    if not selected_pattern_id:
        st.info("Choose a direction or trip pattern to display its ordered stops.")
        return

    ordered_stations = get_stations_for_pattern(
        stations, line_patterns, selected_pattern_id
    )
    st.metric("Stations found", len(ordered_stations))
    st.caption(
        "The blue path connects station centres in GTFS stop_sequence order. It "
        "does not represent the exact road, rail, or ferry geometry."
    )

    map_column, list_column = st.columns([3, 2], gap="large")
    with map_column:
        st.pydeck_chart(
            build_line_pattern_map(ordered_stations),
            key="line-pattern-map",
            height=520,
        )
    with list_column:
        st.dataframe(
            ordered_stations[["stop_sequence", "station_name"]].rename(
                columns={"stop_sequence": "Order", "station_name": "Station"}
            ),
            hide_index=True,
            width="stretch",
            height=520,
        )


def render_direct_connection_tab(
    stations: pd.DataFrame, services: pd.DataFrame
) -> None:
    """Check whether two stations have any transport-type/line pair in common."""

    st.write(
        "Check whether the static dataset contains a transport line serving both "
        "stations."
    )
    first_selector, second_selector = st.columns(2)
    with first_selector:
        first_id = station_selectbox("From", stations, "direct-from")
    with second_selector:
        second_id = station_selectbox("To", stations, "direct-to")

    if first_id is None or second_id is None:
        st.info("Choose an origin and destination.")
        return
    if first_id == second_id:
        st.warning("Origin and destination must be different stations.")
        return

    first_station = get_station(stations, first_id)
    second_station = get_station(stations, second_id)
    if first_station is None or second_station is None:
        st.warning("One of the selected stations could not be found.")
        return

    st.markdown(
        f"#### {first_station['station_name']} → {second_station['station_name']}"
    )
    render_shared_lines(get_shared_lines(services, first_id, second_id))
    st.caption(
        "These are possible shared services from static data, not live journey "
        "advice. Direction, timetable, disruptions, and travel time are not checked."
    )


def main() -> None:
    st.set_page_config(
        page_title="Stockholm Stop Explorer",
        page_icon="🚏",
        layout="wide",
    )

    st.title("Stockholm Public Transport Stop Explorer")
    st.write(
        "Explore stations, compare transport options, inspect lines, and check "
        "possible direct connections."
    )

    try:
        stations, services, line_patterns = load_app_data()
    except TransportDataError as error:
        st.error(str(error))
        st.stop()

    explore_tab, compare_tab, line_tab, direct_tab = st.tabs(
        ["🗺️ Explore", "⚖️ Compare", "🧭 Line explorer", "🔗 Direct connection"]
    )
    with explore_tab:
        render_explore_tab(stations, services)
    with compare_tab:
        render_compare_tab(stations, services)
    with line_tab:
        render_line_tab(stations, line_patterns)
    with direct_tab:
        render_direct_connection_tab(stations, services)


if __name__ == "__main__":
    main()
    load_line_patterns,
