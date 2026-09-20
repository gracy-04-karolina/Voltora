import streamlit as st
import base64
import time


def cinematic_startup():

    with open("assets/logo.png", "rb") as f:
        logo = base64.b64encode(f.read()).decode()

    screen = st.empty()

    css = """
    <style>

    .boot{
        background:linear-gradient(180deg,#020612,#071b38);
        border:1px solid #00d4ff55;
        border-radius:20px;
        padding:35px;
        text-align:center;
        box-shadow:0 0 40px rgba(0,212,255,.4);
    }

    @keyframes rotate{
        from{transform:rotate(0deg);}
        to{transform:rotate(360deg);}
    }

    @keyframes pulse{
        0%{
            transform:scale(1);
            filter:drop-shadow(0 0 15px cyan);
        }

        50%{
            transform:scale(1.08);
            filter:drop-shadow(0 0 35px cyan);
        }

        100%{
            transform:scale(1);
            filter:drop-shadow(0 0 15px cyan);
        }
    }

    .ring{

        width:220px;
        height:220px;
        margin:auto;

        border-radius:50%;
        border:3px solid #00d4ff55;

        animation:rotate 8s linear infinite;

        display:flex;
        justify-content:center;
        align-items:center;

    }

    .ring2{

        width:180px;
        height:180px;

        border-radius:50%;
        border:2px dashed cyan;

        display:flex;
        justify-content:center;
        align-items:center;

    }

    .logo{

        width:110px;
        animation:pulse 2s infinite;

    }

    .title{

        font-size:46px;
        color:#00d4ff;
        font-weight:bold;
        margin-top:20px;

    }

    .sub{

        color:white;
        font-size:20px;
        margin-top:8px;

    }

    .terminal{

        background:#10141f;
        color:#8fff8f;

        text-align:left;

        padding:15px;

        border-radius:12px;

        font-family:monospace;

        margin-top:25px;

        white-space:pre-wrap;

        height:240px;

        overflow:hidden;

    }

    .percent{

        text-align:center;

        color:#00d4ff;

        font-size:26px;

        font-weight:bold;

        margin-top:15px;

    }

    progress{

        width:100%;
        height:20px;

    }

    </style>
    """

    boot = [

        "Initializing AI Core...",
        "Loading Fault Detection Model...",
        "Loading Machine Learning Engine...",
        "Connecting SCADA Sensors...",
        "Connecting GIS Intelligence...",
        "Synchronizing Disaster Database...",
        "Loading Weather API...",
        "Initializing Analytics Engine...",
        "Loading Event Logger...",
        "Loading PDF Generator...",
        "Loading Executive Dashboard...",
        "Connecting 125 Smart Sensors...",
        "Emergency Shutdown Ready...",
        "Grid Health Monitoring Ready...",
        "Model Accuracy : 98.7%",
        "SYSTEM ONLINE"

    ]

    logs = ""

    for i, line in enumerate(boot):

        logs += f"[ OK ] {line}\n"

        percent = int((i + 1) / len(boot) * 100)

        screen.markdown(
            css
            + f"""
<div class="boot">

<div class="ring">
<div class="ring2">
<img class="logo"
src="data:image/png;base64,{logo}">
</div>
</div>

<div class="title">
VOLTORA
</div>

<div class="sub">
AI-Based LT Line Fault Detection
</div>

<div class="sub">
Automatic Emergency Shutdown
</div>

<div class="terminal">
{logs}
</div>

<progress value="{percent}" max="100"></progress>

<div class="percent">
{percent}%
</div>

</div>
""",
            unsafe_allow_html=True,
        )

        time.sleep(0.45)

    time.sleep(1)

    screen.empty()