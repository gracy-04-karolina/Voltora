import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


def show_smart_gis():

    st.title("🛰️ Voltora Smart Disaster Monitoring")

    df = pd.read_csv("data/tamilnadu_cities.csv")

    # Satellite Map
    m = folium.Map(
        location=[11.1271, 78.6569],
        zoom_start=7,
        tiles=None
    )

    # Street Map
    folium.TileLayer(
        "OpenStreetMap",
        name="Street"
    ).add_to(m)

    # Satellite View
    folium.TileLayer(
        tiles="Esri.WorldImagery",
        attr="Esri",
        name="Satellite"
    ).add_to(m)

    # Terrain
    folium.TileLayer(
        "Stamen Terrain",
        name="Terrain"
    ).add_to(m)

    folium.LayerControl().add_to(m)

    st_folium(
        m,
        width=1200,
        height=700
    )