import streamlit as st
import pandas as pd
import joblib
import os
from datetime import datetime
from PIL import Image
import plotly.express as px

from utils.simulation import generate_sensor_data
from utils.virtual_circuit import simulate_circuit, get_circuit_status
from utils.virtual_sensors import read_virtual_sensors
from utils.circuit_builder import show_circuit_builder
from utils.gauges import create_gauge
from utils.graphs import create_live_graph
from utils.animation import show_grid_status
from utils.scada_animation import show_scada_grid
from utils.report import generate_pdf
from utils.history_dashboard import show_history_dashboard
from utils.gis_map import show_gis_map
from utils.weather_api import get_weather_by_coordinates
from utils.advanced_gis import show_advanced_gis
from utils.control_room import control_room_header
from utils.plotly_gis import show_plotly_map
from utils.demo_mode import generate_demo_data
from streamlit_autorefresh import st_autorefresh
from utils.executive_dashboard import show_executive_dashboard
from utils.notification_center import show_notifications
from utils.animated_logo import show_animated_logo
from utils.startup_animation import startup_animation
from utils.cinematic_startup import cinematic_startup
from utils.alarm import play_alarm


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="GridGuard AI",
    page_icon="⚡",
    layout="wide"
)


# ==================================================
# STARTUP
# ==================================================

if "boot_screen" not in st.session_state:

    cinematic_startup()

    st.session_state.boot_screen = True


st.caption(
    "🕒 " +
    datetime.now().strftime("%d %B %Y | %I:%M:%S %p")
)


if "startup_done" not in st.session_state:

    st.session_state.startup_done = True

    startup_animation()


# ==================================================
# INITIAL SESSION STATE
# ==================================================

if "fault" not in st.session_state:

    st.session_state["fault"] = "Normal"


if "confidence" not in st.session_state:

    st.session_state["confidence"] = 0.0


# ==================================================
# ALARM EVENT STATE
# ==================================================

if "previous_fault" not in st.session_state:

    st.session_state["previous_fault"] = "Normal"


if "alarm_triggered" not in st.session_state:

    st.session_state["alarm_triggered"] = False


# ==================================================
# LOAD CSS
# ==================================================

def load_css():

    if os.path.exists("assets/style.css"):

        with open("assets/style.css") as f:

            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )


load_css()


# ==================================================
# LOAD AI MODEL
# ==================================================

model = joblib.load(
    "fault_model.pkl"
)

encoder = joblib.load(
    "fault_encoder.pkl"
)


# ==================================================
# LOAD IMAGES
# ==================================================

try:

    transformer = Image.open(
        "assets/transformer.png"
    )

    pole = Image.open(
        "assets/pole.png"
    )

    house = Image.open(
        "assets/house.png"
    )

except Exception:

    transformer = None
    pole = None
    house = None


# ==================================================
# SIDEBAR
# ==================================================

if os.path.exists("assets/logo.png"):

    st.sidebar.image(
        "assets/logo.png",
        width=120
    )


menu = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🗺️ Tamil Nadu GIS",
        "📋 Fault History",
        "📈 Analytics",
        "📄 Reports",
        "📊 Live Monitoring",
        "ℹ️ About"
    ]
)


# ==================================================
# HISTORY FILE
# ==================================================

history_file = "history.csv"


if not os.path.exists(history_file):

    history = pd.DataFrame(
        columns=[
            "Time",
            "Area ID",
            "Line ID",
            "Asset ID",
            "Voltage",
            "Current",
            "Frequency",
            "Temperature",
            "Fault",
            "Confidence",
            "Grid Health",
            "Shutdown"
        ]
    )

    history.to_csv(
        history_file,
        index=False
    )


# ==================================================
# DASHBOARD
# ==================================================

