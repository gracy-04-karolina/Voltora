import streamlit.components.v1 as components
import streamlit as st


def show_scada_grid(fault):

    # ------------------------
    # Status Colors
    # ------------------------

    if fault == "Normal":
        line_color = "#00ff66"
        status = "🟢 GRID NORMAL"

    elif fault == "Overload":
        line_color = "#ff9900"
        status = "🟠 TRANSFORMER OVERLOAD"

    elif fault == "Overvoltage":
        line_color = "#00bfff"
        status = "🔵 OVERVOLTAGE"

    elif fault == "Undervoltage":
        line_color = "#ffff00"
        status = "🟡 UNDERVOLTAGE"

    else:
        line_color = "#ff3333"
        status = "🔴 LINE BREAK"

    
    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>

*{{
margin:0;
padding:0;
box-sizing:border-box;
}}

body{{
background:#071423;
font-family:Arial,Helvetica,sans-serif;
overflow:hidden;
}}

.container{{
position:relative;
width:100%;
height:650px;
background:#141c2b;
border-radius:18px;
overflow:hidden;
}}

.title{{
position:absolute;
top:25px;
width:100%;
text-align:center;
font-size:34px;
font-weight:bold;
color:white;
letter-spacing:1px;
}}

.status{{
position:absolute;
top:95px;
width:100%;
text-align:center;
font-size:22px;
font-weight:bold;
color:{line_color};
text-shadow:0 0 18px {line_color};
}}

.footer{{
position:absolute;
bottom:15px;
width:100%;
text-align:center;
font-size:15px;
color:#c7d0db;
}}

.transformer {{
position:absolute;
left:47%;
top:110px;

transform:translateX(-50%);

font-size:110px;

z-index:10;

filter:

drop-shadow(0 0 15px {line_color})

drop-shadow(0 0 20px {line_color})

drop-shadow(0 0 40px {line_color});
}}

.transformer.overload{{
animation:transformerOverload .45s infinite;
}}

@keyframes transformerOverload{{

0%{{
transform:translateX(-50%) scale(1);
}}

25%{{
transform:translateX(-50%) scale(1.05);
}}

50%{{
transform:translateX(-50%) scale(.96);
}}

75%{{
transform:translateX(-50%) scale(1.04);
}}

100%{{
transform:translateX(-50%) scale(1);
}}

}}

.main-line{{
position:absolute;
left:150px;
top:260px;
width:900px;
height:10px;

background:linear-gradient(
90deg,
{line_color},
white,
{line_color}
);

border-radius:20px;

box-shadow:
0 0 15px {line_color},
0 0 30px {line_color},
0 0 50px {line_color};

animation:lineGlow 1s infinite alternate;
}}

@keyframes lineGlow{{

0%{{
box-shadow:0 0 10px {line_color};
}}

100%{{
box-shadow:0 0 30px {line_color};
}}

}}

.power{{
position:absolute;

top:252px;

left:160px;

width:18px;

height:18px;

background:white;

border-radius:50%;

box-shadow:0 0 18px white;

animation:powerMove 3s linear infinite;
}}

.p2{{animation-delay:.6s;}}

.p3{{animation-delay:1.2s;}}

.p4{{animation-delay:1.8s;}}

.p5{{animation-delay:2.4s;}}

@keyframes powerMove{{

0%{{
left:160px;
}}

100%{{
left:1030px;
}}

}}

.breaker{{
position:absolute;

left:610px;

top:220px;

width:110px;

text-align:center;

z-index:30;
}}

.breaker-arm{{

width:90px;

height:8px;

background:#dddddd;

border:2px solid #666;

border-radius:10px;

margin:auto;

box-shadow:0 0 10px white;

transition:.5s;

}}

.breaker-open{{

background:#dddddd;

border:2px solid red;

box-shadow:0 0 15px red;

transform:rotate(-32deg);

}}

.breaker-label{{
margin-top:25px;

font-size:18px;

font-weight:bold;

color:white;
}}

.pole{{
position:absolute;

width:14px;

height:170px;

background:#8B5A2B;
}}

.house{{
position:absolute;

font-size:90px;

filter:drop-shadow(0 0 14px {line_color});

animation:houseGlow 1.2s infinite alternate;
}}

.house.off{{

filter:grayscale(100%);

opacity:.25;

animation:none;

text-shadow:none;

}}

@keyframes houseGlow{{

0%{{
transform:scale(1);
}}

100%{{
transform:scale(1.06);
}}

}}

.fault-wave{{

position:absolute;

top:252px;

left:585px;

width:22px;

height:22px;

background:#ff3333;

border-radius:50%;

box-shadow:
0 0 12px red,
0 0 25px red,
0 0 40px red;

animation:faultTravel 1s linear infinite;

}}

