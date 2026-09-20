"""Voltora - upgraded circuit diagram input + simulation module.

This module keeps the existing show_circuit_builder() entry point and includes:
- Grid Area / Line / Asset selection
- image upload and visual inspection
- Analyze Diagram button
- editable detected-component checklist
- Build Circuit button
- explicit Run Simulation / Pause / Reset Demo controls
- live metrics and live generation-vs-consumption chart
- Asset ID attached to the circuit and simulation
- latest virtual sensor values returned to the parent application
- automatic fault alarm sounds for injected circuit conditions

Important:
The uploaded image is treated as a visual reference. Without a dedicated
computer-vision model, the software does not claim perfect semantic circuit
recognition.

Virtual circuit values are simulated and are not measurements from physical
electrical hardware.
"""

import os
import time
import math
import random
from pathlib import Path
from datetime import datetime

import streamlit as st

try:
    from PIL import Image, ImageOps
except Exception:
    Image = None
    ImageOps = None


# ============================================================
# GRID ASSET MANAGEMENT
# ============================================================

from utils.asset_manager import (
    get_all_areas,
    get_area,
    get_asset,
)


# ============================================================
# PATHS
# ============================================================

# circuit_builder.py is inside:
# Voltora/utils/circuit_builder.py
#
# Therefore parent.parent points to:
# Voltora/
BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "assets"


# ============================================================
# ALARM FILES
# ============================================================

ALARM_FILES = {
    "Overload": "overload.mp3",
    "Overvoltage": "overvoltage.mp3",
    "Undervoltage": "undervoltage.mp3",
    "Line Break": "emergency.mp3",
}


# ============================================================
# FAULT NORMALIZATION
# ============================================================

def _normalize_fault(fault):
    """Convert simulation fault names to consistent display names."""

    if fault is None:
        return "Normal"

    fault = str(fault).strip().upper()

    mapping = {
        "NORMAL": "Normal",
        "OVERLOAD": "Overload",
        "OVERVOLTAGE": "Overvoltage",
        "UNDERVOLTAGE": "Undervoltage",
        "LINE BREAK": "Line Break",
        "LINE_BREAK": "Line Break",
    }

    return mapping.get(
        fault,
        str(fault).title(),
    )


# ============================================================
# GET ALARM FILE
# ============================================================

def _get_alarm_file(fault):
    """Return the alarm audio path for a circuit fault."""

    fault = _normalize_fault(fault)

    filename = ALARM_FILES.get(fault)

    if not filename:
        return None

    return ASSETS_DIR / filename


# ============================================================
# TRIGGER ALARM
# ============================================================

def _trigger_alarm(fault):
    """
    Trigger the appropriate alarm when the circuit changes into
    a fault condition.

    The alarm is triggered only when the fault changes. This prevents
    the sound from replaying every time Streamlit reruns the app.
    """

    fault = _normalize_fault(fault)

    previous_fault = _normalize_fault(
        st.session_state.get(
            "circuit_previous_fault",
            "Normal",
        )
    )

    # --------------------------------------------------------
    # NORMAL CONDITION
    # --------------------------------------------------------

    if fault == "Normal":

        st.session_state.circuit_alarm_triggered = False

        st.session_state.circuit_previous_fault = "Normal"

        return

    # --------------------------------------------------------
    # NEW FAULT EVENT
    # --------------------------------------------------------

    new_fault_event = (
        fault != previous_fault
    )

    alarm_file = _get_alarm_file(
        fault
    )

    if new_fault_event:

        st.session_state.circuit_alarm_triggered = True

        # ----------------------------------------------------
        # FILE EXISTS
        # ----------------------------------------------------

        if alarm_file and alarm_file.exists():

            try:

                with open(
                    alarm_file,
                    "rb",
                ) as audio_file:

                    audio_bytes = audio_file.read()

                st.audio(
                    audio_bytes,
                    format="audio/mp3",
                    autoplay=True,
                )

                st.warning(
                    f"🔊 **{fault} alarm activated**"
                )

            except Exception as exc:

                st.error(
                    f"⚠️ Could not play {fault} alarm: {exc}"
                )

        # ----------------------------------------------------
        # FILE DOES NOT EXIST
        # ----------------------------------------------------

        else:

            expected_file = (
                str(alarm_file)
                if alarm_file
                else "Unknown"
            )

            st.error(
                f"🔊 Alarm file not found for "
                f"**{fault}**.\n\n"
                f"Expected:\n`{expected_file}`"
            )

    # --------------------------------------------------------
    # SAVE CURRENT FAULT
    # --------------------------------------------------------

    st.session_state.circuit_previous_fault = fault