if menu == "🏠 Dashboard":

    show_animated_logo()


    # ==================================================
    # DEMO MODE
    # ==================================================

    demo = st.toggle(
        "🎬 Presentation Demo Mode"
    )


    if demo:

        st_autorefresh(
            interval=1500,
            key="demo_refresh"
        )

    else:

        st_autorefresh(
            interval=60000,
            key="weather_refresh"
        )


    st.markdown("---")


    # ==================================================
    # INPUT MODE
    # ==================================================

    mode = st.radio(
        "Choose Input Mode",
        [
            "Manual Input",
            "Live Simulation",
            "⚡ Circuit Builder",
            "Virtual LT Circuit"
        ],
        horizontal=True
    )


    # ==================================================
    # DEFAULT ASSET INFORMATION
    # ==================================================

    asset_id = st.session_state.get(
        "asset_id",
        "MANUAL"
    )

    line_id = st.session_state.get(
        "line_id",
        "MANUAL-LINE"
    )

    area_id = st.session_state.get(
        "area_id",
        "MANUAL-AREA"
    )


    # ==================================================
    # INPUT MODES
    # ==================================================

    if demo:

        # --------------------------------------------------
        # PRESENTATION DEMO
        # --------------------------------------------------

        sensor = generate_demo_data()


        voltage = sensor["Voltage"]

        current = sensor["Current"]

        frequency = sensor["Frequency"]

        temperature = sensor["Temperature"]


        fault = sensor["Fault"]

        confidence = sensor["Confidence"]


        st.session_state["fault"] = fault

        st.session_state["confidence"] = confidence


        st.success(
            "🎬 Presentation Demo Mode Running"
        )


    elif mode == "Manual Input":

        # --------------------------------------------------
        # MANUAL INPUT
        # --------------------------------------------------

        col1, col2 = st.columns(2)


        with col1:

            voltage = st.number_input(
                "🔌 Voltage (V)",
                min_value=0.0,
                value=230.0
            )


            current = st.number_input(
                "⚡ Current (A)",
                min_value=0.0,
                value=5.0
            )


        with col2:

            frequency = st.number_input(
                "📡 Frequency (Hz)",
                min_value=0.0,
                value=50.0
            )


            temperature = st.number_input(
                "🌡 Temperature (°C)",
                min_value=0.0,
                value=30.0
            )


        st.info(
            "Manual electrical values will be analyzed "
            "by the existing GridGuard AI model."
        )


    elif mode == "Live Simulation":

        # --------------------------------------------------
        # LIVE SIMULATION
        # --------------------------------------------------

        sensor = generate_sensor_data()


        voltage = sensor["Voltage"]

        current = sensor["Current"]

        frequency = sensor["Frequency"]

        temperature = sensor["Temperature"]


        st.info(
            "⚡ Live Simulation Mode"
        )


        st.session_state["voltage"] = voltage

        st.session_state["current"] = current

        st.session_state["frequency"] = frequency

        st.session_state["temperature"] = temperature


    elif mode == "⚡ Circuit Builder":

        # ==================================================
        # 3-PHASE LT CIRCUIT BUILDER
        # ==================================================

        circuit_data = show_circuit_builder()


        # --------------------------------------------------
        # CHECK WHETHER SIMULATION HAS BEEN RUN
        # --------------------------------------------------

        if circuit_data.get(
            "simulation_available",
            False
        ):

            # --------------------------------------------------
            # GET VIRTUAL SENSOR VALUES
            # --------------------------------------------------

            voltage = float(
                circuit_data["voltage"]
            )

            current = float(
                circuit_data["current"]
            )

            frequency = float(
                circuit_data["sim_frequency"]
            )

            temperature = float(
                circuit_data["temperature"]
            )


            # --------------------------------------------------
            # GET ASSET IDENTITY
            # --------------------------------------------------

            asset_id = circuit_data.get(
                "asset_id",
                "Unknown"
            )

            line_id = circuit_data.get(
                "line_id",
                "Unknown"
            )

            area_id = circuit_data.get(
                "area_id",
                "Unknown"
            )


            # --------------------------------------------------
            # STORE IDENTITY
            # --------------------------------------------------

            st.session_state["asset_id"] = asset_id

            st.session_state["line_id"] = line_id

            st.session_state["area_id"] = area_id


            # --------------------------------------------------
            # SIMULATION STATE
            # --------------------------------------------------

            circuit_fault = circuit_data.get(
                "simulation_fault",
                "Normal"
            )


            # --------------------------------------------------
            # OUTPUT HEADER
            # --------------------------------------------------

            st.markdown(
                "### 🔌 3-Phase LT Feeder Simulation Output"
            )


            st.caption(
                "Virtual circuit sensor values generated "
                "by the selected Area / Line / Asset."
            )


            # --------------------------------------------------
            # ASSET INFORMATION
            # --------------------------------------------------

            st.info(
                f"📍 Area: **{area_id}**  |  "
                f"⚡ Line: **{line_id}**  |  "
                f"🔌 Asset: **{asset_id}**"
            )


            # --------------------------------------------------
            # VIRTUAL SENSOR VALUES
            # --------------------------------------------------

            a1, a2, a3, a4 = st.columns(4)


            a1.metric(
                "📡 Voltage",
                f"{voltage:.2f} V"
            )


            a2.metric(
                "⚡ Current",
                f"{current:.2f} A"
            )


            a3.metric(
                "📡 Frequency",
                f"{frequency:.2f} Hz"
            )


            a4.metric(
                "🌡 Temperature",
                f"{temperature:.2f} °C"
            )


            # --------------------------------------------------
            # SIMULATION STATUS
            # --------------------------------------------------

            if circuit_fault == "Normal":

                st.success(
                    "🟢 Virtual feeder energized — "
                    "sensor values ready for AI monitoring."
                )


            elif circuit_fault == "Line Break":

                st.error(
                    "🔴 Virtual feeder conductor fault — "
                    "supply interrupted in the simulation."
                )


            else:

                st.warning(
                    f"⚠️ Virtual feeder condition: "
                    f"{circuit_fault}"
                )


            # --------------------------------------------------
            # PROTECTION PATH
            # --------------------------------------------------

            st.markdown(
                f"""
**Virtual protection path:**

11 kV Supply → 11/0.415 kV Transformer →
R/Y/B/N LT Feeder → Consumers →
V/I/F/T Sensors → **GridGuard AI** →
Virtual Relay → Automatic Emergency Shutdown

**Target Line:** `{line_id}`

**Target Asset:** `{asset_id}`
"""
            )


        else:

            st.warning(
                "⚠️ Run the Virtual Circuit simulation "
                "inside the Circuit Builder to generate "
                "V/I/F/T values for AI analysis."
            )

            st.stop()


    elif mode == "Virtual LT Circuit":

        # ==================================================
        # VIRTUAL LT CIRCUIT
        # ==================================================

        st.markdown(
            "### ⚡ Virtual LT Feeder — Circuit Input"
        )


        st.info(
            "Transformer → MCB → LT Cable → "
            "Connected Loads → Virtual Sensors → GridGuard AI"
        )


        # --------------------------------------------------
        # CIRCUIT PARAMETERS
        # --------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)


        with c1:

            source_voltage = st.slider(
                "⚡ Transformer Voltage (V)",
                200.0,
                250.0,
                230.0,
                1.0,
                key="vc_source_voltage"
            )


        with c2:

            line_length = st.slider(
                "📏 LT Cable Length (m)",
                50,
                500,
                100,
                10,
                key="vc_line_length"
            )


        with c3:

            wire_area = st.selectbox(
                "🧵 Cable Size (mm²)",
                [6, 10, 16, 25, 35],
                index=2,
                key="vc_wire_area"
            )


        with c4:

            material = st.selectbox(
                "🔩 Cable Material",
                ["Copper", "Aluminium"],
                index=0,
                key="vc_material"
            )


        # --------------------------------------------------
        # CONNECTED LOADS
        # --------------------------------------------------

        st.markdown(
            "#### 🏠 Connected Loads"
        )


        l1, l2, l3, l4 = st.columns(4)


        with l1:

            lights = st.checkbox(
                "💡 Lighting — 300 W",
                True,
                key="vc_lights"
            )


        with l2:

            fans = st.checkbox(
                "🌀 Fans — 400 W",
                True,
                key="vc_fans"
            )


        with l3:

            refrigerator = st.checkbox(
                "❄ Refrigerator — 450 W",
                True,
                key="vc_refrigerator"
            )


        with l4:

            heavy_load = st.checkbox(
                "🏭 Heavy Load — 2500 W",
                False,
                key="vc_heavy_load"
            )


        # --------------------------------------------------
        # LOAD CALCULATION
        # --------------------------------------------------

        load_power = (

            (300 if lights else 0)

            + (400 if fans else 0)

            + (450 if refrigerator else 0)

            + (2500 if heavy_load else 0)

        )


        if load_power == 0:

            load_power = 100


        # --------------------------------------------------
        # FAULT CONDITION
        # --------------------------------------------------

        line_break = st.toggle(
            "💥 Simulate LT Line Break",
            False,
            key="vc_line_break"
        )


        if line_break:

            circuit_fault = "Line Break"

        elif source_voltage < 215:

            circuit_fault = "Undervoltage"

        elif source_voltage > 245:

            circuit_fault = "Overvoltage"

        elif heavy_load:

            circuit_fault = "Overload"

        else:

            circuit_fault = "Normal"


        # --------------------------------------------------
        # CIRCUIT SIMULATION
        # --------------------------------------------------

        simulation = simulate_circuit(

            source_voltage=source_voltage,

            frequency=50.0,

            material=material,

            length_m=line_length,

            area_mm2=wire_area,

            load_power_w=load_power,

            fault=circuit_fault,

            temperature=30.0

        )


        # --------------------------------------------------
        # VIRTUAL SENSORS
        # --------------------------------------------------

        sensors = read_virtual_sensors(
            simulation
        )


        voltage = sensors["Voltage"]

        current = sensors["Current"]

        frequency = sensors["Frequency"]

        temperature = sensors["Temperature"]


        # --------------------------------------------------
        # VIRTUAL CIRCUIT VISUALIZATION
        # --------------------------------------------------

        st.markdown(
            "### 🔌 Virtual LT Electrical Protection Circuit"
        )


        st.markdown(
            f"""
<div style="
padding:24px;
border-radius:20px;
background:linear-gradient(135deg,#0b1220,#111827);
border:1px solid #334155;
text-align:center;
">

<div style="
font-size:15px;
color:#94a3b8;
margin-bottom:14px;
">
VIRTUAL SOFTWARE CIRCUIT — NO PHYSICAL HARDWARE
</div>

<div style="
display:flex;
align-items:center;
justify-content:center;
gap:10px;
flex-wrap:wrap;
">

<div style="
padding:15px;
border-radius:14px;
border:2px solid #64748b;
min-width:125px;
">
⚡<br>
<b>AC SUPPLY</b><br>
<small>{source_voltage:.1f} V / 50 Hz</small>
</div>

<div style="font-size:26px;">
━━▶
</div>

<div style="
padding:15px;
border-radius:14px;
border:2px solid #64748b;
min-width:125px;
">
🔌<br>
<b>MCB</b><br>
<small>Protection</small>
</div>

<div style="font-size:26px;">
━━▶
</div>

<div style="
padding:15px;
border-radius:14px;
border:2px solid #64748b;
min-width:145px;
">
📏<br>
<b>LT LINE</b><br>
<small>{line_length} m / {material}</small>
</div>

<div style="font-size:26px;">
━━▶
</div>

<div style="
padding:15px;
border-radius:14px;
border:2px solid #64748b;
min-width:135px;
">
🏠<br>
<b>LOAD</b><br>
<small>{load_power} W</small>
</div>

</div>

<div style="
margin:18px auto 0;
max-width:850px;
padding:15px;
border-radius:14px;
border:1px dashed #38bdf8;
">

📡 <b>VIRTUAL SENSOR LAYER</b>

<br><br>

Voltage Sensor
&nbsp;│&nbsp;
Current Sensor
&nbsp;│&nbsp;
Frequency Sensor
&nbsp;│&nbsp;
Temperature Sensor

</div>

<div style="
margin-top:14px;
font-size:14px;
color:#cbd5e1;
">

Sensor measurements →
<b>GridGuard AI</b> →
AI Fault Prediction →
Virtual Relay →
Automatic Emergency Shutdown

</div>

</div>
""",
            unsafe_allow_html=True
        )


        # --------------------------------------------------
        # SENSOR VALUES
        # --------------------------------------------------

        v1, v2, v3, v4 = st.columns(4)


        v1.metric(
            "📡 Voltage Sensor",
            f"{voltage:.2f} V"
        )


        v2.metric(
            "📡 Current Sensor",
            f"{current:.2f} A"
        )


        v3.metric(
            "📡 Frequency Sensor",
            f"{frequency:.2f} Hz"
        )


        v4.metric(
            "📡 Temperature Sensor",
            f"{temperature:.2f} °C"
        )


        # --------------------------------------------------
        # CIRCUIT STATUS
        # --------------------------------------------------

        status = get_circuit_status(
            simulation
        )


        if circuit_fault == "Normal":

            st.success(
                f"🟢 Circuit Status: {status}"
            )


        elif circuit_fault == "Line Break":

            st.error(
                f"🔴 Circuit Status: {status}"
            )


        else:

            st.warning(
                f"⚠️ Circuit Status: {status}"
            )


        st.caption(
            f"Line Resistance: "
            f"{simulation['Line Resistance']} Ω | "
            f"Load Power: "
            f"{simulation['Load Power']} W | "
            f"Cable: "
            f"{material} {wire_area} mm²"
        )


        st.success(
            "🔄 Virtual circuit output is connected "
            "directly to GridGuard AI."
        )


    # ==================================================
    # EXECUTIVE DASHBOARD
    # ==================================================

    fault = st.session_state.get(
        "fault",
        "Normal"
    )


    confidence = st.session_state.get(
        "confidence",
        0
    )


    show_executive_dashboard(
        fault,
        confidence
    )


    # ==================================================
    # LIVE WEATHER
    # ==================================================

    lat = 13.0827

    lon = 80.2707


    weather = get_weather_by_coordinates(
        lat,
        lon
    )


    if weather:

        st.markdown(
            "### 🌦 Live Weather"
        )


        c1, c2, c3, c4 = st.columns(4)


        with c1:

            st.metric(
                "🌡 Temperature",
                f"{weather['temperature']} °C"
            )


        with c2:

            st.metric(
                "💧 Humidity",
                f"{weather['humidity']} %"
            )


        with c3:

            st.metric(
                "💨 Wind",
                f"{weather['wind']} m/s"
            )


        with c4:

            st.metric(
                "☁ Weather",
                weather["weather"]
            )


        st.caption(
            weather["description"]
        )


    # ==================================================
    # LIVE METRICS
    # ==================================================

    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "Voltage",
        f"{voltage} V"
    )


    c2.metric(
        "Current",
        f"{current} A"
    )


    c3.metric(
        "Frequency",
        f"{frequency} Hz"
    )


    c4.metric(
        "Temperature",
        f"{temperature} °C"
    )


    # ==================================================
    # GAUGES
    # ==================================================

    st.subheader(
        "📟 Live SCADA Gauges"
    )


    g1, g2 = st.columns(2)


    with g1:

        st.plotly_chart(
            create_gauge(
                "Voltage (V)",
                voltage,
                0,
                300
            ),
            use_container_width=True
        )


    with g2:

        st.plotly_chart(
            create_gauge(
                "Current (A)",
                current,
                0,
                20
            ),
            use_container_width=True
        )


    g3, g4 = st.columns(2)


    with g3:

        st.plotly_chart(
            create_gauge(
                "Frequency (Hz)",
                frequency,
                45,
                55
            ),
            use_container_width=True
        )


    with g4:

        st.plotly_chart(
            create_gauge(
                "Temperature (°C)",
                temperature,
                0,
                100
            ),
            use_container_width=True
        )


    # ==================================================
    # NOTIFICATIONS
    # ==================================================

    st.markdown("---")


    show_notifications(
        fault
    )


    # ==================================================
    # LIVE SENSOR TRENDS
    # ==================================================

    st.markdown("---")


    st.subheader(
        "📈 Live Sensor Trends"
    )


    if "voltage_history" not in st.session_state:

        st.session_state.voltage_history = []


    if "current_history" not in st.session_state:

        st.session_state.current_history = []


    if "frequency_history" not in st.session_state:

        st.session_state.frequency_history = []


    if "temperature_history" not in st.session_state:

        st.session_state.temperature_history = []


    # --------------------------------------------------
    # STORE VALUES
    # --------------------------------------------------

    st.session_state.voltage_history.append(
        voltage
    )


    st.session_state.current_history.append(
        current
    )


    st.session_state.frequency_history.append(
        frequency
    )


    st.session_state.temperature_history.append(
        temperature
    )


    # --------------------------------------------------
    # KEEP LAST 20
    # --------------------------------------------------

    st.session_state.voltage_history = (
        st.session_state.voltage_history[-20:]
    )


    st.session_state.current_history = (
        st.session_state.current_history[-20:]
    )


    st.session_state.frequency_history = (
        st.session_state.frequency_history[-20:]
    )


    st.session_state.temperature_history = (
        st.session_state.temperature_history[-20:]
    )


    g1, g2 = st.columns(2)


    with g1:

        st.plotly_chart(
            create_live_graph(
                st.session_state.voltage_history,
                "Voltage Trend",
                "Voltage (V)"
            ),
            use_container_width=True
        )


    with g2:

        st.plotly_chart(
            create_live_graph(
                st.session_state.current_history,
                "Current Trend",
                "Current (A)"
            ),
            use_container_width=True
        )


    g3, g4 = st.columns(2)


    with g3:

        st.plotly_chart(
            create_live_graph(
                st.session_state.frequency_history,
                "Frequency Trend",
                "Frequency (Hz)"
            ),
            use_container_width=True
        )


    with g4:

        st.plotly_chart(
            create_live_graph(
                st.session_state.temperature_history,
                "Temperature Trend",
                "Temperature (°C)"
            ),
            use_container_width=True
        )


    # ==================================================
    # AI FAULT PREDICTION
    # ==================================================

    st.markdown("---")


    st.subheader(
        "🧠 GridGuard AI Fault Detection"
    )


    # --------------------------------------------------
    # PREPARE AI INPUT
    # --------------------------------------------------

    new_data = pd.DataFrame({

        "Voltage": [voltage],

        "Current": [current],

        "Frequency": [frequency],

        "Temperature": [temperature]

    })


    # --------------------------------------------------
    # AI MODEL PREDICTION
    # --------------------------------------------------

    prediction = model.predict(
        new_data
    )


    fault = encoder.inverse_transform(
        prediction
    )[0]


    confidence = (
        model.predict_proba(
            new_data
        ).max()
        * 100
    )


    # --------------------------------------------------
    # STORE AI RESULT
    # --------------------------------------------------

    st.session_state["fault"] = fault

    st.session_state["confidence"] = confidence


    # --------------------------------------------------
    # DISPLAY AI RESULT
    # --------------------------------------------------

    st.success(
        f"⚡ Detected Fault: {fault}"
    )


    st.info(
        f"🎯 Confidence: {confidence:.2f}%"
    )


    # ==================================================
    # EVENT-BASED ALARM
    # ==================================================

    previous_fault = st.session_state.get(
        "previous_fault",
        "Normal"
    )


    new_fault_event = (

        fault != "Normal"

        and previous_fault == "Normal"

    )


    sound_file = None


    if fault == "Overload":

        sound_file = (
            "assets/overload.mp3"
        )


    elif fault == "Overvoltage":

        sound_file = (
            "assets/overvoltage.mp3"
        )


    elif fault == "Undervoltage":

        sound_file = (
            "assets/undervoltage.mp3"
        )


    elif fault == "Line Break":

        sound_file = (
            "assets/emergency.mp3"
        )


    # --------------------------------------------------
    # PLAY ALARM ONLY FOR NEW FAULT
    # --------------------------------------------------

    if new_fault_event and sound_file:

        try:

            with open(
                sound_file,
                "rb"
            ) as audio_file:

                st.audio(
                    audio_file.read(),
                    format="audio/mp3",
                    autoplay=True
                )


            st.session_state["alarm_triggered"] = True


        except FileNotFoundError:

            st.warning(
                f"⚠ Alarm file not found: {sound_file}"
            )


    # --------------------------------------------------
    # RESET ALARM WHEN SYSTEM RETURNS TO NORMAL
    # --------------------------------------------------

    if fault == "Normal":

        st.session_state["alarm_triggered"] = False


    # --------------------------------------------------
    # REMEMBER CURRENT FAULT
    # --------------------------------------------------

    st.session_state["previous_fault"] = fault


    # ==================================================
    # GRID HEALTH + PROTECTION
    # ==================================================

    if fault == "Normal":

        shutdown = "NO"

        health = 100


    elif fault == "Overload":

        shutdown = "YES"

        health = 45


    elif fault == "Overvoltage":

        shutdown = "YES"

        health = 40


    elif fault == "Undervoltage":

        shutdown = "YES"

        health = 50


    else:

        shutdown = "YES"

        health = 20


    # ==================================================
    # SAVE HISTORY
    # ==================================================

    history = pd.read_csv(
        history_file
    )


    # --------------------------------------------------
    # ENSURE IDENTITY COLUMNS
    # --------------------------------------------------

    required_columns = [

        "Area ID",

        "Line ID",

        "Asset ID"

    ]


    for column in required_columns:

        if column not in history.columns:

            history[column] = "Unknown"


    # --------------------------------------------------
    # CREATE NEW RECORD
    # --------------------------------------------------

    new_record = pd.DataFrame({

        "Time": [

            datetime.now().strftime(
                "%d-%m-%Y %H:%M:%S"
            )

        ],

        "Area ID": [

            area_id

        ],

        "Line ID": [

            line_id

        ],

        "Asset ID": [

            asset_id

        ],

        "Voltage": [

            voltage

        ],

        "Current": [

            current

        ],

        "Frequency": [

            frequency

        ],

        "Temperature": [

            temperature

        ],

        "Fault": [

            fault

        ],

        "Confidence": [

            round(
                confidence,
                2
            )

        ],

        "Grid Health": [

            health

        ],

        "Shutdown": [

            shutdown

        ]

    })


    history = pd.concat(

        [

            history,

            new_record

        ],

        ignore_index=True

    )


    history.to_csv(

        history_file,

        index=False

    )


    st.success(
        "Prediction Completed Successfully"
    )


    # ==================================================
    # RESULT METRICS
    # ==================================================

    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "⚠ Fault",
        fault
    )


    c2.metric(
        "📊 Confidence",
        f"{confidence:.2f}%"
    )


    c3.metric(
        "💚 Grid Health",
        f"{health}%"
    )


    c4.metric(
        "🚨 Shutdown",
        shutdown
    )


    # ==================================================
    # EMERGENCY SHUTDOWN STATUS
    # ==================================================

    if shutdown == "YES":

        st.error(
            f"""
🚨 Automatic Emergency Shutdown Activated

Target Area: {area_id}

Target Line: {line_id}

Target Asset: {asset_id}

Detected Fault: {fault}
"""
        )


    else:

        st.success(
            "🟢 Grid Operating Normally"
        )


    # ==================================================
    # SCADA SMART GRID
    # ==================================================

    st.markdown("---")


    st.subheader(
        "⚡ SCADA Smart Grid"
    )


    show_scada_grid(
        fault
    )


    # ==================================================
    # AI RECOMMENDATION
    # ==================================================

    st.markdown("---")


    st.subheader(
        "💡 AI Recommendation"
    )


    if fault == "Normal":

        st.success(
            """
Grid operating normally.

No maintenance required.
"""
        )


    elif fault == "Overload":

        st.error(
            """
Reduce connected load immediately.

Inspect transformer.
"""
        )


    elif fault == "Overvoltage":

        st.warning(
            """
Check voltage regulator.

Inspect supply line.
"""
        )


    elif fault == "Undervoltage":

        st.warning(
            """
Inspect LT feeder.

Check transformer output.
"""
        )


    else:

        st.error(
            """
Inspect distribution pole.

Repair broken line.

Restore supply safely.
"""
        )


    # ==================================================
    # PDF REPORT
    # ==================================================

    pdf = generate_pdf(

        voltage=voltage,

        current=current,

        frequency=frequency,

        temperature=temperature,

        fault=fault,

        confidence=confidence,

        health=health,

        shutdown=shutdown

    )


    with open(
        pdf,
        "rb"
    ) as file:

        st.download_button(

            label="📄 Download PDF Report",

            data=file,

            file_name=pdf,

            mime="application/pdf",

            use_container_width=True

        )


    # ==================================================
    # SMART GRID VISUALIZATION
    # ==================================================

    st.markdown("---")


    show_grid_status(
        fault
    )


