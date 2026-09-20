from datetime import datetime

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

from utils.pdf_cover import create_cover_page
from utils.pdf_contents import create_contents_page
from utils.pdf_dashboard import create_dashboard
from utils.pdf_summary import create_summary_page
from utils.pdf_sensor_table import create_sensor_table
from utils.pdf_ai import create_ai_section
from utils.pdf_network import create_network_pages
from utils.pdf_analysis import create_analysis_pages
from utils.pdf_verification import create_verification_page
from utils.pdf_qrcode import create_qr
from utils.pdf_footer import create_footer, add_footer

# ==========================================
# MAIN PDF FUNCTION
# ==========================================

def generate_pdf(
    voltage,
    current,
    frequency,
    temperature,
    fault,
    confidence,
    health,
    shutdown
):

    filename = (
        "Voltora_Report_" +
        datetime.now().strftime("%Y%m%d_%H%M%S") +
        ".pdf"
    )

    doc = SimpleDocTemplate(
        filename,
        leftMargin=30,
        rightMargin=30,
        topMargin=35,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    elements = []

    report_id = datetime.now().strftime(
        "GG-%Y%m%d-%H%M%S"
    )

    # =====================================
    # Cover Page
    # =====================================

    create_cover_page(
        elements,
        report_id,
        fault,
        confidence,
        health,
        shutdown
    )

    elements.append(PageBreak())

    # =====================================
# Table of Contents
# =====================================

    create_contents_page(elements)

    elements.append(PageBreak())

# =====================================
# Executive Dashboard
# =====================================

    create_dashboard(
        elements,
        fault,
        confidence,
        health,
        shutdown
    )

    elements.append(PageBreak())

# =====================================
# Executive Summary
# =====================================

    create_summary_page(
        elements,
        voltage,
        current,
        frequency,
        temperature,
        fault,
        confidence,
        health,
        shutdown
    )

    elements.append(PageBreak())
    # =====================================
# Sensor Data Analysis
# =====================================

    create_sensor_table(
        elements,
        voltage,
        current,
        frequency,
        temperature,
        fault,
        confidence,
        health
    )

    elements.append(Spacer(1,20))


    # =====================================
# AI Analysis
# =====================================

    create_ai_section(
    elements,
    fault,
    confidence,
    health,
    shutdown
)

    elements.append(PageBreak())

    # =====================================
# GIS + SCADA
# =====================================

    create_network_pages(
    elements,
    fault
)

    elements.append(PageBreak())

    # =====================================
# Analysis
# =====================================

    create_analysis_pages(
    elements,
    voltage,
    current,
    frequency,
    temperature
)

    elements.append(PageBreak())

    # =====================================
# QR CODE
# =====================================

    elements.append(
    Paragraph(
        "<font size=18 color='#003366'><b>Application QR Code</b></font>",
        styles["Heading1"]
    )
)

    elements.append(Spacer(1,10))

    create_qr(elements)

    elements.append(PageBreak())

# =====================================
# Verification
# =====================================

    create_verification_page(
    elements,
    report_id
)

    elements.append(PageBreak())

    # =====================================
# Footer
# =====================================

    create_footer(
    elements,
    report_id
    )

    doc.build(
    elements,
    onFirstPage=add_footer,
    onLaterPages=add_footer
)

    return filename