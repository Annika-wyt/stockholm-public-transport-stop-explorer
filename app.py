"""Streamlit interface for the Stockholm Public Transport Stop Explorer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
import pydeck as pdk
import streamlit as st

from transport_data import (
    TransportDataError,
    get_services_for_station,
    get_station,
    get_station_summary,
    group_services_by_type,
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
def load_app_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the two small application files once per Streamlit session."""

    return load_stations(), load_services()


def build_station_map(stations: pd.DataFrame) -> pdk.Deck:
    """Build the selectable Stockholm station map."""

    station_layer = pdk.Layer(
        "ScatterplotLayer",
        id=MAP_LAYER_ID,
        data=stations,
        get_position="[longitude, latitude]",
        get_fill_color=[236, 72, 153, 210],
        get_line_color=[131, 24, 67, 255],
        get_radius=90,
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
        initial_view_state=pdk.ViewState(**STOCKHOLM_VIEW),
        layers=[station_layer],
        tooltip={"text": "{station_name}\nClick to explore"},
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
                use_container_width=True,
                height=table_height,
            )


def main() -> None:
    st.set_page_config(
        page_title="Stockholm Stop Explorer",
        page_icon="🚏",
        layout="wide",
    )

    st.title("Stockholm Public Transport Stop Explorer")
    st.write(
        "Click a station on the map to see which public transport services "
        "stop there."
    )

    try:
        stations, services = load_app_data()
    except TransportDataError as error:
        st.error(str(error))
        st.stop()

    map_column, details_column = st.columns([3, 2], gap="large")

    with map_column:
        map_event = st.pydeck_chart(
            build_station_map(stations),
            on_select="rerun",
            selection_mode="single-object",
            key="station-map",
            height=620,
        )
        st.caption(
            f"Showing {len(stations)} stations from the static 1 August 2026 feed."
        )

    selected_station_id = get_selected_station_id(map_event)

    with details_column:
        st.markdown("### Selected station")
        if selected_station_id is None:
            st.info("Select one of the pink map markers to explore a station.")
        else:
            station = get_station(stations, selected_station_id)
            if station is None:
                st.warning("The selected station could not be found.")
            else:
                station_services = get_services_for_station(
                    services, selected_station_id
                )
                render_station_details(station, station_services)


if __name__ == "__main__":
    main()