# ============================================================
# RESET ALARM STATE
# ============================================================

def _reset_alarm_state():

    st.session_state.circuit_previous_fault = "Normal"

    st.session_state.circuit_alarm_triggered = False


# ============================================================
# UI HELPER
# ============================================================

def _box(
    title,
    body,
    border="#64748b",
):

    return (
        '<div style="padding:14px 12px;border-radius:14px;border:2px solid '
        f'{border};background:#0b1220;text-align:center;min-width:135px;'
        'line-height:1.45;box-sizing:border-box;">'
        f'{title}<br>{body}</div>'
    )


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def _analyze_image(uploaded):
    """Perform safe local image analysis."""

    if Image is None:

        return {
            "status": "Pillow is not installed",
            "width": 0,
            "height": 0,
            "mode": "-",
            "aspect": 0,
            "orientation": "-",
            "contrast": 0,
            "complexity": "-",
        }

    img = Image.open(
        uploaded
    ).convert(
        "RGB"
    )

    width, height = img.size

    aspect = width / max(
        height,
        1,
    )

    gray = ImageOps.grayscale(
        img
    )

    small = gray.copy()

    small.thumbnail(
        (
            900,
            900,
        )
    )

    px = list(
        small.getdata()
    )

    if px:

        mean = sum(px) / len(px)

        variance = sum(
            (
                p - mean
            ) ** 2
            for p in px
        ) / len(px)

        contrast = math.sqrt(
            variance
        )

    else:

        mean = 0
        contrast = 0

    orientation = (
        "Landscape"
        if aspect >= 1.25
        else "Portrait"
        if aspect <= 0.8
        else "Square / near-square"
    )

    complexity = (
        "High"
        if contrast > 65
        else "Medium"
        if contrast > 35
        else "Low"
    )

    return {
        "status": "Image loaded successfully",
        "width": width,
        "height": height,
        "mode": "RGB",
        "aspect": aspect,
        "orientation": orientation,
        "contrast": contrast,
        "complexity": complexity,
    }


# ============================================================
# DEFAULT COMPONENTS
# ============================================================

def _default_components():

    return {
        "Transformer": True,
        "3-Phase / AC Supply": True,
        "Neutral / Ground": True,
        "Feeder / Transmission Lines": True,
        "Protection / Breaker": True,
        "Loads / Consumers": True,
        "Sensors": True,
        "Relay / Trip": True,
    }


# ============================================================
# SIMULATION RESET
# ============================================================

def _reset_simulation():

    st.session_state.sim_history = []

    st.session_state.sim_running = False

    st.session_state.sim_tick = 0

    st.session_state.latest_simulation = None

    # Reset alarm state as well
    _reset_alarm_state()


# ============================================================
# SIMULATION SAMPLE GENERATOR
# ============================================================

def _make_sample(
    condition,
    total_load,
    phase_voltage,
    frequency,
    transformer_rating,
):
    """Generate representative demo values."""

    tick = st.session_state.get(
        "sim_tick",
        0,
    )

    wave = math.sin(
        tick / 3.5
    )

    noise = random.uniform(
        -0.025,
        0.025,
    )

    solar_factor = (
        1.0
        + 0.10 * wave
        + noise
    )

    base_generation = (
        10.8
        * solar_factor
    )

    base_generation = max(
        0.5,
        base_generation,
    )

    voltage = (
        phase_voltage
        + random.uniform(
            -1.5,
            1.5,
        )
    )

    current = max(
        0.5,
        (
            total_load
            / max(
                phase_voltage,
                1,
            )
        )
        * (
            1
            + 0.08 * wave
        ),
    )

    freq = (
        frequency
        + random.uniform(
            -0.06,
            0.06,
        )
    )

    temperature = (
        31.0
        + (
            current
            * 0.75
        )
        + random.uniform(
            -0.8,
            0.8,
        )
    )

    # ========================================================
    # FAULT CONDITIONS
    # ========================================================

    if condition == "Overload":

        current *= 1.75

        temperature += 18

        generation = (
            base_generation
            * 0.88
        )

        consumption = (
            total_load
            / 1000
            * 1.35
        )

        fault = "OVERLOAD"

    elif condition == "Overvoltage":

        voltage += 24

        generation = (
            base_generation
            * 1.05
        )

        consumption = (
            total_load
            / 1000
        )

        fault = "OVERVOLTAGE"

    elif condition == "Undervoltage":

        voltage -= 30

        generation = (
            base_generation
            * 0.75
        )

        consumption = (
            total_load
            / 1000
            * 0.92
        )

        fault = "UNDERVOLTAGE"

    elif condition == "Line Break":

        voltage = 0.0

        current = 0.0

        generation = 0.0

        consumption = 0.0

        temperature = (
            28.0
            + random.uniform(
                -0.5,
                0.5,
            )
        )

        fault = "LINE BREAK"

    else:

        generation = base_generation

        consumption = (
            total_load
            / 1000
        )

        fault = "NORMAL"

    # ========================================================
    # DEMO GRID HEALTH
    # ========================================================

    health = 96.0

    if fault != "NORMAL":

        health -= {
            "OVERLOAD": 30,
            "OVERVOLTAGE": 25,
            "UNDERVOLTAGE": 22,
            "LINE BREAK": 35,
        }[fault]

    health -= min(
        18,
        max(
            0,
            consumption - generation,
        )
        * 1.2,
    )

    health = max(
        0.0,
        min(
            100.0,
            health,
        ),
    )

    return {

        "time": datetime.now().strftime(
            "%H:%M:%S"
        ),

        "voltage": voltage,

        "current": current,

        "frequency": freq,

        "temperature": temperature,

        "generation": generation,

        "consumption": consumption,

        "health": health,

        "fault": fault,

        "transformer": transformer_rating,
    }


