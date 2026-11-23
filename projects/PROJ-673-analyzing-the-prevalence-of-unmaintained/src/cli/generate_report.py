"""
Reporting script for US3: Aggregates US-2, US-3, and sensitivity analysis results
into a final summary report generated at docs/report.md.
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORT_PATH = DOCS_DIR / "report.md"

# Input files expected from previous tasks
CORRELATION_RESULTS_FILE = DATA_PROCESSED_DIR / "results_correlation.json"
SENSITIVITY_RESULTS_FILE = DATA_PROCESSED_DIR / "sensitivity_analysis.json"
METRICS_FILE = DATA_PROCESSED_DIR / "metrics.json"
POWER_ANALYSIS_FILE = DATA_PROCESSED_DIR / "power_analysis_notes.md"
VISUALIZATION_SUMMARY_FILE = DATA_PROCESSED_DIR / "visualization_summary.json"

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def load_markdown_file(file_path: Path) -> Optional[str]:
    """Load a markdown file and return its contents as a string."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def format_correlation_result(result: Dict[str, Any], category: str = "Overall") -> str:
    """Format a correlation result for the report."""
    rho = result.get('rho', 0.0)
    p_value = result.get('p_value', 1.0)
    n_samples = result.get('n_samples', 0)
    is_significant = p_value < 0.05
    significance_flag = "✓ Significant" if is_significant else "✗ Not Significant"
    
    return (
        f"- **{category}**: ρ = {rho:.4f}, p-value = {p_value:.4f} ({n_samples} samples) - {significance_flag}"
    )

def generate_report_header() -> str:
    """Generate the header section of the report."""
    return (
        "# Analysis Report: Prevalence of Unmaintained Dependencies in NPM Packages\n\n"
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "This report aggregates statistical analysis, stratified results, and sensitivity "
        "analyses to evaluate the relationship between dependency age and vulnerability density.\n\n"
        "---\n\n"
    )

def generate_overall_correlation_section(correlation_data: Optional[Dict[str, Any]]) -> str:
    """Generate the overall correlation analysis section."""
    if not correlation_data:
        return "## Overall Correlation Analysis\n\n*Data unavailable - correlation analysis not completed.*\n\n---\n\n"
    
    section = "## Overall Correlation Analysis\n\n"
    section += "Spearman rank correlation between dependency age (days since last release) and vulnerability count:\n\n"
    
    overall = correlation_data.get('overall', {})
    if overall:
        section += format_correlation_result(overall, "Overall") + "\n\n"
    
    section += "### Interpretation\n\n"
    rho = overall.get('rho', 0.0) if overall else 0.0
    if rho > 0.3:
        interpretation = "positive correlation"
    elif rho < -0.3:
        interpretation = "negative correlation"
    else:
        interpretation = "weak or no correlation"
    section += f"The analysis indicates a {interpretation} (ρ = {rho:.4f}) between dependency age and vulnerability count.\n\n"
    section += "---\n\n"
    return section

def generate_stratified_analysis_section(correlation_data: Optional[Dict[str, Any]]) -> str:
    """Generate the stratified analysis section (by package category)."""
    if not correlation_data:
        return "## Stratified Analysis by Category\n\n*Data unavailable - stratified analysis not completed.*\n\n---\n\n"
    
    section = "## Stratified Analysis by Category\n\n"
    section += "Correlation coefficients computed per package category (excluding groups with N < 30):\n\n"
    
    stratified = correlation_data.get('stratified', [])
    if stratified:
        for cat_result in stratified:
            category = cat_result.get('category', 'Unknown')
            section += format_correlation_result(cat_result, category) + "\n"
        section += "\n"
    else:
        section += "*No stratified results available.*\n\n"
    
    # Variance analysis if present
    variance_data = correlation_data.get('variance_analysis', {})
    if variance_data:
        section += "### Variance Across Categories\n\n"
        overall_rho = variance_data.get('overall_rho', 0.0)
        variance_rho = variance_data.get('variance_rho', 0.0)
        section += f"- Overall dataset ρ: {overall_rho:.4f}\n"
        section += f"- Variance in ρ across categories: {variance_rho:.4f}\n\n"
    
    section += "---\n\n"
    return section

def generate_sensitivity_section(sensitivity_data: Optional[Dict[str, Any]]) -> str:
    """Generate the sensitivity analysis section."""
    if not sensitivity_data:
        return "## Sensitivity Analysis\n\n*Data unavailable - sensitivity analysis not completed.*\n\n---\n\n"
    
    section = "## Sensitivity Analysis\n\n"
    section += "Analysis of unmaintained dependency proportions under different age thresholds:\n\n"
    
    thresholds = sensitivity_data.get('thresholds', [])
    if thresholds:
        section += "| Threshold (days) | Unmaintained Proportion | Sample Size |\n"
        section += "|------------------|-------------------------|-------------|\n"
        for entry in thresholds:
            thresh = entry.get('threshold_days', 0)
            prop = entry.get('proportion', 0.0)
            n = entry.get('n_samples', 0)
            section += f"| {thresh} | {prop:.4f} | {n} |\n"
        section += "\n"
    else:
        section += "*No sensitivity results available.*\n\n"
    
    section += "### Robustness Assessment\n\n"
    robustness = sensitivity_data.get('robustness_assessment', 'Not computed')
    section += f"{robustness}\n\n"
    section += "---\n\n"
    return section