# ==================================================
# FAULT HISTORY PAGE
# ==================================================

elif menu == "📋 Fault History":

    st.title(
        "📋 Fault History"
    )


    history = pd.read_csv(
        history_file
    )


    if history.empty:

        st.info(
            "No fault history available."
        )


    else:

        st.dataframe(
            history,
            use_container_width=True
        )


        csv = history.to_csv(
            index=False
        ).encode(
            "utf-8"
        )


        st.download_button(

            "⬇ Download History",

            csv,

            "GridGuard_History.csv",

            "text/csv"

        )


# ==================================================
# ANALYTICS PAGE
# ==================================================

elif menu == "📈 Analytics":

    st.title(
        "📈 Grid Analytics"
    )


    show_history_dashboard(
        history_file
    )


    history = pd.read_csv(
        history_file
    )


    if history.empty:

        st.warning(
            "No data available."
        )


    else:

        # --------------------------------------------------
        # VOLTAGE
        # --------------------------------------------------

        st.subheader(
            "Voltage Trend"
        )


        fig1 = px.line(

            history,

            x="Time",

            y="Voltage",

            markers=True,

            title="Voltage vs Time"

        )


        st.plotly_chart(
            fig1,
            use_container_width=True
        )


        # --------------------------------------------------
        # CURRENT
        # --------------------------------------------------

        st.subheader(
            "Current Trend"
        )


        fig2 = px.line(

            history,

            x="Time",

            y="Current",

            markers=True,

            title="Current vs Time"

        )


        st.plotly_chart(
            fig2,
            use_container_width=True
        )


        # --------------------------------------------------
        # TEMPERATURE
        # --------------------------------------------------

        st.subheader(
            "Temperature Trend"
        )


        fig3 = px.line(

            history,

            x="Time",

            y="Temperature",

            markers=True,

            title="Temperature vs Time"

        )


        st.plotly_chart(
            fig3,
            use_container_width=True
        )


        # --------------------------------------------------
        # FAULT DISTRIBUTION
        # --------------------------------------------------

        st.subheader(
            "Fault Distribution"
        )


        fig4 = px.pie(

            history,

            names="Fault",

            title="Detected Faults"

        )


        st.plotly_chart(
            fig4,
            use_container_width=True
        )


        # --------------------------------------------------
        # PROJECT STATISTICS
        # --------------------------------------------------

        st.markdown("---")


        st.subheader(
            "📊 Project Statistics"
        )


        c1, c2, c3 = st.columns(3)


        c1.metric(
            "Predictions",
            len(history)
        )


        c2.metric(
            "Fault Types",
            history["Fault"].nunique()
        )


        c3.metric(
            "Average Grid Health",
            f"{history['Grid Health'].mean():.1f}%"
        )


