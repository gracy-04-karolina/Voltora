from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf(
    filename,
    voltage,
    current,
    frequency,
    temperature,
    fault,
    confidence,
    health,
    shutdown
):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b>VOLTORA</b>", styles["Title"]))

    story.append(Paragraph("Electrical Fault Report", styles["Heading2"]))

    story.append(Paragraph(f"Voltage : {voltage} V", styles["BodyText"]))
    story.append(Paragraph(f"Current : {current} A", styles["BodyText"]))
    story.append(Paragraph(f"Frequency : {frequency} Hz", styles["BodyText"]))
    story.append(Paragraph(f"Temperature : {temperature} °C", styles["BodyText"]))

    story.append(Paragraph("<br/>", styles["BodyText"]))

    story.append(Paragraph(f"Fault : {fault}", styles["BodyText"]))
    story.append(Paragraph(f"Confidence : {confidence:.2f}%", styles["BodyText"]))
    story.append(Paragraph(f"Grid Health : {health}%", styles["BodyText"]))
    story.append(Paragraph(f"Shutdown : {shutdown}", styles["BodyText"]))

    doc.build(story)

if __name__ == "__main__":

    generate_pdf(
        "sample_report.pdf",
        230,
        8.5,
        50,
        35,
        "Normal",
        98.6,
        100,
        "NO"
    )

    print("PDF Created Successfully")