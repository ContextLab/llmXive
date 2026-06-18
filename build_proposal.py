#!/usr/bin/env python3
"""Generate a one-page GPU server funding proposal PDF."""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

OUT = "/home/user/llmXive/gpu-server-proposal.pdf"

INK = colors.HexColor("#1a1a1a")
ACCENT = colors.HexColor("#0b5394")
LIGHT = colors.HexColor("#eef3f8")
RULE = colors.HexColor("#b8c4d0")

styles = getSampleStyleSheet()

title = ParagraphStyle(
    "title", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=15.5, leading=18, textColor=ACCENT, spaceAfter=1,
)
subtitle = ParagraphStyle(
    "subtitle", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8.5, leading=11, textColor=colors.HexColor("#555555"),
)
h = ParagraphStyle(
    "h", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=10, leading=12, textColor=ACCENT, spaceBefore=7, spaceAfter=2,
)
body = ParagraphStyle(
    "body", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8.7, leading=11.4, textColor=INK, alignment=TA_JUSTIFY,
    spaceAfter=3,
)
bullet = ParagraphStyle(
    "bullet", parent=body, leftIndent=11, bulletIndent=2, spaceAfter=1.5,
)
cell = ParagraphStyle(
    "cell", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8.2, leading=10, textColor=INK,
)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
cellr = ParagraphStyle("cellr", parent=cell, alignment=TA_RIGHT)
cellbr = ParagraphStyle("cellbr", parent=cellb, alignment=TA_RIGHT)
foot = ParagraphStyle(
    "foot", parent=styles["Normal"], fontName="Helvetica-Oblique",
    fontSize=7.3, leading=9, textColor=colors.HexColor("#777777"),
)

doc = SimpleDocTemplate(
    OUT, pagesize=LETTER,
    leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    topMargin=0.55 * inch, bottomMargin=0.5 * inch,
    title="GPU Compute Node — Funding Proposal",
    author="Jeremy R. Manning",
)

el = []

el.append(Paragraph("Funding Proposal: GPU Compute Node for the Campus Research Cluster", title))
el.append(Paragraph(
    "Prepared by Jeremy R. Manning &nbsp;|&nbsp; June 2026 &nbsp;|&nbsp; "
    "Request: <b>$185,000</b> (within $150K&ndash;$200K envelope) &nbsp;|&nbsp; "
    "One-time capital, 3-year warranty included", subtitle))
el.append(Spacer(1, 4))
el.append(HRFlowable(width="100%", thickness=1.1, color=ACCENT, spaceAfter=4))

# Summary
el.append(Paragraph("Summary", h))
el.append(Paragraph(
    "We propose a one-time investment of <b>$185,000</b> to purchase a flagship GPU compute "
    "node and integrate it into the existing campus research cluster (Slurm-scheduled, "
    "InfiniBand-connected). The node &mdash; four NVIDIA H200 accelerators with 564&nbsp;GB of "
    "pooled high-bandwidth memory &mdash; closes a critical gap in large-memory accelerated "
    "computing that currently forces our LLM development and automated-discovery work onto "
    "metered cloud GPUs. As a shared cluster resource it will serve multiple labs while "
    "directly accelerating model fine-tuning, high-throughput inference, and the autonomous "
    "research pipeline.", body))

