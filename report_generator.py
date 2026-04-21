"""
report_generator.py — PDF Report Generator for ForensicAI
Phase 5 USP feature.

Generates a professional forensic analysis report using ReportLab.
"""

import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ── Brand colours ──────────────────────────────────────────────────────────────
BRAND_DARK   = HexColor("#0f172a")
BRAND_VIOLET = HexColor("#7c3aed")
BRAND_RED    = HexColor("#ef4444")
BRAND_GREEN  = HexColor("#10b981")
BRAND_SLATE  = HexColor("#64748b")


def _b64_to_image(b64_str, width=None, height=None):
    """Convert a base64 JPEG string to a ReportLab Image flowable."""
    if not b64_str:
        return None
    raw = base64.b64decode(b64_str)
    buf = io.BytesIO(raw)
    img = RLImage(buf)
    if width:
        ratio = img.imageHeight / img.imageWidth
        img.drawWidth = width
        img.drawHeight = width * ratio
    if height:
        img.drawHeight = height
    return img


def generate_report(analysis_data: dict) -> bytes:
    """
    Generate a PDF report from an analysis result dict.

    Parameters
    ----------
    analysis_data : dict — must contain keys like ela_confidence, noise_score,
                    edge_score, unified_score, verdict, filename, exif, and
                    optionally original_image_base64, ela_image_base64.

    Returns
    -------
    bytes — raw PDF file content
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    # ── Custom Styles ──────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=22, textColor=BRAND_VIOLET, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontSize=10, textColor=BRAND_SLATE, alignment=TA_CENTER, spaceAfter=16,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        fontSize=14, textColor=BRAND_DARK, spaceBefore=14, spaceAfter=8,
        borderWidth=1, borderColor=BRAND_VIOLET, borderPadding=4,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, textColor=black, spaceAfter=6,
    )

    # ── Header ─────────────────────────────────────────────────────────────
    story.append(Paragraph("ForensicAI — Image Tampering Analysis Report", title_style))

    ts = analysis_data.get("timestamp")
    if isinstance(ts, datetime):
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
    elif isinstance(ts, str):
        ts_str = ts
    else:
        ts_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    story.append(Paragraph(f"Generated: {ts_str}", subtitle_style))
    story.append(HRFlowable(width="100%", color=BRAND_VIOLET, thickness=1.5))
    story.append(Spacer(1, 12))

    # ── Filename ───────────────────────────────────────────────────────────
    fname = analysis_data.get("filename", "Unknown")
    story.append(Paragraph(f"<b>File analysed:</b>  {fname}", body_style))
    story.append(Spacer(1, 8))

    # ── Original Image ─────────────────────────────────────────────────────
    orig_b64 = analysis_data.get("original_image_base64")
    if orig_b64:
        img = _b64_to_image(orig_b64, width=14 * cm)
        if img:
            story.append(img)
            story.append(Spacer(1, 10))

    # ── ELA Analysis Section ───────────────────────────────────────────────
    story.append(Paragraph("ELA Analysis", section_style))
    ela_b64 = analysis_data.get("ela_image_base64")
    if ela_b64:
        ela_img = _b64_to_image(ela_b64, width=10 * cm)
        if ela_img:
            story.append(ela_img)
            story.append(Spacer(1, 6))

    ela_conf = analysis_data.get("ela_confidence", 0)
    story.append(Paragraph(
        f"ELA Tampered Probability: <b>{ela_conf * 100:.1f}%</b>",
        body_style,
    ))
    story.append(Spacer(1, 10))

    # ── Score Breakdown Table ──────────────────────────────────────────────
    story.append(Paragraph("Score Breakdown", section_style))

    noise_s = analysis_data.get("noise_score", 0)
    edge_s  = analysis_data.get("edge_score", 0)

    table_data = [
        ["Module", "Weight", "Score"],
        ["ELA (DenseNet121)",  "50%",  f"{ela_conf * 100:.1f}%"],
        ["Noise (Laplacian)",  "30%",  f"{noise_s * 100:.1f}%"],
        ["Edge (Gradient)",    "20%",  f"{edge_s * 100:.1f}%"],
    ]
    t = Table(table_data, colWidths=[7 * cm, 3 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), BRAND_VIOLET),
        ("TEXTCOLOR",    (0, 0), (-1, 0), white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 10),
        ("ALIGN",        (1, 0), (-1, -1), "CENTER"),
        ("GRID",         (0, 0), (-1, -1), 0.5, BRAND_SLATE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8fafc"), white]),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # ── Verdict Section ────────────────────────────────────────────────────
    story.append(Paragraph("Verdict", section_style))
    unified = analysis_data.get("unified_score", 0)
    verdict = analysis_data.get("verdict", "Unknown")

    verdict_color = BRAND_RED if verdict == "Tampered" else BRAND_GREEN
    verdict_label = "TAMPERED" if verdict == "Tampered" else "AUTHENTIC"

    verdict_style = ParagraphStyle(
        "VerdictBig", parent=styles["Normal"],
        fontSize=28, leading=34, textColor=verdict_color, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=10,
    )
    story.append(Paragraph(verdict_label, verdict_style))

    score_style = ParagraphStyle(
        "ScoreCenter", parent=styles["Normal"],
        fontSize=14, leading=18, textColor=BRAND_DARK, alignment=TA_CENTER, spaceAfter=10,
    )
    story.append(Paragraph(f"Unified Forgery Score: <b>{unified} / 100</b>", score_style))
    story.append(Spacer(1, 10))

    # ── EXIF Metadata ──────────────────────────────────────────────────────
    story.append(Paragraph("EXIF Metadata", section_style))
    exif = analysis_data.get("exif", {})
    if exif and len(exif) > 0:
        exif_rows = [["Tag", "Value"]]
        for k, v in list(exif.items())[:12]:
            exif_rows.append([str(k), str(v)[:60]])
        et = Table(exif_rows, colWidths=[5 * cm, 10 * cm])
        et.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_SLATE),
            ("TEXTCOLOR",  (0, 0), (-1, 0), white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("GRID",       (0, 0), (-1, -1), 0.4, BRAND_SLATE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8fafc"), white]),
        ]))
        story.append(et)
    else:
        story.append(Paragraph("<i>No EXIF metadata found.</i>", body_style))

    story.append(Spacer(1, 20))

    # ── Footer ─────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", color=BRAND_SLATE, thickness=0.5))
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=BRAND_SLATE, alignment=TA_CENTER, spaceBefore=6,
    )
    story.append(Paragraph(
        "Generated by ForensicAI using DenseNet121 + Multi-modal analysis",
        footer_style,
    ))

    doc.build(story)
    return buf.getvalue()
