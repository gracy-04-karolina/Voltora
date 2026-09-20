import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.ai_recommendation import get_ai_recommendation
from utils.event_log import show_event_log
from utils.weather_api import get_weather_by_coordinates
from utils.live_dashboard import get_live_status
from utils.power_animation import add_power_flow
import time
from utils.fault_visualization import get_fault_connection
from utils.alarm_panel import show_alarm_panel
from utils.scada_panel import show_scada_panel

def show_plotly_map():
    fault = st.session_state.get("fault", "Normal")
    fault_connection = get_fault_connection(fault)
    
    st.title("🛰️ GridGuard AI - Disaster Intelligence Center")
    show_alarm_panel(fault)
    if fault != "Normal":

        st.error(
            f"""
🚨 AUTOMATIC EMERGENCY SHUTDOWN ACTIVATED

Fault Detected: {fault}

AI has isolated the affected transmission section.
"""
         )
    else:
        st.success("🟢 Grid Operating Normally")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
        "⚡ Grid Health",
        "96%",
        "+2%"
    )

    with c2:
        st.metric(
        "🚨 Active Faults",
        "2",
        "-1"
    )

    with c3:
        st.metric(
        "🌩 Disaster Risk",
        "Medium"
    )

    with c4:
        st.metric(
        "🔌 Power Supply",
        "98%"
    )

    df = pd.read_csv("data/tamilnadu_cities.csv")
    st.write("CSV Shape:", df.shape)
    st.write("Columns:", df.columns)
    st.dataframe(df)

    # ==========================================
    # Select City
    # ==========================================

    st.write("Available Cities:")
    st.write(df["City"].unique())

    selected_city = st.selectbox(
       "📍 Select City",
     options=df["City"].dropna().unique()
    )

    st.write("Selected City:", selected_city)

    selected = df[df["City"] == selected_city].iloc[0]

    lat = selected["latitude"]
    lon = selected["longitude"]

    st.write("Latitude:", lat)
    st.write("Longitude:", lon)

    frame = int(time.time() * 2) % 20
    # ==========================================
    # Live Weather
    # ==========================================
    weather = get_weather_by_coordinates(lat, lon)

    if weather:

      st.markdown("## 🌦 Live Weather")

      w1, w2, w3, w4 = st.columns(4)

      with w1:
        st.metric(
            "🌡 Temperature",
            f"{weather['temperature']} °C"
        )

      with w2:
        st.metric(
            "💧 Humidity",
            f"{weather['humidity']} %"
        )

      with w3:
        st.metric(
            "💨 Wind",
            f"{weather['wind']} m/s"
        )

      with w4:
        st.metric(
            "☁ Weather",
            weather["weather"]
        )

      st.caption(weather["description"])
    else:
      st.warning("⚠ Weather data unavailable")


     # ==========================================
     # AI Disaster Alert
     # ==========================================

    disaster = selected["Disaster"]
    city = selected["City"]

    if disaster == "Cyclone":

         st.error(
          f"🚨 HIGH ALERT : Cyclone Risk in {city}. AI recommends emergency shutdown."
         ) 

    elif disaster == "Flood":

         st.warning(
          f"🌊 Flood Alert in {city}. Protect substations and transformers."
         )

    elif disaster == "Heatwave":

         st.warning(
           f"🔥 Heatwave in {city}. Monitor transformer temperature."
         )

    elif disaster == "Heavy Rain":

         st.info(
         f"🌧 Heavy Rain in {city}. Monitor feeder lines."
         )

    else:

     disaster = "Safe"
     st.success("✅ No disaster risk detected.")

    recommendation = get_ai_recommendation(disaster)

    st.markdown("## 🤖 AI Recommendation")

    st.metric(
       "Risk Level",
       recommendation["level"]
    )

    for item in recommendation["action"]:
      st.success("✔ " + item)

    # Create the map AFTER the loop
    fig = px.scatter_map(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="City",
        hover_data={
          "Disaster": True,
          "GridStatus": True,
          "latitude": False,
          "longitude": False
         },
        color="Disaster",
        color_discrete_map={
         "Safe": "#00FF00",
         "Flood": "#0080FF",
         "Cyclone": "#FF0000",
         "Heatwave": "#FF8C00",
         "Heavy Rain": "#8000FF"
         },
        zoom=6,
        height=700
    )

    fig.update_traces(
         marker=dict(
          size=18,
          opacity=0.9
         )
     )


   
    # ---------------------------------------
    # Transmission Line Connections
    # ---------------------------------------

    connections = [
        ("Chennai", "Salem"),
        ("Salem", "Coimbatore"),
        ("Salem", "Erode"),
        ("Salem", "Tiruchirappalli"),
        ("Tiruchirappalli", "Thanjavur"),
        ("Tiruchirappalli", "Madurai"),
        ("Madurai", "Tirunelveli"),
        ("Tirunelveli", "Kanyakumari"),
        ("Coimbatore", "Tiruppur"),
    ]

    for city1, city2 in connections:

        p1 = df[df["City"] == city1].iloc[0]
        p2 = df[df["City"] == city2].iloc[0]

        color = "cyan"
        width = 4
        if fault_connection and set(fault_connection) == set((city1, city2)):

            color = "#ff3030"
            width = 8

        fig.add_trace(
            go.Scattermap(
                lat=[p1["latitude"], p2["latitude"]],
                lon=[p1["longitude"], p2["longitude"]],
                mode="lines",
                line=dict(
                    color=color,
                    width=width
                ),
                hoverinfo="skip",
                showlegend=False
            )
        )

    if fault_connection:

        city1, city2 = fault_connection

        p1 = df[df["City"] == city1].iloc[0]
        p2 = df[df["City"] == city2].iloc[0]

        lat = (p1["latitude"] + p2["latitude"]) / 2
        lon = (p1["longitude"] + p2["longitude"]) / 2

        fig.add_trace(
            go.Scattermap(
                lat=[lat],
                lon=[lon],
                mode="markers+text",
                marker=dict(
                    size=24,
                    color="#ff3030",
                    symbol="x"
                ),
                text=["FAULT"],
                textfont=dict(
                    size=14,
                    color="#ff3030"
                ),
                textposition="top center",
                showlegend=False
            )
        )

    fig = add_power_flow(
        fig,
        df,
        connections,
        frame
    )

    fig.update_layout(
        map_style="carto-darkmatter",
        paper_bgcolor="#08192d",
        plot_bgcolor="#08192d",
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),
        font=dict(
            color="white",
            size=14
        )
    )

    st.markdown("""
## 🛰️ Smart Disaster Intelligence Center

**Live AI Monitoring | Tamil Nadu Power Grid | Disaster Analytics**
""")

    left, right = st.columns([3, 1])

    with left:
        st.session_state["gis_fig"] = fig
        st.plotly_chart(
            fig,
            use_container_width=True
        )

    status = get_live_status()

    with right:
        show_scada_panel(
            status,
            fault
        )

    st.markdown("---")

    show_event_log()


    
    
   