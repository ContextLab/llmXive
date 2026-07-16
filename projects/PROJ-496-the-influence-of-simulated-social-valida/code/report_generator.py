"""
Report generation utilities for the llmXive pipeline.
Specifically handles the generation of the Negative Finding Report (PDF).
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch

logger = logging.getLogger(__name__)

def generate_negative_finding_report(
    output_path: Path,
    search_summary: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    scenario: str = "separate_datasets"
) -> None:
    """
    Generates a PDF report detailing the negative finding (no eligible single dataset).

    Args:
        output_path: Path where the PDF will be saved.
        search_summary: Dict containing search metadata (keywords, total found, etc.).
        candidates: List of dataset dicts that failed eligibility (Sim-Only, Real-Only, etc.).
        scenario: One of 'no_datasets', 'separate_datasets', 'qc_failure'.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=colors.HexColor('#2c3e50')
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#34495e')
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leading=14
    )

    # Title
    story.append(Paragraph("Negative Finding Report", title_style))
    story.append(Paragraph(f"Pipeline: Simulated Social Validation Study", normal_style))
    story.append(Paragraph(f"Scenario: {scenario.replace('_', ' ').title()}", normal_style))
    story.append(Spacer(1, 20))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", heading_style))
    story.append(Paragraph(
        "This report documents the outcome of the dataset search phase. "
        "No single dataset was identified that simultaneously contains "
        "both 'Simulated Social Feedback' manipulation and valid "
        "measures of 'Social Anxiety' required for the proposed analysis. "
        "Per the project plan, the pipeline is terminating with a Negative Finding.",
        normal_style
    ))
    story.append(Spacer(1, 15))

    # Search Parameters
    story.append(Paragraph("2. Search Parameters", heading_style))
    keywords = search_summary.get('keywords', [])
    story.append(Paragraph(f"Keywords used: {', '.join(keywords)}", normal_style))
    story.append(Paragraph(f"Total datasets scanned: {search_summary.get('total_scanned', 0)}", normal_style))
    story.append(Paragraph(f"Datasets categorized as 'Eligible': {search_summary.get('eligible_count', 0)}", normal_style))
    story.append(Spacer(1, 15))

    # Detailed Findings based on Scenario
    if scenario == "no_datasets":
        story.append(Paragraph("3. Findings: No Datasets Found", heading_style))
        story.append(Paragraph(
            "The search returned zero datasets matching the core criteria. "
            "This indicates a potential gap in the public neuroimaging repository "
            "for this specific intersection of variables.",
            normal_style
        ))
    elif scenario == "separate_datasets":
        story.append(Paragraph("3. Findings: Separate Datasets Identified", heading_style))
        story.append(Paragraph(
            "The search identified datasets that are either 'Simulated-Only' or 'Real-Only'. "
            "No single dataset satisfied both conditions. The following candidates were identified:",
            normal_style
        ))
        
        # Categorize for display
        sim_only = [c for c in candidates if c.get('status') == 'Sim-Only']
        real_only = [c for c in candidates if c.get('status') == 'Real-Only']
        partial = [c for c in candidates if c.get('status') in ['Partial-EEG', 'Partial-Anxiety', 'None']]

        if sim_only:
            story.append(Paragraph("<b>Simulated-Only Candidates:</b>", normal_style))
            for ds in sim_only:
                text = f"- ID: {ds['dataset_id']} | Title: {ds['title']} | URL: {ds['url']}"
                story.append(Paragraph(text, normal_style))
            story.append(Spacer(1, 10))

        if real_only:
            story.append(Paragraph("<b>Real-Only Candidates:</b>", normal_style))
            for ds in real_only:
                text = f"- ID: {ds['dataset_id']} | Title: {ds['title']} | URL: {ds['url']}"
                story.append(Paragraph(text, normal_style))
            story.append(Spacer(1, 10))
        
        if partial:
            story.append(Paragraph("<b>Partial/Other Candidates:</b>", normal_style))
            for ds in partial:
                text = f"- ID: {ds['dataset_id']} | Status: {ds['status']} | Title: {ds['title']}"
                story.append(Paragraph(text, normal_style))

    elif scenario == "qc_failure":
        story.append(Paragraph("3. Findings: Quality Control Failure", heading_style))
        story.append(Paragraph(
            "While an eligible dataset was found, the preprocessing phase failed "
            "Quality Control checks (e.g., trial retention < 80% or amplitude out of range).",
            normal_style
        ))

    story.append(PageBreak())

    # Conclusion
    story.append(Paragraph("4. Conclusion & Next Steps", heading_style))
    conclusion_text = (
        "Due to the absence of a suitable single dataset (or data quality failure), "
        "the statistical modeling phase (Phase 5) has been bypassed. "
        "The pipeline has exited with code 0 to indicate successful execution of the "
        "negative finding protocol. "
        "Future work may require: <br/>&bull; Expanding search to other repositories (e.g., OSF, Zenodo). "
        "<br/>&bull; Conducting a new data collection study. "
        "<br/>&bull; Re-evaluating the inclusion criteria."
    )
    story.append(Paragraph(conclusion_text, normal_style))

    doc.build(story)
    logger.info(f"Negative finding report generated at {output_path}")
