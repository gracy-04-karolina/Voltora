import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


def show_gis_map():

    st.subheader("🗺️ GIS Disaster Risk Map")

    df = pd.read_csv("data/disaster_zones.csv")

    # Select city
    selected_city = st.selectbox(
        "📍 Select Location",
        df["Location"].unique()
    )

    # Get selected row
    row = df[df["Location"] == selected_city].iloc[0]

    lat = row["latitude"]
    lon = row["longitude"]

    # Create map centered on selected city
    m = folium.Map(
        location=[lat, lon],
        zoom_start=14,
        tiles="OpenStreetMap"
    )

    colors = {
        "Safe": "green",
        "Flood": "blue",
        "Cyclone": "orange",
        "Landslide": "red"
    }

    for _, r in df.iterrows():

        popup = f"""
        <b>📍 Location:</b> {r['Location']}<br>
        <b>🌍 Disaster Zone:</b> {r['Risk']}<br>
        <b>⚡ Fault:</b> {r['Fault']}<br>
        <b>🚦 Status:</b> {r['Status']}
        """

        folium.Marker(
            location=[r["latitude"], r["longitude"]],
            popup=popup,
            tooltip=r["Location"],
            icon=folium.Icon(
                color=colors.get(r["Risk"], "gray"),
                icon="info-sign"
            )
        ).add_to(m)

    st_folium(m, width=1000, height=600)

    st.markdown("---")

    st.subheader("📋 Disaster Zone Details")
    st.dataframe(df, use_container_width=True)

    # Return selected location
    return lat, lon