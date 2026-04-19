import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

DARK_BG    = colors.HexColor("#0A0F1E")
CARD_BG    = colors.HexColor("#0D1B2A")
ACCENT     = colors.HexColor("#1E90FF")
TEXT_WHITE = colors.HexColor("#E8F4FD")
TEXT_GRAY  = colors.HexColor("#8BA3BF")
GREEN      = colors.HexColor("#00C896")
ORANGE     = colors.HexColor("#FFA500")
RED        = colors.HexColor("#FF4444")
SELECTED   = colors.HexColor("#1E3A5F")

def export_report(data: dict, output_path: str = None) -> str:
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(os.path.expanduser("~"), "Desktop", f"GPU-T_Report_{timestamp}.pdf")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = _build_styles()
    story  = []

    story += _build_header(styles)
    story.append(Spacer(1, 0.5*cm))

    if "os" in data:
        story += _build_section("Operating System", data["os"], styles)

    if "cpu" in data:
        story += _build_section("Processor", data["cpu"], styles)

    if "ram" in data:
        story += _build_section("Memory", data["ram"], styles)

    if "gpu" in data:
        for i, gpu in enumerate(data["gpu"]):
            story += _build_section(f"GPU {i+1}", gpu, styles)

    if "board" in data:
        story += _build_section("Motherboard", data["board"], styles)

    # Disk
    if "disk" in data:
        for i, disk in enumerate(data["disk"]):
            story += _build_section(f"Disk {i+1}", disk, styles)

    if "network" in data:
        story += _build_section("Network", data["network"], styles)

    if "health" in data:
        story += _build_health_section(data["health"], styles)

    story += _build_footer(styles)

    doc.build(story)
    return output_path


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Title_GPU",
        fontSize=28,
        textColor=ACCENT,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=5,
    ))

    styles.add(ParagraphStyle(
        name="Subtitle_GPU",
        fontSize=11,
        textColor=TEXT_GRAY,
        alignment=TA_CENTER,
        fontName="Helvetica",
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontSize=13,
        textColor=TEXT_WHITE,
        fontName="Helvetica-Bold",
        spaceAfter=8,
        spaceBefore=12,
        backColor=SELECTED,
        leftIndent=8,
        rightIndent=8,
        borderPadding=6,
    ))

    styles.add(ParagraphStyle(
        name="FieldKey",
        fontSize=10,
        textColor=TEXT_GRAY,
        fontName="Helvetica",
    ))

    styles.add(ParagraphStyle(
        name="FieldValue",
        fontSize=10,
        textColor=TEXT_WHITE,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        name="Footer_GPU",
        fontSize=9,
        textColor=TEXT_GRAY,
        alignment=TA_CENTER,
        fontName="Helvetica",
    ))

    return styles


def _build_header(styles):
    elements = []
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph("⚡ GPU-T", styles["Title_GPU"]))
    elements.append(Paragraph("Infrastructure Diagnostic Report", styles["Subtitle_GPU"]))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["Subtitle_GPU"]
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=10))
    return elements


def _build_section(title, data: dict, styles):
    elements = []
    elements.append(Paragraph(f"  {title}", styles["SectionTitle"]))

    rows = []
    for key, value in data.items():
        if key == "brand":
            continue
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value) if value else "N/A"
        elif isinstance(value, dict):
            continue
        rows.append([
            Paragraph(str(key).replace("_", " ").title(), styles["FieldKey"]),
            Paragraph(str(value), styles["FieldValue"]),
        ])

    if rows:
        table = Table(rows, colWidths=[5*cm, 12*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), CARD_BG),
            ("TEXTCOLOR",   (0, 0), (-1, -1), TEXT_WHITE),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CARD_BG, SELECTED]),
            ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",    (0, 0), (-1, -1), 10),
            ("PADDING",     (0, 0), (-1, -1), 6),
            ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#1A2744")),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)

    elements.append(Spacer(1, 0.3*cm))
    return elements


def _build_health_section(health: dict, styles):
    elements = []
    elements.append(Paragraph("  System Health Score", styles["SectionTitle"]))

    overall = health.get("overall", 0)
    color = GREEN if overall >= 75 else ORANGE if overall >= 50 else RED

    score_data = [[
        Paragraph("Overall Score", styles["FieldKey"]),
        Paragraph(f"{overall}/100", ParagraphStyle(
            name="Score",
            fontSize=16,
            textColor=color,
            fontName="Helvetica-Bold"
        )),
    ]]

    for key, val in health.items():
        if key == "overall":
            continue
        if isinstance(val, tuple) and len(val) == 2:
            score, status = val
            score_color = GREEN if score >= 75 else ORANGE if score >= 50 else RED
            score_data.append([
                Paragraph(key.upper(), styles["FieldKey"]),
                Paragraph(f"{score}/100 - {status}", ParagraphStyle(
                    name=f"S_{key}",
                    fontSize=10,
                    textColor=score_color,
                    fontName="Helvetica-Bold"
                )),
            ])

    table = Table(score_data, colWidths=[5*cm, 12*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), CARD_BG),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CARD_BG, SELECTED]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#1A2744")),
        ("PADDING",     (0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3*cm))
    return elements


def _build_footer(styles):
    elements = []
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        f"GPU-T Infrastructure Diagnostic Tool  |  {datetime.now().strftime('%Y')}",
        styles["Footer_GPU"]
    ))
    return elements


def export_json(data: dict, output_path: str = None) -> str:
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(os.path.expanduser("~"), "Desktop", f"GPU-T_Report_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False, default=str)

    return output_path