# ==================================================
# REPORTS PAGE
# ==================================================

elif menu == "📄 Reports":

    st.title(
        "📄 Reports"
    )


    history = pd.read_csv(
        history_file
    )


    if history.empty:

        st.warning(
            "No report available."
        )


    else:

        st.subheader(
            "Latest Fault Report"
        )


        latest = history.iloc[-1]


        st.write(
            "### Prediction Summary"
        )


        st.write(
            f"**Time:** {latest['Time']}"
        )


        if "Area ID" in history.columns:

            st.write(
                f"**Area ID:** {latest['Area ID']}"
            )


        if "Line ID" in history.columns:

            st.write(
                f"**Line ID:** {latest['Line ID']}"
            )


        if "Asset ID" in history.columns:

            st.write(
                f"**Asset ID:** {latest['Asset ID']}"
            )


        st.write(
            f"**Voltage:** {latest['Voltage']} V"
        )


        st.write(
            f"**Current:** {latest['Current']} A"
        )


        st.write(
            f"**Frequency:** {latest['Frequency']} Hz"
        )


        st.write(
            f"**Temperature:** {latest['Temperature']} °C"
        )


        st.write(
            f"**Fault:** {latest['Fault']}"
        )


        st.write(
            f"**Confidence:** {latest['Confidence']} %"
        )


        st.write(
            f"**Grid Health:** {latest['Grid Health']} %"
        )


        st.write(
            f"**Shutdown:** {latest['Shutdown']}"
        )


        csv = history.to_csv(
            index=False
        ).encode(
            "utf-8"
        )


        st.download_button(

            "⬇ Download Complete Report",

            csv,

            "GridGuard_Report.csv",

            "text/csv"

        )