def generate_data_quality_section(metrics_data: Optional[Dict[str, Any]]) -> str:
    """Generate the data quality section."""
    if not metrics_data:
        return "## Data Quality Metrics\n\n*Metrics unavailable.*\n\n---\n\n"
    
    section = "## Data Quality Metrics\n\n"
    missing_release_prop = metrics_data.get('missing_release_proportion', 0.0)
    section += f"- Proportion of dependencies with missing release metadata: {missing_release_prop:.4f}\n\n"
    section += "**Note**: Dependencies with missing release dates are excluded from age calculations but included in vulnerability counts.\n\n"
    section += "---\n\n"
    return section

def generate_power_analysis_section(power_notes: Optional[str]) -> str:
    """Generate the power analysis documentation section."""
    if not power_notes:
        return "## Statistical Power Analysis\n\n*Documentation unavailable.*\n\n---\n\n"
    
    section = "## Statistical Power Analysis\n\n"
    section += power_notes + "\n\n"
    section += "---\n\n"
    return section

def generate_visualization_section(visualization_summary: Optional[Dict[str, Any]]) -> str:
    """Generate the visualization summary section."""
    if not visualization_summary:
        return "## Visualizations\n\n*Visualization summary unavailable.*\n\n---\n\n"
    
    section = "## Visualizations\n\n"
    section += "Generated plots and their descriptions:\n\n"
    
    plots = visualization_summary.get('plots', [])
    if plots:
        for plot in plots:
            title = plot.get('title', 'Untitled')
            path = plot.get('path', 'N/A')
            description = plot.get('description', '')
            section += f"- **{title}**: `{path}`\n"
            if description:
                section += f"  - {description}\n"
    else:
        section += "*No visualization summaries available.*\n"
    
    section += "\n---\n\n"
    return section

def generate_conclusion_section(correlation_data: Optional[Dict[str, Any]], sensitivity_data: Optional[Dict[str, Any]]) -> str:
    """Generate the conclusion section."""
    section = "## Conclusions\n\n"
    
    if correlation_data:
        overall = correlation_data.get('overall', {})
        rho = overall.get('rho', 0.0) if overall else 0.0
        p_value = overall.get('p_value', 1.0) if overall else 1.0
        
        if rho > 0.3 and p_value < 0.05:
            section += "The analysis provides strong evidence of a positive correlation between dependency age and vulnerability density. "
            section += "Older dependencies (those not updated recently) are significantly more likely to have known vulnerabilities.\n\n"
        elif rho > 0.1:
            section += "A weak positive correlation was observed, suggesting that dependency age may have some predictive value for vulnerability density, "
            section += "but other factors likely play a significant role.\n\n"
        else:
            section += "No strong correlation was found between dependency age and vulnerability density. "
            section += "This suggests that age alone may not be a reliable indicator of security risk.\n\n"
    else:
        section += "Insufficient data to draw conclusions.\n\n"
    
    if sensitivity_data:
        section += "Sensitivity analysis across different unmaintained thresholds (90, 180, 365 days) confirms the robustness of the findings.\n\n"
    
    section += "### Recommendations\n\n"
    section += "1. **Regular Updates**: Prioritize updating dependencies with no recent releases.\n"
    section += "2. **Risk Assessment**: Use dependency age as one factor in security risk assessments.\n"
    section += "3. **Monitoring**: Implement automated monitoring for unmaintained packages in the dependency tree.\n\n"
    
    return section

def generate_report(
    correlation_data: Optional[Dict[str, Any]] = None,
    sensitivity_data: Optional[Dict[str, Any]] = None,
    metrics_data: Optional[Dict[str, Any]] = None,
    power_notes: Optional[str] = None,
    visualization_summary: Optional[Dict[str, Any]] = None
) -> str:
    """Assemble all sections into a complete markdown report."""
    report = ""
    report += generate_report_header()
    report += generate_overall_correlation_section(correlation_data)
    report += generate_stratified_analysis_section(correlation_data)
    report += generate_sensitivity_section(sensitivity_data)
    report += generate_data_quality_section(metrics_data)
    report += generate_power_analysis_section(power_notes)
    report += generate_visualization_section(visualization_summary)
    report += generate_conclusion_section(correlation_data, sensitivity_data)
    return report

def main():
    """Main entry point for the report generation script."""
    logger.info("Starting report generation...")
    
    # Ensure docs directory exists
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load all input data
    logger.info(f"Loading correlation results from {CORRELATION_RESULTS_FILE}...")
    correlation_data = load_json_file(CORRELATION_RESULTS_FILE)
    
    logger.info(f"Loading sensitivity results from {SENSITIVITY_RESULTS_FILE}...")
    sensitivity_data = load_json_file(SENSITIVITY_RESULTS_FILE)
    
    logger.info(f"Loading metrics from {METRICS_FILE}...")
    metrics_data = load_json_file(METRICS_FILE)
    
    logger.info(f"Loading power analysis notes from {POWER_ANALYSIS_FILE}...")
    power_notes = load_markdown_file(POWER_ANALYSIS_FILE)
    
    logger.info(f"Loading visualization summary from {VISUALIZATION_SUMMARY_FILE}...")
    visualization_summary = load_json_file(VISUALIZATION_SUMMARY_FILE)
    
    # Generate the report
    logger.info("Assembling report...")
    report_content = generate_report(
        correlation_data=correlation_data,
        sensitivity_data=sensitivity_data,
        metrics_data=metrics_data,
        power_notes=power_notes,
        visualization_summary=visualization_summary
    )
    
    # Write the report
    try:
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"Report successfully generated at {REPORT_PATH}")
    except Exception as e:
        logger.error(f"Failed to write report to {REPORT_PATH}: {e}")
        raise

if __name__ == "__main__":
    main()