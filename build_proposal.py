#!/usr/bin/env python3
"""Generate a one-page GPU server funding proposal PDF (monochrome)."""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

OUT = "/home/user/llmXive/gpu-server-proposal.pdf"

INK = colors.HexColor("#111111")
GRAY = colors.HexColor("#555555")
HDR_BG = colors.HexColor("#e6e6e6")
TOT_BG = colors.HexColor("#d9d9d9")
ALT_BG = colors.HexColor("#f4f4f4")
RULE = colors.HexColor("#999999")

styles = getSampleStyleSheet()

title = ParagraphStyle(
    "title", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=15.5, leading=18, textColor=INK, spaceAfter=2,
)
h = ParagraphStyle(
    "h", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=10, leading=12, textColor=INK, spaceBefore=8, spaceAfter=2,
)
body = ParagraphStyle(
    "body", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8.7, leading=11.4, textColor=INK, alignment=TA_JUSTIFY,
    spaceAfter=3,
)
bullet = ParagraphStyle(
    "bullet", parent=body, leftIndent=11, bulletIndent=2, spaceAfter=2,
)
cell = ParagraphStyle(
    "cell", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8.2, leading=10, textColor=INK,
)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
cellr = ParagraphStyle("cellr", parent=cell, alignment=TA_RIGHT)
cellbr = ParagraphStyle("cellbr", parent=cellb, alignment=TA_RIGHT)
note = ParagraphStyle(
    "note", parent=styles["Normal"], fontName="Helvetica",
    fontSize=7.4, leading=9.2, textColor=GRAY,
)

doc = SimpleDocTemplate(
    OUT, pagesize=LETTER,
    leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    topMargin=0.6 * inch, bottomMargin=0.5 * inch,
    title="GPU Compute Node Funding Proposal",
)

el = []

el.append(Paragraph("Funding Proposal: GPU Compute Node for the Campus Research Cluster", title))
el.append(HRFlowable(width="100%", thickness=1.0, color=INK, spaceBefore=2, spaceAfter=5))

# Summary
el.append(Paragraph("Summary", h))
el.append(Paragraph(
    "We propose a one-time investment of $185,000 to purchase a high-end GPU compute node and "
    "add it to the existing campus research cluster (Slurm-scheduled, InfiniBand-connected). "
    "The node provides four NVIDIA H200 accelerators with 564&nbsp;GB of pooled high-bandwidth "
    "memory. It addresses a gap in large-memory accelerated computing that currently sends our "
    "LLM development and automated-discovery work to metered cloud GPUs. As a shared cluster "
    "resource, it would serve multiple labs while supporting model fine-tuning, high-throughput "
    "inference, and the automated research pipeline.", body))

# Justification
el.append(Paragraph("Justification", h))
for b in [
    "<b>Capability gap.</b> Training, fine-tuning, and serving current open models (roughly 70B "
    "to 400B parameters) need 100&nbsp;GB or more of GPU memory and NVLink-coupled accelerators. "
    "The campus cluster has no large-VRAM GPUs today, so this work either waits in queue or runs "
    "on costly on-demand cloud instances.",

    "<b>Cost relative to cloud.</b> A comparable four-GPU H200 cloud instance rents for about $14 "
    "to $16 per hour, or roughly $90,000 to $120,000 per year at sustained research use. The node "
    "reaches break-even in about 18 to 24 months and then provides two to three further years of "
    "compute at only power and maintenance cost, on campus, with no data leaving the institution.",

    "<b>Support for automated discovery.</b> Our llmXive platform runs about 50 specialist LLM "
    "agents that brainstorm, draft, and review research artifacts. Local inference lets these "
    "pipelines run continuously without per-token API fees and supports fine-tuning of "
    "domain-specialist models.",

    "<b>Shared resource.</b> The node joins the existing Slurm scheduler, so idle cycles are "
    "available to other groups across campus.",
]:
    el.append(Paragraph(b, bullet, bulletText="•"))

# Budget
el.append(Paragraph("Proposed System and Budget", h))

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
     Paragraph("About 30&nbsp;TB NVMe (RAID1 OS plus high-speed scratch)", cell),
     Paragraph("$8,000", cellr)],
    [Paragraph("Cluster networking", cell),
     Paragraph("NVIDIA ConnectX-7 NDR 400&nbsp;Gb InfiniBand HCA plus cabling", cell),
     Paragraph("$6,000", cellr)],
    [Paragraph("Integration", cell),
     Paragraph("Rack, rails, PDU, Slurm integration, burn-in testing", cell),
     Paragraph("$3,000", cellr)],
    [Paragraph("Warranty and support", cell),
     Paragraph("3-year 24&times;7 on-site, next-business-day parts", cell),
     Paragraph("$10,000", cellr)],
    [Paragraph("Total", cellb), Paragraph("", cell), Paragraph("$185,000", cellbr)],
]

tbl = Table(rows, colWidths=[1.35 * inch, 4.25 * inch, 0.95 * inch])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HDR_BG),
    ("TEXTCOLOR", (0, 0), (-1, 0), INK),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 8.2),
    ("BACKGROUND", (0, -1), (-1, -1), TOT_BG),
    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, ALT_BG]),
    ("LINEBELOW", (0, 0), (-1, 0), 0.6, INK),
    ("LINEABOVE", (0, -1), (-1, -1), 0.8, INK),
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
    "Cost figures are planning estimates from our June 2026 conversation with Dartmouth Research "
    "Computing (ITC) and are subject to final vendor quotes. Power and cooling are assumed "
    "available in the existing cluster facility.", note))
el.append(Spacer(1, 2))
el.append(Paragraph(
    "Alternative configuration: for workloads dominated by many-user inference rather than "
    "large-model training, the same budget buys 8 &times; NVIDIA L40S (48&nbsp;GB) for higher "
    "aggregate throughput. The H200 build above is recommended as the more training-capable "
    "option.", note))

# Expected outcomes (own section)
el.append(Paragraph("Expected Outcomes", h))
for b in [
    "Continuous on-campus LLM training and inference, without queueing for scarce accelerators.",
    "Reduced recurring cloud GPU spend once the node is in sustained use.",
    "Capacity to fine-tune specialist research agents on institutional data, kept on campus.",
    "A shared accelerator resource available to the broader campus research community.",
]:
    el.append(Paragraph(b, bullet, bulletText="•"))

doc.build(el)
print("wrote", OUT)
