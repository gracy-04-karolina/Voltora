from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

styles = getSampleStyleSheet()


# =====================================
# Footer inside the report
# =====================================

def create_footer(elements, report_id):

    elements.append(

        Paragraph(

f"""

<hr/>

<b>Voltora</b><br/>

AI-Based LT Line Fault Detection & Automatic Emergency Shutdown<br/><br/>

<b>Report ID :</b> {report_id}

""",

styles["Normal"]

        )

    )


# =====================================
# Footer on every page
# =====================================

def add_footer(canvas, doc):

    canvas.saveState()

    canvas.setFont("Helvetica", 9)

    canvas.drawString(
        20 * mm,
        10 * mm,
        "Voltora | Confidential Engineering Report"
    )

    canvas.drawRightString(
        190 * mm,
        10 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()