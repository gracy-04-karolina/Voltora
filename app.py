import os
from pathlib import Path
from datetime import datetime

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from streamlit_autorefresh import st_autorefresh

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
from utils.weather_api import get_weather_by_coordinates
from utils.plotly_gis import show_plotly_map
from utils.demo_mode import generate_demo_data
from utils.executive_dashboard import show_executive_dashboard
from utils.notification_center import show_notifications
from utils.animated_logo import show_animated_logo
from utils.startup_animation import startup_animation
from utils.cinematic_startup import cinematic_startup


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"

MODEL_FILE = BASE_DIR / "fault_model.pkl"

ENCODER_FILE = BASE_DIR / "fault_encoder.pkl"

HISTORY_FILE = BASE_DIR / "history.csv"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Voltora",
    page_icon="⚡",
    layout="wide"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def asset_path(filename):
    """
    Return an absolute path inside the assets directory.
    """
    return ASSETS_DIR / filename


def initialize_session_state():
    """
    Initialize all required Streamlit session-state variables.
    """

    defaults = {
        "fault": "Normal",
        "confidence": 0.0,
        "previous_fault": "Normal",
        "alarm_triggered": False,

        "asset_id": "MANUAL",
        "line_id": "MANUAL-LINE",
        "area_id": "MANUAL-AREA",

        "voltage_history": [],
        "current_history": [],
        "frequency_history": [],
        "temperature_history": [],

        "last_prediction_signature": None,

        "last_history_signature": None,

        "model_error": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


def load_css():
    """
    Load custom CSS if available.
    """

    css_file = asset_path("style.css")

    if css_file.exists():

        try:

            with open(
                css_file,
                "r",
                encoding="utf-8"
            ) as file:

                st.markdown(
                    f"<style>{file.read()}</style>",
                    unsafe_allow_html=True
                )

        except Exception as error:

            st.warning(
                f"Unable to load custom CSS: {error}"
            )


def load_ai_model():
    """
    Safely load the trained model and encoder.
    """

    model = None
    encoder = None

    if not MODEL_FILE.exists():

        st.error(
            f"❌ AI model not found:\n\n"
            f"`{MODEL_FILE}`"
        )

        return None, None

    if not ENCODER_FILE.exists():

        st.error(
            f"❌ Fault encoder not found:\n\n"
            f"`{ENCODER_FILE}`"
        )

        return None, None

    try:

        model = joblib.load(
            MODEL_FILE
        )

        encoder = joblib.load(
            ENCODER_FILE
        )

    except Exception as error:

        st.error(
            "❌ Unable to load the AI model.\n\n"
            f"Error: `{error}`"
        )

        return None, None

    return model, encoder


def initialize_history_file():
    """
    Create history.csv if it does not exist.
    """

    columns = [
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

    if not HISTORY_FILE.exists():

        history = pd.DataFrame(
            columns=columns
        )

        history.to_csv(
            HISTORY_FILE,
            index=False
        )

    else:

        try:

            history = pd.read_csv(
                HISTORY_FILE
            )

            changed = False

            for column in columns:

                if column not in history.columns:

                    if column in [
                        "Area ID",
                        "Line ID",
                        "Asset ID"
                    ]:

                        history[column] = "Unknown"

                    else:

                        history[column] = ""

                    changed = True

            if changed:

                history.to_csv(
                    HISTORY_FILE,
                    index=False
                )

        except Exception:

            history = pd.DataFrame(
                columns=columns
            )

            history.to_csv(
                HISTORY_FILE,
                index=False
            )


def calculate_grid_health(fault):
    """
    Calculate the demo grid-health value and shutdown state
    using the same mapping as the original application.
    """

    if fault == "Normal":

        return 100, "NO"

    if fault == "Overload":

        return 45, "YES"

    if fault == "Overvoltage":

        return 40, "YES"

    if fault == "Undervoltage":

        return 50, "YES"

    return 20, "YES"


def normalize_fault_name(fault):
    """
    Normalize fault names coming from the encoder/model/demo.
    """

    if fault is None:

        return "Normal"

    text = str(fault).strip()

    fault_map = {
        "NORMAL": "Normal",
        "Normal": "Normal",

        "OVERLOAD": "Overload",
        "Overload": "Overload",

        "OVERVOLTAGE": "Overvoltage",
        "Overvoltage": "Overvoltage",

        "UNDERVOLTAGE": "Undervoltage",
        "Undervoltage": "Undervoltage",

        "LINE BREAK": "Line Break",
        "LINE_BREAK": "Line Break",
        "Line Break": "Line Break",
    }

    return fault_map.get(
        text,
        text
    )


def predict_fault(
    model,
    encoder,
    voltage,
    current,
    frequency,
    temperature
):
    """
    Run the trained Voltora model.

    IMPORTANT:
    The feature order must match the order used when
    fault_model.pkl was trained:

        Voltage
        Current
        Frequency
        Temperature
    """

    new_data = pd.DataFrame(
        {
            "Voltage": [float(voltage)],
            "Current": [float(current)],
            "Frequency": [float(frequency)],
            "Temperature": [float(temperature)]
        }
    )

    try:

        prediction = model.predict(
            new_data
        )

        decoded = encoder.inverse_transform(
            prediction
        )

        fault = normalize_fault_name(
            decoded[0]
        )

        confidence = 0.0

        if hasattr(
            model,
            "predict_proba"
        ):

            try:

                probabilities = model.predict_proba(
                    new_data
                )

                confidence = (
                    float(probabilities.max())
                    * 100
                )

            except Exception:

                confidence = 0.0

        return (
            fault,
            confidence,
            new_data,
            None
        )

    except Exception as error:

        return (
            "Normal",
            0.0,
            new_data,
            error
        )


def get_alarm_file(fault):
    """
    Return the appropriate alarm file for a fault.
    """

    alarm_files = {
        "Overload": "overload.mp3",
        "Overvoltage": "overvoltage.mp3",
        "Undervoltage": "undervoltage.mp3",
        "Line Break": "emergency.mp3"
    }

    filename = alarm_files.get(
        fault
    )

    if filename is None:

        return None

    return asset_path(
        filename
    )


def handle_alarm(fault):
    """
    Trigger alarm when the system enters a fault condition.

    Alarm is triggered when:
    Normal -> Fault
    OR
    Fault A -> Fault B
    """

    previous_fault = st.session_state.get(
        "previous_fault",
        "Normal"
    )

    fault = normalize_fault_name(fault)
    previous_fault = normalize_fault_name(previous_fault)

    new_fault_event = (
        fault != "Normal"
        and fault != previous_fault
    )

    sound_file = get_alarm_file(
        fault
    )

    if new_fault_event and sound_file:

        if sound_file.exists():

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

                st.session_state[
                    "alarm_triggered"
                ] = True

            except Exception as error:

                st.warning(
                    f"⚠️ Unable to play alarm: {error}"
                )

        else:

            st.warning(
                f"⚠️ Alarm file not found: `{sound_file}`"
            )

    if fault == "Normal":

        st.session_state[
            "alarm_triggered"
        ] = False

    st.session_state[
        "previous_fault"
    ] = fault


def create_history_signature(
    area_id,
    line_id,
    asset_id,
    voltage,
    current,
    frequency,
    temperature,
    fault,
    confidence
):
    """
    Create a unique signature for a prediction.

    This prevents Streamlit reruns from writing the exact
    same prediction to history repeatedly.
    """

    return (
        str(area_id),
        str(line_id),
        str(asset_id),
        round(float(voltage), 4),
        round(float(current), 4),
        round(float(frequency), 4),
        round(float(temperature), 4),
        str(fault),
        round(float(confidence), 4)
    )


def save_history(
    area_id,
    line_id,
    asset_id,
    voltage,
    current,
    frequency,
    temperature,
    fault,
    confidence,
    health,
    shutdown
):
    """
    Save a prediction to history.csv only once for the
    current unique sensor/prediction signature.
    """

    signature = create_history_signature(
        area_id,
        line_id,
        asset_id,
        voltage,
        current,
        frequency,
        temperature,
        fault,
        confidence
    )

    if (
        st.session_state.get(
            "last_history_signature"
        )
        == signature
    ):

        return False

    try:

        history = pd.read_csv(
            HISTORY_FILE
        )

    except Exception:

        history = pd.DataFrame()

    required_columns = [
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

    for column in required_columns:

        if column not in history.columns:

            history[column] = ""

    new_record = pd.DataFrame(
        {
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
        }
    )

    history = pd.concat(
        [
            history,
            new_record
        ],
        ignore_index=True
    )

    history.to_csv(
        HISTORY_FILE,
        index=False
    )

    st.session_state[
        "last_history_signature"
    ] = signature

    return True


def update_sensor_history(
    voltage,
    current,
    frequency,
    temperature
):
    """
    Maintain the last 20 sensor readings.
    """

    st.session_state[
        "voltage_history"
    ].append(
        float(voltage)
    )

    st.session_state[
        "current_history"
    ].append(
        float(current)
    )

    st.session_state[
        "frequency_history"
    ].append(
        float(frequency)
    )

    st.session_state[
        "temperature_history"
    ].append(
        float(temperature)
    )

    st.session_state[
        "voltage_history"
    ] = st.session_state[
        "voltage_history"
    ][-20:]

    st.session_state[
        "current_history"
    ] = st.session_state[
        "current_history"
    ][-20:]

    st.session_state[
        "frequency_history"
    ] = st.session_state[
        "frequency_history"
    ][-20:]

    st.session_state[
        "temperature_history"
    ] = st.session_state[
        "temperature_history"
    ][-20:]


def show_ai_recommendation(fault):
    """
    Display the appropriate recommendation.
    """

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


def show_weather():
    """
    Display live Chennai weather.
    """

    lat = 13.0827
    lon = 80.2707

    try:

        weather = get_weather_by_coordinates(
            lat,
            lon
        )

    except Exception as error:

        st.warning(
            f"Weather service unavailable: {error}"
        )

        return

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


# ============================================================
# INITIALIZE
# ============================================================

initialize_session_state()

load_css()


# ============================================================
# STARTUP
# ============================================================

if "boot_screen" not in st.session_state:

    cinematic_startup()

    st.session_state.boot_screen = True


st.caption(
    "🕒 "
    + datetime.now().strftime(
        "%d %B %Y | %I:%M:%S %p"
    )
)


if "startup_done" not in st.session_state:

    st.session_state.startup_done = True

    startup_animation()


# ============================================================
# LOAD AI MODEL
# ============================================================

model, encoder = load_ai_model()


# ============================================================
# LOAD IMAGES
# ============================================================

try:

    transformer = Image.open(
        asset_path("transformer.png")
    )

    pole = Image.open(
        asset_path("pole.png")
    )

    house = Image.open(
        asset_path("house.png")
    )

except Exception:

    transformer = None
    pole = None
    house = None


# ============================================================
# SIDEBAR
# ============================================================

logo_file = asset_path(
    "logo.png"
)

if logo_file.exists():

    st.sidebar.image(
        str(logo_file),
        width=120
    )


st.sidebar.title(
    "⚡ Voltora"
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


# ============================================================
# INITIALIZE HISTORY
# ============================================================

initialize_history_file()


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    show_animated_logo()

    # ========================================================
    # DEMO MODE
    # ========================================================

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

    # ========================================================
    # INPUT MODE
    # ========================================================

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

    # ========================================================
    # DEFAULT ASSET INFORMATION
    # ========================================================

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

    # ========================================================
    # DEFAULT VARIABLES
    # ========================================================

    voltage = 230.0
    current = 5.0
    frequency = 50.0
    temperature = 30.0

    demo_fault = None
    demo_confidence = None

    # ========================================================
    # PRESENTATION DEMO
    # ========================================================

    if demo:

        sensor = generate_demo_data()

        voltage = float(
            sensor["Voltage"]
        )

        current = float(
            sensor["Current"]
        )

        frequency = float(
            sensor["Frequency"]
        )

        temperature = float(
            sensor["Temperature"]
        )

        demo_fault = normalize_fault_name(
            sensor["Fault"]
        )

        demo_confidence = float(
            sensor["Confidence"]
        )

        st.session_state[
            "fault"
        ] = demo_fault

        st.session_state[
            "confidence"
        ] = demo_confidence

        st.success(
            "🎬 Presentation Demo Mode Running"
        )

    # ========================================================
    # MANUAL INPUT
    # ========================================================

    elif mode == "Manual Input":

        col1, col2 = st.columns(2)

        with col1:

            voltage = st.number_input(
                "🔌 Voltage (V)",
                min_value=0.0,
                value=230.0,
                key="manual_voltage"
            )

            current = st.number_input(
                "⚡ Current (A)",
                min_value=0.0,
                value=5.0,
                key="manual_current"
            )

        with col2:

            frequency = st.number_input(
                "📡 Frequency (Hz)",
                min_value=0.0,
                value=50.0,
                key="manual_frequency"
            )

            temperature = st.number_input(
                "🌡 Temperature (°C)",
                min_value=0.0,
                value=30.0,
                key="manual_temperature"
            )

        st.info(
            "Manual electrical values will be analyzed "
            "by the existing Voltora model."
        )

    # ========================================================
    # LIVE SIMULATION
    # ========================================================

    elif mode == "Live Simulation":

        sensor = generate_sensor_data()

        voltage = float(
            sensor["Voltage"]
        )

        current = float(
            sensor["Current"]
        )

        frequency = float(
            sensor["Frequency"]
        )

        temperature = float(
            sensor["Temperature"]
        )

        st.info(
            "⚡ Live Simulation Mode"
        )

        st.session_state[
            "voltage"
        ] = voltage

        st.session_state[
            "current"
        ] = current

        st.session_state[
            "frequency"
        ] = frequency

        st.session_state[
            "temperature"
        ] = temperature

    # ========================================================
    # CIRCUIT BUILDER
    # ========================================================

    elif mode == "⚡ Circuit Builder":

        st.markdown(
            "## ⚡ 3-Phase LT Circuit Builder"
        )

        circuit_data = show_circuit_builder()

        if circuit_data.get(
            "simulation_available",
            False
        ):

            voltage = float(
                circuit_data.get(
                    "voltage",
                    230.0
                )
            )

            current = float(
                circuit_data.get(
                    "current",
                    5.0
                )
            )

            frequency = float(
                circuit_data.get(
                    "sim_frequency",
                    50.0
                )
            )

            temperature = float(
                circuit_data.get(
                    "temperature",
                    30.0
                )
            )

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

            st.session_state[
                "asset_id"
            ] = asset_id

            st.session_state[
                "line_id"
            ] = line_id

            st.session_state[
                "area_id"
            ] = area_id

            circuit_fault = normalize_fault_name(
                circuit_data.get(
                    "simulation_fault",
                    "Normal"
                )
            )

            st.markdown(
                "### 🔌 3-Phase LT Feeder Simulation Output"
            )

            st.caption(
                "Virtual circuit sensor values generated "
                "by the selected Area / Line / Asset."
            )

            st.info(
                f"📍 Area: **{area_id}**  |  "
                f"⚡ Line: **{line_id}**  |  "
                f"🔌 Asset: **{asset_id}**"
            )

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

            st.markdown(
                f"""
**Virtual protection path:**

11 kV Supply → 11/0.415 kV Transformer →
R/Y/B/N LT Feeder → Consumers →
V/I/F/T Sensors → **Voltora** →
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

    # ========================================================
    # VIRTUAL LT CIRCUIT
    # ========================================================

    elif mode == "Virtual LT Circuit":

        st.markdown(
            "### ⚡ Virtual LT Feeder — Circuit Input"
        )

        st.info(
            "Transformer → MCB → LT Cable → "
            "Connected Loads → Virtual Sensors → Voltora"
        )

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

        load_power = (
            (300 if lights else 0)
            + (400 if fans else 0)
            + (450 if refrigerator else 0)
            + (2500 if heavy_load else 0)
        )

        if load_power == 0:

            load_power = 100

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

        sensors = read_virtual_sensors(
            simulation
        )

        voltage = float(
            sensors["Voltage"]
        )

        current = float(
            sensors["Current"]
        )

        frequency = float(
            sensors["Frequency"]
        )

        temperature = float(
            sensors["Temperature"]
        )

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
<b>Voltora</b> →
AI Fault Prediction →
Virtual Relay →
Automatic Emergency Shutdown

</div>

</div>
""",
            unsafe_allow_html=True
        )

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
            "directly to Voltora."
        )

    # ========================================================
    # EXECUTIVE DASHBOARD
    # ========================================================

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

    # ========================================================
    # WEATHER
    # ========================================================

    show_weather()

    # ========================================================
    # LIVE METRICS
    # ========================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Voltage",
        f"{voltage:.2f} V"
    )

    c2.metric(
        "Current",
        f"{current:.2f} A"
    )

    c3.metric(
        "Frequency",
        f"{frequency:.2f} Hz"
    )

    c4.metric(
        "Temperature",
        f"{temperature:.2f} °C"
    )

    # ========================================================
    # GAUGES
    # ========================================================

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

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    st.markdown("---")

    show_notifications(
        fault
    )

    # ========================================================
    # SENSOR HISTORY
    # ========================================================

    st.markdown("---")

    st.subheader(
        "📈 Live Sensor Trends"
    )

    update_sensor_history(
        voltage,
        current,
        frequency,
        temperature
    )

    g1, g2 = st.columns(2)

    with g1:

        st.plotly_chart(
            create_live_graph(
                st.session_state[
                    "voltage_history"
                ],
                "Voltage Trend",
                "Voltage (V)"
            ),
            use_container_width=True
        )

    with g2:

        st.plotly_chart(
            create_live_graph(
                st.session_state[
                    "current_history"
                ],
                "Current Trend",
                "Current (A)"
            ),
            use_container_width=True
        )

    g3, g4 = st.columns(2)

    with g3:

        st.plotly_chart(
            create_live_graph(
                st.session_state[
                    "frequency_history"
                ],
                "Frequency Trend",
                "Frequency (Hz)"
            ),
            use_container_width=True
        )

    with g4:

        st.plotly_chart(
            create_live_graph(
                st.session_state[
                    "temperature_history"
                ],
                "Temperature Trend",
                "Temperature (°C)"
            ),
            use_container_width=True
        )

    # ========================================================
    # AI FAULT PREDICTION
    # ========================================================

    st.markdown("---")

    st.subheader(
        "🧠 Voltora Fault Detection"
    )

    # ========================================================
    # DEMO MODE
    # ========================================================

    if demo and demo_fault is not None:

        fault = demo_fault

        confidence = demo_confidence

        st.session_state[
            "fault"
        ] = fault

        st.session_state[
            "confidence"
        ] = confidence

        st.info(
            "🎬 Demo Mode: displaying the generated "
            "presentation scenario."
        )

    # ========================================================
    # REAL AI MODEL
    # ========================================================

    else:

        if model is None or encoder is None:

            st.error(
                "❌ AI prediction cannot run because "
                "the model or encoder could not be loaded."
            )

            st.stop()

        fault, confidence, new_data, prediction_error = (
            predict_fault(
                model,
                encoder,
                voltage,
                current,
                frequency,
                temperature
            )
        )

        if prediction_error is not None:

            st.error(
                "❌ AI prediction failed.\n\n"
                f"Error: `{prediction_error}`"
            )

            st.stop()

        st.session_state[
            "fault"
        ] = fault

        st.session_state[
            "confidence"
        ] = confidence

    # ========================================================
    # AI RESULT
    # ========================================================

    st.success(
        f"⚡ Detected Fault: {fault}"
    )

    st.info(
        f"🎯 Confidence: {confidence:.2f}%"
    )

    # ========================================================
    # ALARM
    # ========================================================

    handle_alarm(
        fault
    )

    # ========================================================
    # GRID HEALTH + PROTECTION
    # ========================================================

    health, shutdown = calculate_grid_health(
        fault
    )

    # ========================================================
    # SAVE HISTORY
    # ========================================================

    record_saved = save_history(
        area_id=area_id,
        line_id=line_id,
        asset_id=asset_id,
        voltage=voltage,
        current=current,
        frequency=frequency,
        temperature=temperature,
        fault=fault,
        confidence=confidence,
        health=health,
        shutdown=shutdown
    )

    if record_saved:

        st.success(
            "Prediction recorded in Voltora history."
        )

    # ========================================================
    # RESULT METRICS
    # ========================================================

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

    # ========================================================
    # EMERGENCY SHUTDOWN
    # ========================================================

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

    # ========================================================
    # SCADA SMART GRID
    # ========================================================

    st.markdown("---")

    st.subheader(
        "⚡ SCADA Smart Grid"
    )

    show_scada_grid(
        fault
    )

    # ========================================================
    # AI RECOMMENDATION
    # ========================================================

    show_ai_recommendation(
        fault
    )

    # ========================================================
    # PDF REPORT
    # ========================================================

    st.markdown("---")

    try:

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

        if pdf and os.path.exists(pdf):

            with open(
                pdf,
                "rb"
            ) as file:

                st.download_button(
                    label="📄 Download PDF Report",
                    data=file.read(),
                    file_name=Path(pdf).name,
                    mime="application/pdf",
                    use_container_width=True
                )

        else:

            st.warning(
                "PDF report could not be generated."
            )

    except Exception as error:

        st.warning(
            f"⚠️ PDF generation unavailable: {error}"
        )

    # ========================================================
    # SMART GRID VISUALIZATION
    # ========================================================

    st.markdown("---")

    show_grid_status(
        fault
    )


# ============================================================
# FAULT HISTORY PAGE
# ============================================================

elif menu == "📋 Fault History":

    st.title(
        "📋 Fault History"
    )

    initialize_history_file()

    try:

        history = pd.read_csv(
            HISTORY_FILE
        )

    except Exception as error:

        st.error(
            f"Unable to read history: {error}"
        )

        history = pd.DataFrame()

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
            "Voltora_History.csv",
            "text/csv"
        )


# ============================================================
# ANALYTICS PAGE
# ============================================================

elif menu == "📈 Analytics":

    st.title(
        "📈 Grid Analytics"
    )

    show_history_dashboard(
        str(HISTORY_FILE)
    )

    try:

        history = pd.read_csv(
            HISTORY_FILE
        )

    except Exception:

        history = pd.DataFrame()

    if history.empty:

        st.warning(
            "No data available."
        )

    else:

        # ----------------------------------------------------
        # VOLTAGE
        # ----------------------------------------------------

        st.subheader(
            "Voltage Trend"
        )

        if "Voltage" in history.columns:

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

        # ----------------------------------------------------
        # CURRENT
        # ----------------------------------------------------

        st.subheader(
            "Current Trend"
        )

        if "Current" in history.columns:

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

        # ----------------------------------------------------
        # TEMPERATURE
        # ----------------------------------------------------

        st.subheader(
            "Temperature Trend"
        )

        if "Temperature" in history.columns:

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

        # ----------------------------------------------------
        # FAULT DISTRIBUTION
        # ----------------------------------------------------

        st.subheader(
            "Fault Distribution"
        )

        if "Fault" in history.columns:

            fig4 = px.pie(
                history,
                names="Fault",
                title="Detected Faults"
            )

            st.plotly_chart(
                fig4,
                use_container_width=True
            )

        # ----------------------------------------------------
        # PROJECT STATISTICS
        # ----------------------------------------------------

        st.markdown("---")

        st.subheader(
            "📊 Project Statistics"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Predictions",
            len(history)
        )

        if "Fault" in history.columns:

            c2.metric(
                "Fault Types",
                history["Fault"].nunique()
            )

        else:

            c2.metric(
                "Fault Types",
                0
            )

        if "Grid Health" in history.columns:

            health_values = pd.to_numeric(
                history["Grid Health"],
                errors="coerce"
            )

            average_health = health_values.mean()

            if pd.isna(
                average_health
            ):

                average_health = 0

        else:

            average_health = 0

        c3.metric(
            "Average Grid Health",
            f"{average_health:.1f}%"
        )


# ============================================================
# REPORTS PAGE
# ============================================================

elif menu == "📄 Reports":

    st.title(
        "📄 Reports"
    )

    try:

        history = pd.read_csv(
            HISTORY_FILE
        )

    except Exception:

        history = pd.DataFrame()

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
            f"**Time:** {latest.get('Time', 'Unknown')}"
        )

        st.write(
            f"**Area ID:** "
            f"{latest.get('Area ID', 'Unknown')}"
        )

        st.write(
            f"**Line ID:** "
            f"{latest.get('Line ID', 'Unknown')}"
        )

        st.write(
            f"**Asset ID:** "
            f"{latest.get('Asset ID', 'Unknown')}"
        )

        st.write(
            f"**Voltage:** "
            f"{latest.get('Voltage', 'Unknown')} V"
        )

        st.write(
            f"**Current:** "
            f"{latest.get('Current', 'Unknown')} A"
        )

        st.write(
            f"**Frequency:** "
            f"{latest.get('Frequency', 'Unknown')} Hz"
        )

        st.write(
            f"**Temperature:** "
            f"{latest.get('Temperature', 'Unknown')} °C"
        )

        st.write(
            f"**Fault:** "
            f"{latest.get('Fault', 'Unknown')}"
        )

        st.write(
            f"**Confidence:** "
            f"{latest.get('Confidence', 'Unknown')} %"
        )

        st.write(
            f"**Grid Health:** "
            f"{latest.get('Grid Health', 'Unknown')} %"
        )

        st.write(
            f"**Shutdown:** "
            f"{latest.get('Shutdown', 'Unknown')}"
        )

        csv = history.to_csv(
            index=False
        ).encode(
            "utf-8"
        )

        st.download_button(
            "⬇ Download Complete Report",
            csv,
            "Voltora_Report.csv",
            "text/csv"
        )


