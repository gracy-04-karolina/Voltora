import streamlit as st


def control_room_header():

    st.markdown("""
    <style>

    .title{

        background:#08192d;

        padding:20px;

        border-radius:15px;

        border:2px solid #00d4ff;

        text-align:center;

        box-shadow:0px 0px 25px cyan;

        margin-bottom:20px;
    }

    .title h1{

        color:white;

        font-size:42px;

        margin:0;
    }

    .title p{

        color:#9fdcff;

        font-size:18px;
    }

    </style>

    <div class="title">

        <h1>🛰 VOLTORA CONTROL CENTER</h1>

        <p>
        Live Disaster Intelligence • Smart Grid Monitoring • AI Fault Detection
        </p>

    </div>

    """, unsafe_allow_html=True)