@keyframes faultTravel{{

0%{{
left:520px;
}}

100%{{
left:650px;
}}

}}
.lightning{{

position:absolute;
left:585px;
top:220px;
font-size:45px;

animation:lightningFlash .2s infinite;

text-shadow:
0 0 20px yellow,
0 0 40px orange;

}}
@keyframes lightningFlash{{

0%{{opacity:1;}}

50%{{opacity:.3;}}

100%{{opacity:1;}}

}}

.smoke{{

position:absolute;

left:495px;

top:105px;

width:130px;

height:130px;

border-radius:50%;

background:rgba(255,255,255,.22);

filter:blur(28px);

animation:smokeRise 2s infinite;

}}

@keyframes smokeRise{{

0%{{
transform:translateY(0) scale(.7);
opacity:.7;
}}

40%{{
opacity:.6;
}}

100%{{
transform:translateY(-80px) scale(1.5);
opacity:0;
}}

}}

.banner{{

position:absolute;

bottom:25px;

left:-100%;

width:100%;

font-size:26px;

font-weight:bold;

color:#ff3333;

text-shadow:0 0 20px red;

white-space:nowrap;

animation:alarmMove 7s linear infinite;

}}

@keyframes bannerFlash{{

0%{{opacity:1;}}

50%{{opacity:.25;}}

100%{{opacity:1;}}

}}

@keyframes alarmMove{{

0%{{
left:-100%;
}}

100%{{
left:100%;
}}

}}

</style>
</head>

<body>

<div class="container">

<div class="title">
⚡ Voltora SCADA
</div>

<div class="status">
{status}
</div>
"""
    html += f"""

<div style="
position:absolute;
top:135px;
right:35px;
font-size:16px;
color:white;
line-height:28px;
text-align:left;
">

Voltage : {st.session_state.get("voltage",0)} V<br>

Current : {st.session_state.get("current",0)} A<br>

Frequency : {st.session_state.get("frequency",0)} Hz<br>

Temperature : {st.session_state.get("temperature",0)} °C

</div>


"""
    html += f"""
<div class="transformer {'overload' if fault=='Overload' else ''}">
🏭

</div>
"""
    breaker_text = (
    "🟢 BREAKER CLOSED"
    if fault == "Normal"
    else "🔴 BREAKER OPEN"
)

    html += f"""
<div class="breaker" style="left:590px;">

<div class="breaker-arm {'breaker-open' if fault!='Normal' else ''}">
</div>

<div class="breaker-label">
{breaker_text}
</div>

</div>
"""
    if fault == "Normal":

        html += """
<div class="main-line"></div>
"""

    else:

        html += f"""
<div class="main-line"
style="
background:{line_color};
opacity:.35;
">
</div>
"""
    if fault == "Normal":

        html += """
<div class="power"></div>
<div class="power p2"></div>
<div class="power p3"></div>
<div class="power p4"></div>
<div class="power p5"></div>
"""

    elif fault == "Overload":

        html += """
<div class="power"></div>
<div class="power p2"></div>
"""
    if fault != "Normal":

        html += """
<div class="fault-wave"></div>

"""
    if fault != "Normal":

        html += """
<div class="lightning">
────⚡────
</div>
"""
    if fault == "Overload":

        html += """
<div class="smoke"></div>
"""
    html += """
<div class="pole" style="left:180px;top:250px;"></div>

<div class="pole" style="left:450px;top:250px;"></div>

<div class="pole" style="left:720px;top:250px;"></div>
"""
    html += """

<div style="
position:absolute;
left:187px;
top:420px;
width:4px;
height:60px;
background:#bbbbbb;
"></div>

<div style="
position:absolute;
left:457px;
top:420px;
width:4px;
height:60px;
background:#bbbbbb;
"></div>

<div style="
position:absolute;
left:727px;
top:420px;
width:4px;
height:60px;
background:#bbbbbb;
"></div>

"""
    if fault == "Line Break":

        html += """
<div class="house" style="left:200px;top:315px;">🏠</div>

<div class="house off" style="left:465px;top:315px;">🏠</div>

<div class="house off" style="left:730px;top:315px;">🏠</div>
"""

    else:

        html += """
<div class="house" style="left:140px;top:330px;">🏠</div>

<div class="house" style="left:405px;top:330px;">🏠</div>

<div class="house" style="left:670px;top:330px;">🏠</div>
"""
    if fault != "Normal":

        html += """
<div class="banner">
🚨 AUTO EMERGENCY SHUTDOWN ACTIVATED
</div>
"""
    html += """
<div class="footer">
Voltora
AI Based LT Line Fault Detection & Automatic Emergency Shutdown
</div>

</div>

</body>

</html>
"""

    components.html(html, height=650)