# ============================================================
# LIVE MONITORING
# ============================================================

elif menu == "📊 Live Monitoring":

    st.title(
        "📊 Live Grid Monitoring"
    )

    try:

        history = pd.read_csv(
            HISTORY_FILE
        )

    except Exception:

        history = pd.DataFrame()

    if history.empty:

        st.warning(
            "No sensor data available."
        )

    else:

        latest = history.iloc[-1]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "🔌 Voltage",
            f"{latest.get('Voltage', 0)} V"
        )

        c2.metric(
            "⚡ Current",
            f"{latest.get('Current', 0)} A"
        )

        c3.metric(
            "🌡 Temperature",
            f"{latest.get('Temperature', 0)} °C"
        )

        c4.metric(
            "💚 Grid Health",
            f"{latest.get('Grid Health', 0)} %"
        )

        st.markdown("---")

        st.subheader(
            "Latest Fault"
        )

        if str(
            latest.get(
                "Shutdown",
                "NO"
            )
        ) == "YES":

            st.error(
                f"""
Fault : {latest.get('Fault', 'Unknown')}

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


# ============================================================
# ABOUT
# ============================================================

elif menu == "ℹ️ About":

    st.title(
        "ℹ️ About Voltora"
    )

    st.markdown(
        """
# ⚡ Voltora

Voltora is an Artificial Intelligence based Low Tension (LT)
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


# ============================================================
# TAMIL NADU GIS
# ============================================================

elif menu == "🗺️ Tamil Nadu GIS":

    st.title(
        "🗺️ Tamil Nadu GIS"
    )

    try:

        show_plotly_map()

    except Exception as error:

        st.error(
            f"Unable to load Tamil Nadu GIS map: {error}"
        )