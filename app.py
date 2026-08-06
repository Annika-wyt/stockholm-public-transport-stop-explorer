"""Barebones Streamlit starter for the Stockholm Stop Explorer."""

import streamlit as st

from transport_data import load_services, load_stations


st.set_page_config(
    page_title="Stockholm Stop Explorer",
    page_icon="🚏",
    layout="wide",
)

st.title("Stockholm Public Transport Stop Explorer")
st.write("Build an app where a user selects a station and explores its services.")


@st.cache_data
def load_app_data():
    """Load the prepared files once per Streamlit session."""

    return load_stations(), load_services()


stations, services = load_app_data()

st.success(f"Loaded {len(stations)} stations and {len(services)} services.")
st.caption("This starter map is not selectable yet. That is one of your tasks.")

st.map(
    stations,
    latitude="latitude",
    longitude="longitude",
    zoom=11,
    size=30,
)

st.subheader("Selected station")
st.info("TODO: Display information after the user selects a station.")