# ============================================================
# RUN ONE SIMULATION STEP
# ============================================================

def _run_simulation_step(
    condition,
    total_load,
    phase_voltage,
    frequency,
    transformer_rating,
):

    sample = _make_sample(
        condition,
        total_load,
        phase_voltage,
        frequency,
        transformer_rating,
    )

    history = st.session_state.setdefault(
        "sim_history",
        [],
    )

    history.append(
        sample
    )

    st.session_state.sim_history = (
        history[-30:]
    )

    st.session_state.sim_tick = (
        st.session_state.get(
            "sim_tick",
            0,
        )
        + 1
    )

    st.session_state.latest_simulation = (
        sample
    )

    # ========================================================
    # 🔊 TRIGGER CIRCUIT ALARM
    # ========================================================

    _trigger_alarm(
        sample["fault"]
    )

    return sample


# ============================================================
# MAIN CIRCUIT BUILDER
# ============================================================

def show_circuit_builder():

    # ========================================================
    # TITLE
    # ========================================================

    st.markdown(
        "## ⚡ 3-Phase LT Virtual Circuit Builder"
    )

    st.info(
        "Software-only Voltora AI demo. Upload a circuit diagram, "
        "inspect the detected visual structure, build the editable "
        "virtual circuit, then press Run Simulation. Values are "
        "simulated; no physical hardware is connected."
    )

    # ========================================================
    # GRID ASSET SELECTION
    # ========================================================

    st.markdown(
        "### 📍 0. Grid Asset Selection"
    )

    areas = get_all_areas()

    if not areas:

        st.error(
            "No grid assets found. Check data/grid_assets.csv."
        )

        return {}

    selected_area = st.selectbox(
        "Select Area",
        areas,
        key="circuit_area_select",
    )

    area_assets = get_area(
        selected_area
    )

    if area_assets.empty:

        st.warning(
            "No lines are available for this area."
        )

        return {}

    selected_line = st.selectbox(
        "Select Line",
        area_assets["line_id"].tolist(),
        key="circuit_line_select",
    )

    selected_asset_id = area_assets.loc[
        area_assets["line_id"]
        == selected_line,
        "asset_id",
    ].iloc[0]

    selected_asset = get_asset(
        selected_asset_id
    )

    if selected_asset:

        a1, a2, a3, a4 = st.columns(4)

        with a1:

            st.metric(
                "Asset ID",
                selected_asset["asset_id"],
            )

        with a2:

            st.metric(
                "Line ID",
                selected_asset["line_id"],
            )

        with a3:

            st.metric(
                "Area",
                selected_asset["area_name"],
            )

        with a4:

            st.metric(
                "Status",
                selected_asset["status"],
            )

        st.caption(
            f"📍 Location: "
            f"{selected_asset['latitude']:.4f}, "
            f"{selected_asset['longitude']:.4f}"
        )

    # ========================================================
    # IMAGE INPUT
    # ========================================================

    st.markdown(
        "### 🖼️ 1. Circuit Diagram Input"
    )

    st.caption(
        "Upload PNG/JPG/JPEG. The image is used as the visual "
        "reference. The local analyzer checks image structure; "
        "component detection is presented as editable suggestions "
        "rather than guaranteed symbol recognition."
    )

    uploaded = st.file_uploader(
        "Upload Circuit Diagram (PNG / JPG / JPEG)",
        type=[
            "png",
            "jpg",
            "jpeg",
        ],
        key="lt_reference_upload_v2",
    )

    if uploaded is not None:

        st.image(
            uploaded,
            caption="Uploaded Circuit Diagram",
            use_container_width=True,
        )

        if st.button(
            "🔍 Analyze Diagram",
            type="primary",
            use_container_width=True,
        ):

            try:

                st.session_state.diagram_analysis = (
                    _analyze_image(
                        uploaded
                    )
                )

                st.session_state.detected_components = (
                    _default_components()
                )

                st.session_state.analysis_done = True

            except Exception as exc:

                st.error(
                    f"Could not analyze this image: {exc}"
                )

        if st.session_state.get(
            "analysis_done"
        ):

            info = (
                st.session_state.diagram_analysis
            )

            st.success(
                "Diagram analyzed. Review the suggested "
                "circuit elements below before building."
            )

            a1, a2, a3, a4 = st.columns(4)

            a1.metric(
                "Image",
                f"{info['width']} × {info['height']}",
            )

            a2.metric(
                "Orientation",
                info["orientation"],
            )

            a3.metric(
                "Visual complexity",
                info["complexity"],
            )

            a4.metric(
                "Aspect ratio",
                f"{info['aspect']:.2f}",
            )

            st.markdown(
                "#### 🧩 Suggested Circuit Elements — edit before building"
            )

            comps = st.session_state.setdefault(
                "detected_components",
                _default_components(),
            )

            cols = st.columns(4)

            for idx, name in enumerate(
                comps
            ):

                with cols[
                    idx % 4
                ]:

                    comps[name] = st.checkbox(
                        name,
                        value=comps[name],
                        key=f"det_{idx}_{name}",
                    )

            st.session_state.detected_components = (
                comps
            )

    elif os.path.exists(
        BASE_DIR
        / "assets"
        / "lt_3phase_reference.png"
    ):

        st.image(
            BASE_DIR
            / "assets"
            / "lt_3phase_reference.png",
            caption="Default LT Reference Diagram",
            use_container_width=True,
        )

    # ========================================================
    # BUILDER SETTINGS
    # ========================================================

    st.markdown(
        "### ⚙️ 2. Circuit Configuration"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        incoming_kv = st.number_input(
            "⚡ Incoming Supply (kV)",
            1.0,
            33.0,
            11.0,
            0.5,
        )

    with c2:

        phase_voltage = st.number_input(
            "🔌 Phase Voltage (V)",
            180.0,
            260.0,
            230.0,
            1.0,
        )

    with c3:

        frequency = st.number_input(
            "📡 Frequency (Hz)",
            45.0,
            55.0,
            50.0,
            0.5,
        )

    with c4:

        transformer_rating = st.selectbox(
            "🔻 Transformer",
            [
                "25 kVA",
                "63 kVA",
                "100 kVA",
                "160 kVA",
                "250 kVA",
            ],
            index=1,
        )

    f1, f2, f3 = st.columns(3)

    with f1:

        cable_length = st.slider(
            "📏 Feeder Length (m)",
            100,
            2000,
            1000,
            100,
        )

    with f2:

        cable_material = st.selectbox(
            "🧵 Conductor",
            [
                "Aluminium",
                "Copper",
            ],
            index=0,
        )

    with f3:

        cable_size = st.selectbox(
            "📐 Conductor Size (mm²)",
            [
                16,
                25,
                35,
                50,
                70,
                95,
            ],
            index=2,
        )

    # ========================================================
    # CONNECTED CONSUMERS
    # ========================================================

    st.markdown(
        "### 🏠 Connected Consumers"
    )

    l1, l2, l3, l4 = st.columns(4)

    with l1:

        residential_1 = st.checkbox(
            "🏠 Consumer 1 — 3 kW",
            True,
        )

    with l2:

        commercial = st.checkbox(
            "🏢 Consumer 2 — 5 kW",
            True,
        )

    with l3:

        industrial = st.checkbox(
            "🏭 Consumer 3 — 10 kW",
            True,
        )

    with l4:

        residential_2 = st.checkbox(
            "🏠 Consumer 4 — 3 kW",
            True,
        )

    total_load = (
        (3000 if residential_1 else 0)
        + (5000 if commercial else 0)
        + (10000 if industrial else 0)
        + (3000 if residential_2 else 0)
    )

    if total_load == 0:

        total_load = 1000

    st.caption(
        f"Configured consumer load: "
        f"**{total_load / 1000:.1f} kW**"
    )

    # ========================================================
    # SENSOR LAYER
    # ========================================================

    st.markdown(
        "### 📡 Virtual Sensor Layer"
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:

        voltage_sensor = st.checkbox(
            "Voltage Sensor",
            True,
        )

    with s2:

        current_sensor = st.checkbox(
            "Current Sensor",
            True,
        )

    with s3:

        frequency_sensor = st.checkbox(
            "Frequency Sensor",
            True,
        )

    with s4:

        temperature_sensor = st.checkbox(
            "Temperature Sensor",
            True,
        )

    # ========================================================
    # PROTECTION & FAULT INJECTION
    # ========================================================

    st.markdown(
        "### 🛡️ 3. Protection & Fault Injection"
    )

    p1, p2 = st.columns(2)

    with p1:

        mcb_enabled = st.checkbox(
            "🛡️ MCB / Consumer Protection",
            True,
        )

        relay_enabled = st.checkbox(
            "🔄 Virtual Relay",
            True,
        )

    with p2:

        circuit_condition = st.selectbox(
            "💥 Simulated Circuit Condition",
            [
                "Normal",
                "Overload",
                "Overvoltage",
                "Undervoltage",
                "Line Break",
            ],
            index=0,
        )

    # ========================================================
    # BUILD CIRCUIT
    # ========================================================

    st.markdown(
        "### 🔧 4. Build Circuit"
    )

    if "circuit_built" not in st.session_state:

        st.session_state.circuit_built = False

    b1, b2 = st.columns(
        [2, 1]
    )

    with b1:

        if st.button(
            "🔧 Build Circuit",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.circuit_built = True

            _reset_simulation()

            # Set initial fault state according to the
            # currently selected condition.
            #
            # This is intentionally Normal so the first
            # simulation of a fault generates an alarm.
            _reset_alarm_state()

            st.success(
                f"Circuit built successfully for "
                f"{selected_line} / {selected_asset_id}."
            )

    with b2:

        if st.button(
            "↻ Reset Demo",
            use_container_width=True,
        ):

            st.session_state.circuit_built = False

            st.session_state.analysis_done = False

            _reset_simulation()

            st.rerun()

    # ========================================================
    # CIRCUIT VISUAL
    # ========================================================

    if st.session_state.circuit_built:

        st.markdown(
            "### 🔌 Built Virtual Circuit"
        )

        fault_border = {
            "Normal": "#22c55e",
            "Overload": "#f59e0b",
            "Overvoltage": "#a78bfa",
            "Undervoltage": "#eab308",
            "Line Break": "#ef4444",
        }[
            circuit_condition
        ]

        st.info(
            f"📍 **Area:** {selected_area}  |  "
            f"**Line:** {selected_line}  |  "
            f"**Asset:** {selected_asset_id}"
        )

        # ----------------------------------------------------
        # SUPPLY
        # ----------------------------------------------------

        st.markdown(
            """
            <div style="
                text-align:center;
                padding:12px;
                border:2px solid #64748b;
                border-radius:14px;
                background:#0b1220;
                margin:8px auto;
                max-width:300px;
            ">
                ⚡ <b>SUPPLY</b><br>
                Incoming LT Distribution Supply
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='text-align:center;font-size:25px;'>▼</div>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # TRANSFORMER
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div style="
                text-align:center;
                padding:14px;
                border:2px solid #64748b;
                border-radius:14px;
                background:#0b1220;
                margin:8px auto;
                max-width:320px;
            ">
                🔻 <b>TRANSFORMER</b><br>
                {incoming_kv:.1f} kV → 0.415 kV<br>
                {transformer_rating}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='text-align:center;font-size:25px;'>▼</div>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # LT FEEDER
        # ----------------------------------------------------

        feeder_html = f"""
<div style="
    text-align:center;
    padding:16px;
    border:2px solid #38bdf8;
    border-radius:14px;
    background:#0b1220;
    margin:8px auto;
    max-width:650px;
">

<div style="
    font-size:18px;
    font-weight:bold;
    margin-bottom:14px;
">
⚡ 3-PHASE LT FEEDER
</div>

<div style="
    color:#f87171;
    font-size:20px;
    font-weight:bold;
">
━━━━━━━━━━━━━━━━ R
</div>

<div style="
    color:#f59e0b;
    font-size:20px;
    font-weight:bold;
">
━━━━━━━━━━━━━━━━ Y
</div>

<div style="
    color:#60a5fa;
    font-size:20px;
    font-weight:bold;
">
━━━━━━━━━━━━━━━━ B
</div>

<div style="
    color:#e5e7eb;
    font-size:20px;
    font-weight:bold;
">
━━━━━━━━━━━━━━━━ N
</div>

<div style="
    margin-top:12px;
    color:#94a3b8;
    font-size:13px;
">
{cable_length} m
&nbsp; | &nbsp;
{cable_material}
&nbsp; | &nbsp;
{cable_size} mm²
</div>

</div>
"""

        st.markdown(
            feeder_html,
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # CONSUMERS
        # ----------------------------------------------------

        st.markdown(
            "#### 🏠 Connected Consumers"
        )

        consumer_cols = st.columns(4)

        consumers = [
            (
                "🏠",
                "CONSUMER 1",
                "Residential",
                "3 kW",
                residential_1,
            ),
            (
                "🏢",
                "CONSUMER 2",
                "Commercial",
                "5 kW",
                commercial,
            ),
            (
                "🏭",
                "CONSUMER 3",
                "Industrial",
                "10 kW",
                industrial,
            ),
            (
                "🏠",
                "CONSUMER 4",
                "Residential",
                "3 kW",
                residential_2,
            ),
        ]

        for col, consumer in zip(
            consumer_cols,
            consumers,
        ):

            icon, name, category, power, enabled = consumer

            with col:

                st.markdown(
                    f"""
                    <div style="
                        padding:14px 10px;
                        border-radius:14px;
                        border:2px solid #64748b;
                        background:#0b1220;
                        text-align:center;
                        min-height:105px;
                        line-height:1.45;
                        box-sizing:border-box;
                    ">
                        {icon}<br>
                        <b>{name}</b><br>
                        {category}<br>
                        {
                            "<b>" + power + "</b>"
                            if enabled
                            else "Disconnected"
                        }
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<div style='text-align:center;font-size:25px;margin:10px;'>▼</div>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # SENSOR LAYER
        # ----------------------------------------------------

        sensor_cols = st.columns(4)

        sensors_data = [
            (
                "⚡",
                "VOLTAGE",
                voltage_sensor,
            ),
            (
                "🔌",
                "CURRENT",
                current_sensor,
            ),
            (
                "〰️",
                "FREQUENCY",
                frequency_sensor,
            ),
            (
                "🌡️",
                "TEMPERATURE",
                temperature_sensor,
            ),
        ]

        for col, sensor in zip(
            sensor_cols,
            sensors_data,
        ):

            icon, name, enabled = sensor

            with col:

                st.markdown(
                    f"""
                    <div style="
                        padding:14px 8px;
                        border-radius:14px;
                        border:2px solid #38bdf8;
                        background:#0b1220;
                        text-align:center;
                        min-height:85px;
                        box-sizing:border-box;
                    ">
                        {icon}<br>
                        <b>{name}</b><br>
                        {"ACTIVE" if enabled else "DISABLED"}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<div style='text-align:center;font-size:25px;margin:10px;'>▼</div>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # AI
        # ----------------------------------------------------

        st.markdown(
            """
            <div style="
                text-align:center;
                padding:15px;
                border:2px solid #a78bfa;
                border-radius:14px;
                background:#0b1220;
                margin:8px auto;
                max-width:320px;
            ">
                🧠 <b> VOLTORA </b><br>
                Fault Detection
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='text-align:center;font-size:25px;'>▼</div>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # RELAY
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div style="
                text-align:center;
                padding:15px;
                border:2px solid {fault_border};
                border-radius:14px;
                background:#0b1220;
                margin:8px auto;
                max-width:320px;
            ">
                🔄 <b>VIRTUAL RELAY</b><br>
                {"ENABLED" if relay_enabled else "DISABLED"}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='text-align:center;font-size:25px;'>▼</div>",
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # PROTECTION STATE
        # ----------------------------------------------------

        if circuit_condition == "Normal":

            protection_text = (
                "🟢 LOAD REMAINS ENERGIZED"
            )

        else:

            protection_text = (
                "🚨 PROTECTION RESPONSE ACTIVE"
            )

        st.markdown(
            f"""
            <div style="
                text-align:center;
                padding:18px;
                border:2px solid {fault_border};
                border-radius:14px;
                background:#111827;
                margin:10px auto;
                max-width:500px;
            ">
                <b>{protection_text}</b><br>
                <small>
                    Demo condition: {circuit_condition}
                </small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ====================================================
        # ALARM STATUS PANEL
        # ====================================================

        current_alarm_fault = _normalize_fault(
            circuit_condition
        )

        if current_alarm_fault == "Normal":

            st.success(
                "🔇 Alarm system: STANDBY — circuit is normal."
            )

        else:

            alarm_file = _get_alarm_file(
                current_alarm_fault
            )

            if (
                alarm_file
                and alarm_file.exists()
            ):

                st.error(
                    f"🚨 Alarm system: **{current_alarm_fault.upper()}** "
                    f"alarm armed"
                )

            else:

                st.warning(
                    f"⚠️ Alarm system: {current_alarm_fault} "
                    f"sound file is missing."
                )

        # ====================================================
        # SIMULATION CONTROLS
        # ====================================================

        st.markdown(
            "### ▶ 5. Run Simulation"
        )

        r1, r2, r3 = st.columns(
            [2, 1, 1]
        )

        with r1:

            if st.button(
                "▶ Run Simulation",
                type="primary",
                use_container_width=True,
            ):

                st.session_state.sim_running = True

                _run_simulation_step(
                    circuit_condition,
                    total_load,
                    phase_voltage,
                    frequency,
                    transformer_rating,
                )

        with r2:

            if st.button(
                "⏸ Pause",
                use_container_width=True,
            ):

                st.session_state.sim_running = False

        with r3:

            if st.button(
                "↻ Reset Simulation",
                use_container_width=True,
            ):

                _reset_simulation()

                st.rerun()

        # ====================================================
        # LIVE SIMULATION
        # ====================================================

        if st.session_state.get(
            "sim_running"
        ):

            sample = _run_simulation_step(
                circuit_condition,
                total_load,
                phase_voltage,
                frequency,
                transformer_rating,
            )

        elif st.session_state.get(
            "sim_history"
        ):

            sample = (
                st.session_state.sim_history[-1]
            )

        else:

            sample = None

        # ====================================================
        # DISPLAY LIVE VALUES
        # ====================================================

        if sample:

            if st.session_state.get(
                "sim_running"
            ):

                st.success(
                    f"Simulation running in DEMO mode • "
                    f"Asset: {selected_asset_id} • "
                    f"Line: {selected_line} • "
                    f"Last update: {sample['time']}"
                )

            else:

                st.info(
                    f"Simulation paused • "
                    f"Asset: {selected_asset_id} • "
                    f"Line: {selected_line} • "
                    f"Last update: {sample['time']}"
                )

            m1, m2, m3, m4, m5 = st.columns(5)

            m1.metric(
                "Voltage",
                f"{sample['voltage']:.1f} V",
            )

            m2.metric(
                "Current",
                f"{sample['current']:.1f} A",
            )

            m3.metric(
                "Frequency",
                f"{sample['frequency']:.2f} Hz",
            )

            m4.metric(
                "Temperature",
                f"{sample['temperature']:.1f} °C",
            )

            m5.metric(
                "Grid Health",
                f"{sample['health']:.0f}%",
            )

            # ------------------------------------------------
            # SIMULATION FAULT STATUS
            # ------------------------------------------------

            if sample["fault"] == "NORMAL":

                st.success(
                    "🟢 Simulation status: NORMAL — "
                    "relay remains energized."
                )

            else:

                fault_name = _normalize_fault(
                    sample["fault"]
                )

                st.error(
                    f"🚨 Simulation condition: "
                    f"{fault_name.upper()} — "
                    f"protection response active for "
                    f"{selected_line}."
                )

                # ------------------------------------------------
                # ALARM INFORMATION
                # ------------------------------------------------

                alarm_file = _get_alarm_file(
                    fault_name
                )

                if alarm_file and alarm_file.exists():

                    st.warning(
                        f"🔊 **{fault_name} alarm active**"
                    )

            # =================================================
            # LIVE CHART
            # =================================================

            st.markdown(
                "#### 📈 Live Generation vs Consumption"
            )

            history = (
                st.session_state.sim_history
            )

            chart_data = {
                "Generation (kW)": [
                    x["generation"]
                    for x in history
                ],
                "Consumption (kW)": [
                    x["consumption"]
                    for x in history
                ],
            }

            st.line_chart(
                chart_data,
                height=320,
                use_container_width=True,
            )

            # =================================================
            # AUTOMATIC REFRESH
            # =================================================

            if st.session_state.get(
                "sim_running"
            ):

                time.sleep(
                    1.5
                )

                st.rerun()

        else:

            st.info(
                "Press **▶ Run Simulation** to start "
                "the live demo values and graph."
            )

    # ========================================================
    # INFORMATION
    # ========================================================

    with st.expander(
        "ℹ️ How this connects to Voltora"
    ):

        st.write(
            "The selected Area, Line ID and Asset ID identify "
            "the exact electrical section represented by this "
            "virtual circuit. The uploaded diagram is the visual "
            "reference. The virtual circuit is built from the "
            "editable configuration, and the Run Simulation "
            "button generates representative voltage, current, "
            "frequency and temperature values."
        )

        st.write(
            "These virtual sensor values can be passed to the "
            "existing fault_model.pkl in the parent application. "
            "The displayed circuit condition is currently a "
            "demo injection control and is not itself claimed "
            "to be an AI prediction."
        )

        st.write(
            "The circuit protection alarm is triggered directly "
            "from the simulated circuit condition. This keeps "
            "the protection alarm independent from the AI model "
            "prediction."
        )

    # ========================================================
    # RETURN DATA TO PARENT APP
    # ========================================================

    monitored_load_power = (
        3450.0
        if circuit_condition == "Overload"
        else 1150.0
    )

    # --------------------------------------------------------
    # Latest simulation values
    # --------------------------------------------------------

    latest = st.session_state.get(
        "latest_simulation"
    )

    return {

        # ====================================================
        # GRID ASSET IDENTIFICATION
        # ====================================================

        "area_id": selected_area,

        "line_id": selected_line,

        "asset_id": selected_asset_id,

        "asset_status": (
            selected_asset["status"]
            if selected_asset
            else "Unknown"
        ),

        "asset_latitude": (
            selected_asset["latitude"]
            if selected_asset
            else None
        ),

        "asset_longitude": (
            selected_asset["longitude"]
            if selected_asset
            else None
        ),

        # ====================================================
        # CIRCUIT CONFIGURATION
        # ====================================================

        "incoming_kv": incoming_kv,

        "phase_voltage": phase_voltage,

        "frequency": frequency,

        "transformer_rating": transformer_rating,

        "cable_length": cable_length,

        "cable_material": cable_material,

        "cable_size": cable_size,

        # ====================================================
        # LOADS
        # ====================================================

        "residential_1": residential_1,

        "commercial": commercial,

        "industrial": industrial,

        "residential_2": residential_2,

        "total_load": total_load,

        # ====================================================
        # SENSORS
        # ====================================================

        "voltage_sensor": voltage_sensor,

        "current_sensor": current_sensor,

        "frequency_sensor": frequency_sensor,

        "temperature_sensor": temperature_sensor,

        # ====================================================
        # PROTECTION
        # ====================================================

        "mcb_enabled": mcb_enabled,

        "relay_enabled": relay_enabled,

        # ====================================================
        # FAULT CONDITION
        # ====================================================

        "circuit_condition": circuit_condition,

        "monitored_load_power": monitored_load_power,

        # ====================================================
        # ALARM STATE
        # ====================================================

        "alarm_triggered": (
            st.session_state.get(
                "circuit_alarm_triggered",
                False,
            )
        ),

        "alarm_fault": (
            _normalize_fault(
                st.session_state.get(
                    "circuit_previous_fault",
                    "Normal",
                )
            )
        ),

        # ====================================================
        # IMAGE / CIRCUIT STATE
        # ====================================================

        "diagram_analyzed": (
            st.session_state.get(
                "analysis_done",
                False,
            )
        ),

        "circuit_built": (
            st.session_state.get(
                "circuit_built",
                False,
            )
        ),

        "simulation_running": (
            st.session_state.get(
                "sim_running",
                False,
            )
        ),

        # ====================================================
        # LATEST VIRTUAL SENSOR VALUES
        # ====================================================

        "simulation_available": (
            latest is not None
        ),

        "voltage": (
            latest["voltage"]
            if latest
            else None
        ),

        "current": (
            latest["current"]
            if latest
            else None
        ),

        "sim_frequency": (
            latest["frequency"]
            if latest
            else None
        ),

        "temperature": (
            latest["temperature"]
            if latest
            else None
        ),

        "simulation_grid_health": (
            latest["health"]
            if latest
            else None
        ),

        "simulation_fault": (
            latest["fault"]
            if latest
            else None
        ),

        "simulation_time": (
            latest["time"]
            if latest
            else None
        ),
    }