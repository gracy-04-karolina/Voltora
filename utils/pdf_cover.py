from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib.units import inch
import os
from datetime import datetime


styles = getSampleStyleSheet()


# =====================================================
# Executive Cover Page
# =====================================================

def create_cover_page(
    elements,
    report_id,
    fault,
    confidence,
    health,
    shutdown
):

    # ---------------------------------------
    # Logo
    # ---------------------------------------

    logo = "assets/logo.png"

    if os.path.exists(logo):

        elements.append(
            Image(
                logo,
                width=1.4 * inch,
                height=1.4 * inch
            )
        )

    elements.append(Spacer(1, 15))

    # ---------------------------------------
    # Title
    # ---------------------------------------

    title = Paragraph(
        """
        <font size=26 color='#003366'><b>VOLTORA</b></font>
        """,
        styles["Title"]
    )

    elements.append(title)

    subtitle = Paragraph(
        """
        <font size=15>

        AI-Based LT Line Fault Detection<br/>

        Automatic Emergency Shutdown System

        </font>
        """,
        styles["Heading2"]
    )

    elements.append(subtitle)

    elements.append(Spacer(1, 20))

    # ---------------------------------------
    # Report Information
    # ---------------------------------------

    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    info = [

        ["Report ID", report_id],

        ["Generated On", now],

        ["AI Prediction", fault],

        ["Confidence", f"{confidence:.2f}%"],

        ["Grid Health", f"{health}%"],

        ["Emergency Shutdown", shutdown]

    ]

    table = Table(info, colWidths=[170, 260])

    table.setStyle(

        TableStyle(

            [

                ("GRID", (0, 0), (-1, -1), 1, colors.grey),

                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#003366")),

                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),

                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),

                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),

                ("BACKGROUND", (1, 0), (1, -1), colors.whitesmoke),

                ("ALIGN", (0, 0), (-1, -1), "CENTER"),

            ]

        )

    )

    elements.append(table)

    elements.append(Spacer(1, 25))

    # ---------------------------------------
    # Executive Summary
    # ---------------------------------------

    elements.append(

        Paragraph(

            "<b><font size=18 color='#003366'>Executive Summary</font></b>",

            styles["Heading1"]

        )

    )

    elements.append(Spacer(1, 12))

    summary = f"""

    Voltora continuously monitors the Low Tension (LT) electrical
    distribution network using Artificial Intelligence.

    During this monitoring cycle, the AI detected the fault

    <b>{fault}</b>

    with a confidence level of

    <b>{confidence:.2f}%</b>.

    Based on the severity of the detected condition,
    the Automatic Emergency Shutdown mechanism was

    <b>{shutdown}</b>

    to protect transformers, feeders and consumers.

    Current Grid Health:

    <b>{health}%</b>

    """

    elements.append(

        Paragraph(

            summary,

            styles["BodyText"]

        )

    )

    elements.append(Spacer(1, 25))