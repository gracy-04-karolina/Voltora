"""
GridGuard AI - Virtual LT Circuit Simulator

Simplified educational LT feeder model:

Source
   ↓
LT Cable
   ↓
Connected Load
   ↓
Virtual Sensors
   ↓
GridGuard AI

The simulation is software-only. Electrical values are
calculated from the selected load and cable parameters.
"""

import math


# ==========================================================
# WIRE RESISTIVITY
# ==========================================================

# Ohm-mm²/m
WIRE_RESISTIVITY = {
    "Copper": 0.0175,
    "Aluminium": 0.0282,
}


# ==========================================================
# POWER FACTOR
# ==========================================================

DEFAULT_POWER_FACTOR = 0.90


# ==========================================================
# CABLE RESISTANCE
# ==========================================================

def calculate_line_resistance(material, length_m, area_mm2):
    """
    Calculate cable resistance.

    R = ρ × L / A

    ρ = material resistivity
    L = cable length
    A = conductor cross-sectional area
    """

    if material not in WIRE_RESISTIVITY:
        raise ValueError("Unsupported wire material")

    if length_m <= 0:
        raise ValueError(
            "Line length must be greater than 0"
        )

    if area_mm2 <= 0:
        raise ValueError(
            "Wire area must be greater than 0"
        )

    resistivity = WIRE_RESISTIVITY[material]

    resistance = (
        resistivity * length_m / area_mm2
    )

    return resistance


# ==========================================================
# CURRENT CALCULATION
# ==========================================================

def calculate_load_current(
    load_power_w,
    voltage,
    power_factor=DEFAULT_POWER_FACTOR
):
    """
    Calculate approximate load current.

    I = P / (V × PF)

    This simplified model treats the feeder as an
    equivalent 230 V LT load.
    """

    if voltage <= 0:
        return 0.0

    if power_factor <= 0:
        power_factor = DEFAULT_POWER_FACTOR

    current = (
        load_power_w /
        (voltage * power_factor)
    )

    return current


# ==========================================================
# CABLE HEATING
# ==========================================================

def calculate_temperature(
    base_temperature,
    current,
    resistance
):
    """
    Estimate conductor temperature from I²R heating.

    This is an educational thermal approximation,
    not a certified cable thermal model.
    """

    copper_loss = (
        current ** 2
        * resistance
    )

    # Small thermal conversion factor for the
    # software simulation.
    temperature_rise = copper_loss * 0.20

    # Prevent unrealistic temperature values
    temperature_rise = min(
        temperature_rise,
        70.0
    )

    return (
        base_temperature
        + temperature_rise
    )


# ==========================================================
# MAIN CIRCUIT SIMULATION
# ==========================================================

def simulate_circuit(
    source_voltage=230.0,
    frequency=50.0,
    material="Copper",
    length_m=100.0,
    area_mm2=16.0,
    load_power_w=1150.0,
    fault="Normal",
    temperature=30.0,
):
    """
    Simulate a simplified LT feeder.

    Returns:

        Voltage
        Current
        Frequency
        Temperature
        Line Resistance
        Voltage Drop
        Load Power
        Cable Loss
        Wire Material
        Line Length
        Wire Area
        Fault Condition
    """

    # ------------------------------------------------------
    # BASIC VALIDATION
    # ------------------------------------------------------

    source_voltage = float(source_voltage)
    load_power_w = float(load_power_w)
    temperature = float(temperature)

    if source_voltage <= 0:
        source_voltage = 230.0

    if load_power_w < 0:
        load_power_w = 0.0

    # ------------------------------------------------------
    # CABLE RESISTANCE
    # ------------------------------------------------------

    line_resistance = calculate_line_resistance(
        material,
        length_m,
        area_mm2
    )

    # ------------------------------------------------------
    # NORMAL CONDITION
    # ------------------------------------------------------

    if fault == "Normal":

        current = calculate_load_current(
            load_power_w,
            source_voltage
        )

        voltage_drop = (
            current * line_resistance
        )

        voltage = max(
            source_voltage - voltage_drop,
            0.0
        )

    # ------------------------------------------------------
    # OVERLOAD
    # ------------------------------------------------------

    elif fault == "Overload":

        # Increase actual electrical demand.
        overload_power = (
            load_power_w * 3.0
        )

        current = calculate_load_current(
            overload_power,
            source_voltage
        )

        voltage_drop = (
            current * line_resistance
        )

        voltage = max(
            source_voltage - voltage_drop,
            0.0
        )

        load_power_w = overload_power

    # ------------------------------------------------------
    # UNDERVOLTAGE
    # ------------------------------------------------------

    elif fault == "Undervoltage":

        # Reduced source voltage
        source_voltage_fault = (
            source_voltage * 0.85
        )

        current = calculate_load_current(
            load_power_w,
            source_voltage_fault
        )

        voltage_drop = (
            current * line_resistance
        )

        voltage = max(
            source_voltage_fault
            - voltage_drop,
            0.0
        )

    # ------------------------------------------------------
    # OVERVOLTAGE
    # ------------------------------------------------------

    elif fault == "Overvoltage":

        # Increased source voltage
        source_voltage_fault = (
            source_voltage * 1.20
        )

        current = calculate_load_current(
            load_power_w,
            source_voltage_fault
        )

        voltage_drop = (
            current * line_resistance
        )

        voltage = max(
            source_voltage_fault
            - voltage_drop,
            0.0
        )

    # ------------------------------------------------------
    # LINE BREAK
    # ------------------------------------------------------

    elif fault == "Line Break":

        # Open circuit
        voltage = 0.0
        current = 0.0
        voltage_drop = 0.0

    else:

        raise ValueError(
            f"Unknown fault condition: {fault}"
        )

    # ------------------------------------------------------
    # CABLE POWER LOSS
    # ------------------------------------------------------

    cable_loss = (
        current ** 2
        * line_resistance
    )

    # ------------------------------------------------------
    # TEMPERATURE
    # ------------------------------------------------------

    if fault == "Line Break":

        final_temperature = temperature

    else:

        final_temperature = calculate_temperature(
            temperature,
            current,
            line_resistance
        )

    # ------------------------------------------------------
    # RETURN SIMULATION
    # ------------------------------------------------------

    return {

        "Voltage": round(
            voltage,
            2
        ),

        "Current": round(
            current,
            2
        ),

        "Frequency": round(
            frequency,
            2
        ),

        "Temperature": round(
            final_temperature,
            2
        ),

        "Line Resistance": round(
            line_resistance,
            4
        ),

        "Voltage Drop": round(
            voltage_drop,
            2
        ),

        "Cable Loss": round(
            cable_loss,
            2
        ),

        "Load Power": round(
            load_power_w,
            2
        ),

        "Wire Material": material,

        "Line Length": round(
            length_m,
            2
        ),

        "Wire Area": round(
            area_mm2,
            2
        ),

        "Fault Condition": fault,
    }


# ==========================================================
# CIRCUIT STATUS
# ==========================================================

def get_circuit_status(simulation):
    """
    Return a readable virtual feeder status.
    """

    voltage = simulation["Voltage"]
    current = simulation["Current"]
    fault = simulation["Fault Condition"]

    if fault == "Line Break":

        return "🔴 LINE BROKEN"

    if fault == "Overload":

        return "🟠 OVERLOADED"

    if fault == "Undervoltage":

        return "🟡 LOW VOLTAGE"

    if fault == "Overvoltage":

        return "🟣 HIGH VOLTAGE"

    if voltage == 0 and current == 0:

        return "🔴 NO SUPPLY"

    return "🟢 LINE NORMAL"