# Justification
el.append(Paragraph("Justification", h))
for b in [
    "<b>A real capability gap.</b> Training, fine-tuning, and serving modern open models "
    "(70B&ndash;400B parameters) require 100+&nbsp;GB of GPU memory and NVLink-coupled "
    "accelerators. The campus cluster currently lacks large-VRAM GPUs, so this work either "
    "stalls in queue or is pushed to costly on-demand cloud instances.",

    "<b>Cost-effective vs. cloud.</b> A comparable 4&times;H200 cloud instance rents for "
    "~$14&ndash;16/hr; at sustained research utilization that is ~$90K&ndash;$120K per year. "
    "The node pays for itself in roughly 18&ndash;24 months and then delivers 2&ndash;3 further "
    "years of compute at only power and maintenance cost &mdash; on-premises, with no data "
    "leaving campus.",

    "<b>Enables automated scientific discovery.</b> Our llmXive platform runs ~50 specialist "
    "LLM agents that brainstorm, draft, and peer-review research artifacts. Local inference "
    "lets these pipelines run continuously without per-token API fees (advancing our "
    "free-first cost principle) and unlocks fine-tuning of domain-specialist models.",

    "<b>Shared, well-utilized asset.</b> The node joins the existing Slurm scheduler, so idle "
    "cycles are immediately available to other groups across the institution &mdash; maximizing "
    "return on a single capital purchase.",
]:
    el.append(Paragraph(b, bullet, bulletText="•"))

# Budget
el.append(Paragraph("Proposed System &amp; Budget", h))

rows = [
    [Paragraph("Component", cellb), Paragraph("Specification", cellb), Paragraph("Cost (USD)", cellbr)],
    [Paragraph("GPU accelerators", cell),
     Paragraph("4 &times; NVIDIA H200 SXM, 141&nbsp;GB HBM3e (HGX baseboard, NVLink/NVSwitch); 564&nbsp;GB pooled", cell),
     Paragraph("$128,000", cellr)],
    [Paragraph("Server platform", cell),
     Paragraph("Dual AMD EPYC (192 cores), HGX carrier, redundant 3&nbsp;kW PSUs", cell),
     Paragraph("$20,000", cellr)],
    [Paragraph("System memory", cell),
     Paragraph("1.5&nbsp;TB DDR5 ECC", cell),
     Paragraph("$10,000", cellr)],
    [Paragraph("Local storage", cell),
     Paragraph("~30&nbsp;TB NVMe (RAID1 OS + high-speed scratch)", cell),
     Paragraph("$8,000", cellr)],
    [Paragraph("Cluster networking", cell),
     Paragraph("NVIDIA ConnectX-7 NDR 400&nbsp;Gb InfiniBand HCA + cabling", cell),
     Paragraph("$6,000", cellr)],
    [Paragraph("Integration", cell),
     Paragraph("Rack/rails/PDU, Slurm integration, burn-in testing", cell),
     Paragraph("$3,000", cellr)],
    [Paragraph("Warranty &amp; support", cell),
     Paragraph("3-year 24&times;7 on-site, next-business-day parts", cell),
     Paragraph("$10,000", cellr)],
    [Paragraph("Total", cellb), Paragraph("", cell), Paragraph("$185,000", cellbr)],
]

tbl = Table(rows, colWidths=[1.35 * inch, 4.25 * inch, 0.95 * inch])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 8.2),
    ("BACKGROUND", (0, -1), (-1, -1), LIGHT),
    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f7f9fb")]),
    ("LINEBELOW", (0, 0), (-1, 0), 0.6, ACCENT),
    ("LINEABOVE", (0, -1), (-1, -1), 0.8, ACCENT),
    ("GRID", (0, 0), (-1, -1), 0.25, RULE),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 2.3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.3),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
]))
el.append(tbl)
el.append(Spacer(1, 3))
el.append(Paragraph(
    "<b>Alternative configuration:</b> for workloads dominated by many-user inference rather "
    "than large-model training, the same budget buys 8&nbsp;&times;&nbsp;NVIDIA L40S (48&nbsp;GB) "
    "for higher aggregate throughput. The H200 build above is recommended as the more "
    "future-proof, training-capable option.", foot))

el.append(Spacer(1, 5))
el.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceAfter=3))
el.append(Paragraph(
    "Expected outcomes: continuous on-premises LLM training/inference, elimination of recurring "
    "cloud GPU spend at sustained utilization, fine-tuning of specialist research agents, and a "
    "shared accelerator resource for the broader campus community. Figures are planning estimates "
    "(June 2026) subject to vendor quotes; power and cooling assumed available in the existing "
    "cluster facility.", foot))

doc.build(el)
print("wrote", OUT)
