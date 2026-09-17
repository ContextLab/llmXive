import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import base64

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Attempt to register a standard font if available, otherwise fallback to default
try:
    # Try to find a standard font on the system
    import platform
    if platform.system() == "Windows":
        font_path = "C:/Windows/Fonts/arial.ttf"
    elif platform.system() == "Darwin":
        font_path = "/System/Library/Fonts/Helvetica.ttc"
    else:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('CustomFont', font_path))
        font_name = 'CustomFont'
    else:
        font_name = 'Helvetica'
except Exception:
    font_name = 'Helvetica'

logger = logging.getLogger(__name__)

def load_analysis_results(results_path: str) -> Dict[str, Any]:
    """Load the analysis results JSON file."""
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Analysis results file not found: {results_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_visualization_paths(vis_dir: str) -> Dict[str, str]:
    """Load the paths to generated visualizations."""
    vis_path = Path(vis_dir)
    if not vis_path.exists():
        logger.warning(f"Visualization directory not found: {vis_dir}")
        return {}
    
    vis_files = {}
    for ext in ['png', 'jpg', 'jpeg', 'pdf']:
        for file in vis_path.glob(f"*.{ext}"):
            # Categorize based on filename patterns
            name = file.stem.lower()
            if 'box' in name:
                vis_files['box_plot'] = str(file)
            elif 'cdf' in name:
                vis_files['cdf_plot'] = str(file)
            elif 'sensitivity' in name:
                vis_files['sensitivity_plot'] = str(file)
            else:
                # Default to first found if not categorized
                if not vis_files:
                    vis_files['default'] = str(file)
    
    return vis_files

def generate_html_report(results: Dict[str, Any], vis_paths: Dict[str, str], output_path: str) -> None:
    """Generate an HTML report (fallback if PDF generation fails or for quick viewing)."""
    # Basic HTML structure
    html_content = f"""
    <html>
    <head>
        <title>Code Generation Impact Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            h2 {{ color: #555; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            .metric {{ background: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; }}
            .img-container {{ text-align: center; margin: 20px 0; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Analysis Report: Impact of Code Generation on Review Time</h1>
        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <h2>Statistical Results</h2>
        <div class="metric">
            <strong>P-Value:</strong> {results.get('p_value', 'N/A')}
        </div>
        <div class="metric">
            <strong>Effect Size (Cohen's d):</strong> {results.get('effect_size', 'N/A')}
        </div>
        <div class="metric">
            <strong>Significance:</strong> {results.get('is_significant', 'N/A')}
        </div>
        
        <h2>Visualizations</h2>
        {generate_img_html(vis_paths)}
        
        <h2>Sensitivity Analysis</h2>
        <p>Consistency Check: {results.get('sensitivity', {}).get('consistent', 'N/A')}</p>
        <table>
            <tr><th>Subset</th><th>P-Value</th><th>Significant?</th></tr>
            {generate_sensitivity_table(results.get('sensitivity', {}).get('subsets', []))}
        </table>
    </body>
    </html>
    """
    
    with open(output_path, 'w') as f:
        f.write(html_content)

def generate_img_html(vis_paths: Dict[str, str]) -> str:
    """Generate HTML image tags for visualizations."""
    html = ""
    labels = {
        'box_plot': 'Review Duration Distribution (Box Plot)',
        'cdf_plot': 'Cumulative Distribution Function (CDF)',
        'sensitivity_plot': 'Sensitivity Analysis Plot'
    }
    
    for key, label in labels.items():
        if key in vis_paths:
            # Encode image to base64 to embed in HTML
            try:
                with open(vis_paths[key], 'rb') as img_file:
                    encoded = base64.b64encode(img_file.read()).decode('utf-8')
                    ext = vis_paths[key].split('.')[-1]
                    html += f"""
                    <div class="img-container">
                        <h3>{label}</h3>
                        <img src="data:image/{ext};base64,{encoded}" alt="{label}">
                    </div>
                    """
            except Exception as e:
                logger.warning(f"Could not embed image {vis_paths[key]}: {e}")
                html += f"<p>{label} (Image not available)</p>"
    return html

def generate_sensitivity_table(subsets: List[Dict]) -> str:
    """Generate HTML table rows for sensitivity analysis."""
    rows = ""
    for i, subset in enumerate(subsets):
        sig = "Yes" if subset.get('p_value', 1.0) < 0.05 else "No"
        rows += f"<tr><td>Subset {i+1}</td><td>{subset.get('p_value', 'N/A'):.4f}</td><td>{sig}</td></tr>"
    return rows

def generate_pdf_report(results: Dict[str, Any], vis_paths: Dict[str, str], output_path: str) -> None:
    """Generate a comprehensive PDF report using ReportLab."""
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=24,
        spaceAfter=30,
        alignment=1 # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        leading=14,
        spaceAfter=6
    )

    # Title
    story.append(Paragraph("Impact of Code Generation on Code Review Time", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 20))

    # Executive Summary / Statistical Results
    story.append(Paragraph("1. Statistical Results", heading_style))
    
    p_val = results.get('p_value')
    effect_size = results.get('effect_size')
    is_sig = results.get('is_significant', False)
    
    summary_data = [
        ["Metric", "Value"],
        ["P-Value", f"{p_val:.4f}" if p_val is not None else "N/A"],
        ["Effect Size (Cohen's d)", f"{effect_size:.4f}" if effect_size is not None else "N/A"],
        ["Statistically Significant (α=0.05)", "Yes" if is_sig else "No"]
    ]
    
    t = Table(summary_data, colWidths=[4*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # Visualizations
    story.append(Paragraph("2. Visualizations", heading_style))
    
    # Box Plot
    if 'box_plot' in vis_paths:
        story.append(Paragraph("Review Duration Distribution", body_style))
        try:
            img = Image(vis_paths['box_plot'], width=6*inch, height=4*inch)
            story.append(img)
        except Exception as e:
            story.append(Paragraph(f"Box plot image could not be loaded: {e}", body_style))
        story.append(Spacer(1, 10))
    
    # CDF Plot
    if 'cdf_plot' in vis_paths:
        story.append(Paragraph("Cumulative Distribution Function (CDF)", body_style))
        try:
            img = Image(vis_paths['cdf_plot'], width=6*inch, height=4*inch)
            story.append(img)
        except Exception as e:
            story.append(Paragraph(f"CDF image could not be loaded: {e}", body_style))
        story.append(Spacer(1, 10))

    # Sensitivity Analysis
    story.append(Paragraph("3. Sensitivity Analysis", heading_style))
    sens = results.get('sensitivity', {})
    consistent = sens.get('consistent', False)
    story.append(Paragraph(f"Consistency Check (≥80% subsets significant): {'Passed' if consistent else 'Failed'}", body_style))
    
    subsets = sens.get('subsets', [])
    if subsets:
        sens_data = [["Subset", "P-Value", "Significant?"]]
        for i, sub in enumerate(subsets):
            p = sub.get('p_value')
            sig = "Yes" if p is not None and p < 0.05 else "No"
            sens_data.append([f"Subset {i+1}", f"{p:.4f}" if p else "N/A", sig])
        
        t_sens = Table(sens_data, colWidths=[2*inch, 2*inch, 1.5*inch])
        t_sens.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t_sens)
    
    story.append(Spacer(1, 20))
    
    # End of Report
    story.append(Paragraph("4. Conclusion", heading_style))
    conclusion = (
        "The analysis indicates " + ("a statistically significant difference" if is_sig else "no statistically significant difference") + 
        " in code review times between the LLM-like and Human cohorts. "
        "The effect size suggests " + ("a meaningful impact" if abs(effect_size or 0) > 0.5 else "a small or negligible impact") + 
        "."
    )
    story.append(Paragraph(conclusion, body_style))

    # Build PDF
    doc.build(story)

def main():
    """Main entry point for the report generator."""
    # Define paths based on project structure
    base_dir = Path(__file__).resolve().parent.parent.parent
    results_path = base_dir / "data" / "processed" / "analysis_results.json"
    vis_dir = base_dir / "data" / "processed" / "visualizations"
    output_dir = base_dir / "reports"
    output_pdf = output_dir / "analysis_report.pdf"
    output_html = output_dir / "analysis_report.html"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    try:
        # Load inputs
        logger.info(f"Loading analysis results from {results_path}")
        results = load_analysis_results(str(results_path))
        
        logger.info(f"Loading visualizations from {vis_dir}")
        vis_paths = load_visualization_paths(str(vis_dir))
        
        if not vis_paths:
            logger.warning("No visualizations found. Generating report with placeholders.")

        # Generate PDF
        logger.info(f"Generating PDF report: {output_pdf}")
        generate_pdf_report(results, vis_paths, str(output_pdf))
        
        # Generate HTML (optional but useful)
        logger.info(f"Generating HTML report: {output_html}")
        generate_html_report(results, vis_paths, str(output_html))
        
        logger.info("Report generation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
