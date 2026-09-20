import streamlit as st
import base64


def show_animated_logo():

    with open("assets/logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
<style>

@keyframes rotateGlow {{

0% {{
transform: rotate(0deg) scale(1);
filter: drop-shadow(0px 0px 8px #00d4ff);
}}

50% {{
transform: rotate(3deg) scale(1.08);
filter: drop-shadow(0px 0px 30px cyan);
}}

100% {{
transform: rotate(0deg) scale(1);
filter: drop-shadow(0px 0px 8px #00d4ff);
}}

}}

@keyframes typing {{

from {{width:0}}

to {{width:100%}}

}}

.logo-container{{
text-align:center;
margin-top:20px;
margin-bottom:15px;
}}

.logo{{
width:170px;
animation:rotateGlow 2.5s infinite ease-in-out;
}}

.title{{
font-size:40px;
font-weight:bold;
color:#00d4ff;
overflow:hidden;
white-space:nowrap;
border-right:3px solid cyan;
width:0;
margin:auto;
animation:typing 3s steps(20,end) forwards;
}}

.subtitle{{
color:white;
font-size:18px;
margin-top:10px;
}}


</style>

<div class="logo-container">

<img class="logo"
src="data:image/png;base64,{data}">

VOLTORA<div class="title">

</div>

<div class="subtitle">
AI-Based LT Line Fault Detection
</div>

<div class="subtitle">
Automatic Emergency Shutdown
</div>


</div>
""",
        unsafe_allow_html=True
    )