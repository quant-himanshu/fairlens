"""
FairLens PDF Report Generator
Produces a compliance-ready audit report using ReportLab.
"""

import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from models.schemas import AuditResult, FairnessVerdict

VERDICT_COLORS = {
    FairnessVerdict.FAIR:             colors.HexColor("#3B6D11"),
    FairnessVerdict.MARGINAL:         colors.HexColor("#854F0B"),
    FairnessVerdict.BIASED:           colors.HexColor("#993C1D"),
    FairnessVerdict.SEVERELY_BIASED:  colors.HexColor("#791F1F"),
}


def generate_pdf(audit: AuditResult, explanation=None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=20, spaceAfter=6)
    h2_style = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceAfter=4, spaceBefore=12)
    body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14)
    small_style = ParagraphStyle("small", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#888780"))

    story = []

    # Header
    story.append(Paragraph("FairLens Audit Report", title_style))
    story.append(Paragraph(
        f"Dataset: <b>{audit.dataset_name}</b> &nbsp;|&nbsp; "
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} &nbsp;|&nbsp; "
        f"Rows: {audit.row_count:,}",
        small_style,
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb"), spaceAfter=12))

    # Overall verdict
    verdict_color = VERDICT_COLORS[audit.overall_verdict]
    story.append(Paragraph(
        f'Overall verdict: <font color="{verdict_color.hexval()}"><b>{audit.overall_verdict.value.replace("_", " ").title()}</b></font>',
        body_style,
    ))
    story.append(Paragraph(
        f"Sensitive attributes audited: {', '.join(audit.sensitive_attributes)}",
        body_style,
    ))
    if audit.top_biased_feature:
        story.append(Paragraph(f"Most problematic attribute: <b>{audit.top_biased_feature}</b>", body_style))

    # Claude summary
    if explanation:
        story.append(Spacer(1, 12))
        story.append(Paragraph("AI Analysis (Claude)", h2_style))
        story.append(Paragraph(f"<b>Summary:</b> {explanation.summary}", body_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Root cause:</b> {explanation.root_cause}", body_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Business impact:</b> {explanation.business_impact}", body_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Recommended actions:</b>", body_style))
        for i, action in enumerate(explanation.recommended_actions, 1):
            story.append(Paragraph(f"{i}. {action}", body_style))

    # Metrics table
    story.append(Paragraph("Fairness Metrics", h2_style))
    table_data = [["Metric", "Value", "Ideal Range", "Verdict", "Affected Group"]]
    for m in audit.metrics:
        vc = VERDICT_COLORS[m.verdict]
        table_data.append([
            m.name,
            f"{m.value:.4f}",
            f"{m.ideal_range[0]} – {m.ideal_range[1]}",
            Paragraph(f'<font color="{vc.hexval()}"><b>{m.verdict.value.replace("_", " ").title()}</b></font>', body_style),
            m.affected_group or "—",
        ])

    table = Table(table_data, colWidths=[5.5 * cm, 2 * cm, 3 * cm, 3.5 * cm, 3 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEDFE")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#3C3489")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)

    # Group stats table
    story.append(Paragraph("Group Statistics", h2_style))
    gs_data = [["Attribute", "Group", "Count", "Positive Rate", "TPR", "FPR"]]
    for g in audit.group_stats:
        gs_data.append([
            g.attribute, g.group_name, str(g.count),
            f"{g.positive_rate * 100:.1f}%",
            f"{g.true_positive_rate * 100:.1f}%" if g.true_positive_rate is not None else "—",
            f"{g.false_positive_rate * 100:.1f}%" if g.false_positive_rate is not None else "—",
        ])

    gs_table = Table(gs_data, colWidths=[3 * cm, 3 * cm, 2 * cm, 3 * cm, 2.5 * cm, 2.5 * cm])
    gs_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E1F5EE")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#085041")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(gs_table)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
    story.append(Paragraph(
        "Generated by FairLens · Google Solution Challenge 2026 · AI Bias Detection Platform",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.HexColor("#b4b2a9"), alignment=TA_CENTER),
    ))

    doc.build(story)
    return buf.getvalue()
