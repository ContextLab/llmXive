import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch

def generate_negative_finding_report(
    output_path: str,
    search_summary: Dict[str, Any],
    none_datasets: List[Dict[str, Any]],
    report_type: str = "none"
):
    """
    Generate a PDF report for a Negative Finding scenario.
    
    Args:
        output_path: Path to the output PDF file.
        search_summary: Dictionary containing search metadata (keywords, counts, etc.).
        none_datasets: List of datasets with 'None' status.
        report_type: Type of negative finding ("none" or "separate").
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    table_style = styles['Table']
    
    # Title
    title_text = "Negative Finding Report: No Eligible Datasets Found" if report_type == "none" else "Negative Finding Report: Separate Datasets Found"
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Search Summary Section
    story.append(Paragraph("Search Summary", heading_style))
    summary_text = (
        f"Total Datasets Searched: {search_summary.get('total_datasets_searched', 0)}<br/>"
        f"Datasets with '{'None' if report_type == 'none' else 'Separate'}' Status: {search_summary.get('none_status_count', 0)}<br/>"
        f"Search Keywords: {', '.join(search_summary.get('search_keywords', []))}"
    )
    story.append(Paragraph(summary_text, normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Data Gap Statement
    story.append(Paragraph("Data Gap Statement", heading_style))
    gap_text = search_summary.get('data_gap_statement', "No specific data gap statement provided.")
    story.append(Paragraph(gap_text, normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Dataset Details Section
    story.append(Paragraph("Dataset Details", heading_style))
    
    if not none_datasets:
        story.append(Paragraph("No datasets matched the criteria for this negative finding scenario.", normal_style))
    else:
        # Prepare table data
        headers = ["Dataset ID", "Title", "Feedback Type", "Anxiety Measure", "URL"]
        data = [headers]
        
        for ds in none_datasets:
            row = [
                ds.get('dataset_id', 'N/A'),
                ds.get('title', 'N/A'),
                ds.get('feedback_type', 'N/A'),
                ds.get('anxiety_measure', 'N/A'),
                ds.get('url', 'N/A')
            ]
            data.append(row)
        
        # Create table
        table = Table(data, colWidths=[1.5*inch, 3.5*inch, 1.5*inch, 1.5*inch, 2.0*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
    
    # Build PDF
    doc.build(story)