# ==================================================
# LIVE MONITORING
# ==================================================

elif menu == "📊 Live Monitoring":

    st.title(
        "📊 Live Grid Monitoring"
    )


    history = pd.read_csv(
        history_file
    )


    if history.empty:

        st.warning(
            "No sensor data available."
        )


    else:

        latest = history.iloc[-1]


        c1, c2, c3, c4 = st.columns(4)


        c1.metric(
            "🔌 Voltage",
            f"{latest['Voltage']} V"
        )


        c2.metric(
            "⚡ Current",
            f"{latest['Current']} A"
        )


        c3.metric(
            "🌡 Temperature",
            f"{latest['Temperature']} °C"
        )


        c4.metric(
            "💚 Grid Health",
            f"{latest['Grid Health']} %"
        )


        st.markdown("---")


        st.subheader(
            "Latest Fault"
        )


        if latest["Shutdown"] == "YES":

            st.error(
                f"""
Fault : {latest['Fault']}

Emergency Shutdown Activated

Area : {latest.get('Area ID', 'Unknown')}

Line : {latest.get('Line ID', 'Unknown')}

Asset : {latest.get('Asset ID', 'Unknown')}
"""
            )


        else:

            st.success(
                "Grid Operating Normally"
            )


# ==================================================
# ABOUT
# ==================================================

elif menu == "ℹ️ About":

    st.title(
        "ℹ️ About GridGuard AI"
    )


    st.markdown(
        """
# ⚡ GridGuard AI

GridGuard AI is an Artificial Intelligence based Low Tension (LT)
power distribution fault detection system.

The application predicts:

- Overload
- Overvoltage
- Undervoltage
- Line Break
- Normal

using Machine Learning.

---

## Technologies Used

- Python
- Streamlit
- Scikit-Learn
- Pandas
- Plotly
- Joblib

---

## Features

✅ AI Fault Prediction

✅ Emergency Shutdown

✅ Smart Grid Visualization

✅ Fault History

✅ Analytics Dashboard

✅ Reports

✅ Live Monitoring

---

Developed as an AI & ML Project.
"""
    )


# ==================================================
# TAMIL NADU GIS
# ==================================================

elif menu == "🗺️ Tamil Nadu GIS":

    show_plotly_map()