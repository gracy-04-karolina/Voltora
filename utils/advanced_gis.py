import streamlit as st
import pandas as pd
import pydeck as pdk


def show_advanced_gis():

    st.title("🛰️ Voltora - Disaster Intelligence Center")

    # Load city data
    df = pd.read_csv("data/tamilnadu_cities.csv")

    # Assign colors based on disaster type
    color_map = {
        "Safe": [0, 200, 0],
        "Flood": [0, 100, 255],
        "Cyclone": [255, 0, 0],
        "Heatwave": [255, 140, 0],
        "Heavy Rain": [180, 0, 255]
    }

    df["color"] = df["Disaster"].apply(
        lambda x: color_map.get(x, [150, 150, 150])
    )

    # Create glowing circle layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position='[longitude, latitude]',
        get_fill_color='color',
        get_radius=25000,
        pickable=True,
        auto_highlight=True
    )

    # View centered on Tamil Nadu
    view = pdk.ViewState(
        latitude=11.1271,
        longitude=78.6569,
        zoom=6.8,
        pitch=45,
    )

    # Show map
    deck = pdk.Deck(
    initial_view_state=view,
    layers=[layer],
    tooltip={
        "html": """
        <b>{City}</b><br/>
        Disaster: {Disaster}<br/>
        Grid: {GridStatus}
        """
    }
)
    

    st.pydeck_chart(deck)