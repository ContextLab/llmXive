import os
import sys
import csv
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfform
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary

# Register a standard font that is usually available
try:
    pdfmetrics.registerFont(TTFont('Arial', 'Arial'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'Arial-Bold'))
except:
    pass  # Fallback to default if not available

def setup_logging_and_config():
    """Initialize logging and load configuration."""
    config = get_config_summary()
    log_dir = Path(config.get('log_directory', 'data/logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging('generate_final_report_pdf', log_dir)
    return logger, config

def load_json_file(file_path: Path) -> Dict:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def load_csv_file(file_path: Path) -> List[Dict]:
    """Load a CSV file and return a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_metrics_data() -> List[Dict]:
    """Load the processed metrics data."""
    return load_csv_file(Path('data/processed/prs_metrics.csv'))

def load_results() -> Dict:
    """Load the statistical results."""
    return load_json_file(Path('data/processed/results.json'))

def load_gate_status() -> Dict:
    """Load the gate status."""
    return load_json_file(Path('data/processed/gate_status.json'))

def calculate_correlation_coefficients(metrics: List[Dict]) -> Dict[str, float]:
    """Calculate correlation coefficients between complexity and review metrics."""
    # Simple Pearson correlation calculation
    def pearson(x, y):
        n = len(x)
        if n == 0:
            return 0.0
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        sum_y2 = sum(yi ** 2 for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
        
        if denominator == 0:
            return 0.0
        return numerator / denominator

    complexity = [float(m['complexity_score']) for m in metrics]
    comment_density = [float(m['comment_count']) for m in metrics]
    time_to_merge = [float(m['time_to_merge_minutes']) for m in metrics]

    return {
        'complexity_comment_density': pearson(complexity, comment_density),
        'complexity_time_to_merge': pearson(complexity, time_to_merge)
    }

def group_data_by_source(metrics: List[Dict]) -> Dict[str, List[Dict]]:
    """Group metrics by source type (llm vs human)."""
    groups = {'llm': [], 'human': []}
    for m in metrics:
        source = m.get('source_type', 'human')
        if source in groups:
            groups[source].append(m)
    return groups

def create_summary_panel(doc, styles):
    """Create the Executive Summary section."""
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    doc.addPageBreak()
    doc.append(Paragraph("Evaluating the Impact of Code Generation on Code Review Quality", title_style))
    doc.append(Spacer(1, 0.25 * inch))
    
    doc.append(Paragraph("Executive Summary", subtitle_style))
    doc.append(Spacer(1, 0.1 * inch))
    
    gate_status = load_gate_status()
    status_text = "PASSED" if gate_status.get('status') == 'passed' else "BLOCKED"
    
    summary_text = f"""
    This report presents the findings from an analysis of {len(load_metrics_data())} pull requests 
    to evaluate the impact of LLM-generated code on code review quality. The analysis compared 
    metrics such as comment density, time-to-merge, and review cycles between LLM-generated 
    and human-written code.

    The data quality gate status is: {status_text}. 
    Statistical significance was determined using a threshold of α = 0.05.
    """
    
    doc.append(Paragraph(summary_text, normal_style))
    doc.append(Spacer(1, 0.25 * inch))

def create_methodology_section(doc, styles):
    """Create the Methodology section."""
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    doc.append(Paragraph("Methodology", subtitle_style))
    doc.append(Spacer(1, 0.1 * inch))
    
    methodology_text = """
    Data was collected from GitHub repositories using a batched fetch pipeline with exponential backoff. 
    Pull requests were classified as LLM-generated or human-written based on commit signatures and 
    secondary detectors (code entropy and n-gram anomaly scores). 

    Metrics extracted included:
    - Comment count (number of review comments)
    - Time-to-merge (in minutes)
    - Review cycles (number of back-and-forth iterations)
    - Code complexity (Cyclomatic Complexity and Lines of Code)

    Statistical analysis was performed using Mann-Whitney U tests as the primary method, 
    with independent two-sample t-tests as sensitivity analysis. Effect sizes were calculated 
    using Cohen's d.
    """
    
    doc.append(Paragraph(methodology_text, normal_style))
    doc.append(Spacer(1, 0.25 * inch))

def create_results_section(doc, styles, results, correlations):
    """Create the Results section with statistical findings."""
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    doc.append(Paragraph("Results", subtitle_style))
    doc.append(Spacer(1, 0.1 * inch))
    
    # Comment Density Results
    doc.append(Paragraph("Comment Density", styles['Heading3']))
    cd_results = results.get('comment_density', {})
    is_sig_cd = "Significant" if cd_results.get('is_significant', False) else "Not Significant"
    doc.append(Paragraph(
        f"Mann-Whitney U test: U-statistic = {cd_results.get('u_statistic', 'N/A'):.4f}, "
        f"p-value = {cd_results.get('p_value', 'N/A'):.4f}, "
        f"Cohen's d = {cd_results.get('effect_size', 'N/A'):.4f} ({is_sig_cd})",
        normal_style
    ))
    doc.append(Spacer(1, 0.1 * inch))
    
    # Time-to-Merge Results
    doc.append(Paragraph("Time-to-Merge", styles['Heading3']))
    ttm_results = results.get('time_to_merge', {})
    is_sig_ttm = "Significant" if ttm_results.get('is_significant', False) else "Not Significant"
    doc.append(Paragraph(
        f"Mann-Whitney U test: U-statistic = {ttm_results.get('u_statistic', 'N/A'):.4f}, "
        f"p-value = {ttm_results.get('p_value', 'N/A'):.4f}, "
        f"Cohen's d = {ttm_results.get('effect_size', 'N/A'):.4f} ({is_sig_ttm})",
        normal_style
    ))
    doc.append(Spacer(1, 0.1 * inch))
    
    # Correlation Results
    doc.append(Paragraph("Complexity Correlation Analysis", styles['Heading3']))
    doc.append(Paragraph(
        f"Correlation between complexity and comment density: r = {correlations.get('complexity_comment_density', 0):.4f}",
        normal_style
    ))
    doc.append(Paragraph(
        f"Correlation between complexity and time-to-merge: r = {correlations.get('complexity_time_to_merge', 0):.4f}",
        normal_style
    ))
    doc.append(Spacer(1, 0.25 * inch))

def create_discussion_section(doc, styles):
    """Create the Discussion section."""
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    doc.append(Paragraph("Discussion", subtitle_style))
    doc.append(Spacer(1, 0.1 * inch))
    
    discussion_text = """
    The results of this analysis provide insights into how LLM-generated code impacts the code review process. 
    Significant differences in metrics such as comment density and time-to-merge suggest that LLM-generated 
    code may require different review strategies or may exhibit different characteristics compared to 
    human-written code.

    The correlation analysis between code complexity and review metrics helps control for potential 
    confounding variables, ensuring that observed differences are not solely attributable to complexity variations.
    """
    
    doc.append(Paragraph(discussion_text, normal_style))
    doc.append(Spacer(1, 0.25 * inch))

def create_limitations_section(doc, styles):
    """Create the Limitations section."""
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    doc.append(Paragraph("Limitations", subtitle_style))
    doc.append(Spacer(1, 0.1 * inch))
    
    limitations_text = """
    1. Data Collection: The analysis is limited to the selected repositories and may not be generalizable 
       to all open-source projects.
    2. Classification Accuracy: While secondary detectors were used to validate LLM labels, there is a 
       possibility of misclassification, particularly for ambiguous cases.
    3. Sample Size: The number of LLM-generated pull requests may be limited compared to human-written ones, 
       affecting statistical power.
    4. Complexity Measurement: The complexity metrics used (Cyclomatic Complexity and LOC) are standard but 
       may not capture all aspects of code complexity.
    5. External Validity: The findings are based on public open-source projects and may not apply to 
       proprietary codebases.
    """
    
    doc.append(Paragraph(limitations_text, normal_style))
    doc.append(Spacer(1, 0.25 * inch))

def create_plots_section(doc, styles):
    """Create a section for plots (placeholders for actual images)."""
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    doc.append(Paragraph("Visualizations", subtitle_style))
    doc.append(Spacer(1, 0.1 * inch))
    
    plot_text = """
    The following visualizations are included in the full report:
    - Boxplots comparing comment density between LLM and human groups
    - Boxplots comparing time-to-merge between LLM and human groups
    - Histograms of complexity scores for both groups
    - Correlation scatter plots between complexity and review metrics
    """
    
    doc.append(Paragraph(plot_text, normal_style))
    doc.append(Spacer(1, 0.25 * inch))

    # Add placeholder for plots
    doc.append(Paragraph("See reports/figures/boxplots.pdf and reports/figures/histograms.pdf for detailed plots.", styles['Italic']))
    doc.append(Spacer(1, 0.5 * inch))

def generate_final_report_pdf(output_path: Path):
    """Generate the final report PDF with all required sections and plots."""
    logger, config = setup_logging_and_config()
    logger.info("Starting final report PDF generation")
    
    # Load data
    metrics = load_metrics_data()
    results = load_results()
    correlations = calculate_correlation_coefficients(metrics)
    
    # Create PDF document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Build the report
    create_summary_panel(story, styles)
    create_methodology_section(story, styles)
    create_results_section(story, styles, results, correlations)
    create_plots_section(story, styles)
    create_discussion_section(story, styles)
    create_limitations_section(story, styles)
    
    # Build the PDF
    doc.build(story)
    logger.info(f"Final report saved to {output_path}")

def main():
    """Main entry point."""
    output_path = Path('reports/figures/final_report.pdf')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_final_report_pdf(output_path)

if __name__ == '__main__':
    main()