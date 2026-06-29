import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import get_config
from logging_config import setup_logging, get_logger

# Initialize logger
setup_logging()
logger = get_logger(__name__)

def load_template(template_path: str) -> str:
    """Load the Markdown report template."""
    if not os.path.exists(template_path):
        logger.error(f"Template not found at {template_path}")
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def format_correlation_table(results: List[Dict[str, Any]]) -> str:
    """Format correlation results into a Markdown table."""
    if not results:
        return "No correlation results available."
    
    headers = ["Metric", "Correlation (r)", "p-value", "FDR (q)", "Significant"]
    rows = []
    for res in results:
        sig = "Yes" if res.get('significant', False) else "No"
        rows.append([
            res['metric_name'],
            f"{res['r']:.4f}",
            f"{res['p']:.4f}",
            f"{res['q']:.4f}",
            sig
        ])
    
    # Create Markdown table
    table_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]
    for row in rows:
        table_lines.append("| " + " | ".join(row) + " |")
    
    return "\n".join(table_lines)

def format_power_analysis(power_report: str) -> str:
    """Format power analysis report."""
    return power_report if power_report else "Power analysis not available."

def format_plots(plots_dir: str) -> str:
    """Generate Markdown image references for plots."""
    if not os.path.exists(plots_dir):
        return "No plots generated."
    
    plot_files = []
    for f in os.listdir(plots_dir):
        if f.endswith(('.png', '.pdf')):
            plot_files.append(f)
    
    if not plot_files:
        return "No plot files found."
    
    md_refs = []
    for plot in sorted(plot_files):
        md_refs.append(f"![{plot}]({plot})")
    
    return "\n\n".join(md_refs)

def generate_conclusion(results: List[Dict[str, Any]], power_report: str) -> str:
    """Generate the conclusion section with required phrasing."""
    significant_count = sum(1 for r in results if r.get('significant', False))
    total_count = len(results)
    
    conclusion_parts = []
    
    if significant_count > 0:
        conclusion_parts.append(
            f"We found {significant_count} out of {total_count} network metrics showing a statistically significant "
            f"associational relationship with sensorimotor performance after FDR correction."
        )
    else:
        conclusion_parts.append(
            f"No network metrics showed a statistically significant correlational evidence with sensorimotor performance "
            f"after FDR correction (0 out of {total_count})."
        )
    
    if significant_count > 0:
        conclusion_parts.append(
            "This suggests that specific patterns of brain network dynamics may be linked to individual differences "
            "in sensorimotor capabilities."
        )
    
    conclusion_parts.append(
        "However, these findings represent an associational relationship and do not imply causation."
    )
    
    return " ".join(conclusion_parts)

def generate_report(
    correlation_results: List[Dict[str, Any]],
    power_analysis_text: str,
    plots_dir: str,
    template_path: str,
    output_path: str
) -> None:
    """
    Generate the final Markdown report by substituting template variables.
    
    Args:
        correlation_results: List of correlation result dictionaries
        power_analysis_text: Formatted power analysis text
        plots_dir: Directory containing generated plot files
        template_path: Path to the Markdown template
        output_path: Path where the final report will be saved
    """
    logger.info(f"Generating report from template: {template_path}")
    
    template = load_template(template_path)
    
    # Format sections
    correlation_table = format_correlation_table(correlation_results)
    power_section = format_power_analysis(power_analysis_text)
    plots_section = format_plots(plots_dir)
    
    # Generate conclusion with required phrasing
    conclusion = generate_conclusion(correlation_results, power_analysis_text)
    
    # Define limitations section
    limitations = (
        "## Limitations\n\n"
        "1. **Motor Task Performance is a proxy for proprioceptive accuracy.** The behavioral measure used "
        "in this study reflects motor task performance, which serves as an indirect indicator of proprioceptive "
        "ability. Direct proprioceptive measures were not available in the HCP dataset.\n\n"
        "2. **Cross-sectional design.** This study uses cross-sectional data, which limits causal inference "
        "about the direction of relationships between brain network dynamics and sensorimotor performance.\n\n"
        "3. **Sample characteristics.** The HCP sample consists of healthy young adults, which may limit "
        "generalizability to other age groups or clinical populations.\n\n"
        "4. **Multiple comparisons.** Despite FDR correction, the possibility of Type I and Type II errors "
        "remains in high-dimensional network analyses."
    )
    
    # Substitute variables
    report_content = template.replace("{{correlation_table}}", correlation_table)
    report_content = report_content.replace("{{power_analysis}}", power_section)
    report_content = report_content.replace("{{plots}}", plots_section)
    report_content = report_content.replace("{{limitations}}", limitations)
    
    # Insert conclusion if not already in template
    if "{{conclusion}}" in report_content:
        report_content = report_content.replace("{{conclusion}}", conclusion)
    else:
        # Append conclusion at the end if placeholder not found
        report_content += f"\n\n## Conclusion\n\n{conclusion}"
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Report successfully generated at: {output_path}")

def main() -> None:
    """Main entry point for report generation."""
    config = get_config()
    
    # Define paths
    data_dir = Path(config.get('DATA_DIR', 'data'))
    analysis_dir = data_dir / 'analysis'
    reports_dir = data_dir / 'reports'
    plots_dir = data_dir / 'analysis'  # Plots are typically saved in analysis dir
    template_path = Path('templates') / 'report_template.md'
    output_path = reports_dir / f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    
    # Load correlation results
    correlation_file = analysis_dir / 'correlation_results.csv'
    if not correlation_file.exists():
        logger.warning(f"Correlation results file not found: {correlation_file}")
        correlation_results = []
    else:
        df = pd.read_csv(correlation_file)
        correlation_results = df.to_dict('records')
    
    # Load power analysis
    power_file = analysis_dir / 'power_analysis.txt'
    if power_file.exists():
        with open(power_file, 'r') as f:
            power_analysis_text = f.read()
    else:
        logger.warning(f"Power analysis file not found: {power_file}")
        power_analysis_text = "Power analysis not available."
    
    # Ensure template exists
    if not template_path.exists():
        logger.error(f"Template not found at {template_path}")
        # Create a default template if missing
        template_path.parent.mkdir(parents=True, exist_ok=True)
        default_template = """# Brain Network Dynamics and Sensorimotor Performance Report

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Correlation Results

{correlation_table}

## Power Analysis

{power_analysis}

## Visualization Plots

{plots}

## Limitations

{limitations}
"""
        with open(template_path, 'w') as f:
            f.write(default_template)
        logger.info(f"Created default template at {template_path}")
    
    # Generate report
    generate_report(
        correlation_results=correlation_results,
        power_analysis_text=power_analysis_text,
        plots_dir=str(plots_dir),
        template_path=str(template_path),
        output_path=str(output_path)
    )

if __name__ == '__main__':
    main()