import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from analyze import (
    load_spot_check_validation_rate,
    save_statistical_results,
    load_processed_data,
    calculate_descriptive_statistics,
    perform_stratified_mwu_test,
    calculate_effect_size_r,
    calculate_medians,
    calculate_distribution_characteristics,
    calculate_shapiro_wilk
)
from visualize import generate_boxplot, prepare_boxplot_data, load_outlier_indices
from utils import validate_json_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_spot_check_results(filepath: str) -> Dict[str, Any]:
    """
    Load spot-check validation results from CSV.
    Calculates false_negative_rate based on misclassified AI PRs in the non-AI sample.
    
    Args:
        filepath: Path to validation_report.csv
        
    Returns:
        Dictionary containing false_negative_rate and other validation metrics
    """
    import csv
    results = {
        'false_negative_rate': 0.0,
        'total_sample_size': 0,
        'misclassified_ai_count': 0
    }
    
    if not os.path.exists(filepath):
        logger.error(f"Spot check results file not found: {filepath}")
        return results
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        if not rows:
            logger.warning("Spot check results file is empty")
            return results
        
        results['total_sample_size'] = len(rows)
        misclassified_count = sum(
            1 for row in rows 
            if row.get('actual_classification') == 'AI' and row.get('predicted_classification') == 'Non-AI'
        )
        results['misclassified_ai_count'] = misclassified_count
        
        if results['total_sample_size'] > 0:
            results['false_negative_rate'] = misclassified_count / results['total_sample_size']
        
        logger.info(f"Spot check loaded: {results['total_sample_size']} samples, "
                   f"{misclassified_count} misclassified AI, "
                   f"false_negative_rate: {results['false_negative_rate']:.4f}")
                   
    except Exception as e:
        logger.error(f"Error loading spot check results: {e}")
        raise
    
    return results

def assemble_report(
    statistical_results: Dict[str, Any],
    spot_check_results: Dict[str, Any],
    boxplot_path: str,
    output_path: str
) -> None:
    """
    Assemble the final research report including statistical results,
    visualization references, and conditional limitation statements.
    
    Args:
        statistical_results: Dict from T029 containing MWU test results
        spot_check_results: Dict from load_spot_check_results()
        boxplot_path: Path to the generated boxplot image
        output_path: Path where final_report.md will be saved
    """
    # Extract key metrics
    p_value = statistical_results.get('p_value', 0.0)
    u_statistic = statistical_results.get('u_statistic', 0.0)
    effect_size = statistical_results.get('effect_size', 0.0)
    sample_sizes = statistical_results.get('sample_sizes', {})
    ai_count = sample_sizes.get('ai', 0)
    non_ai_count = sample_sizes.get('non_ai', 0)
    
    # Descriptive statistics
    desc_stats = statistical_results.get('descriptive_statistics', {})
    ai_median = desc_stats.get('ai', {}).get('median', 0)
    non_ai_median = desc_stats.get('non_ai', {}).get('median', 0)
    
    # Distribution characteristics
    dist_chars = statistical_results.get('distribution_characteristics', {})
    ai_skew = dist_chars.get('ai', {}).get('skewness', 0)
    non_ai_skew = dist_chars.get('non_ai', {}).get('skewness', 0)
    
    # Shapiro-Wilk results
    shapiro_results = statistical_results.get('shapiro_wilk', {})
    ai_shapiro_p = shapiro_results.get('ai', {}).get('p_value', 0)
    non_ai_shapiro_p = shapiro_results.get('non_ai', {}).get('p_value', 0)
    
    # Median repository stats
    median_stars = statistical_results.get('median_stars', 0)
    median_contributors = statistical_results.get('median_contributors', 0)
    
    # False negative rate from spot check
    false_negative_rate = spot_check_results.get('false_negative_rate', 0.0)
    total_sample_size = spot_check_results.get('total_sample_size', 0)
    misclassified_count = spot_check_results.get('misclassified_ai_count', 0)
    
    # Build report content
    report_lines = [
        "# Research Report: Impact of Code Generation on PR Turnaround Time",
        "",
        "## Executive Summary",
        "",
        "This report presents the findings of a statistical analysis comparing the turnaround times",
        "of AI-assisted pull requests versus non-AI pull requests across top Python and JavaScript repositories.",
        "",
        "## Methodology",
        "",
        "### Data Collection",
        f"- Repositories analyzed: Top Python and JS repos by star count",
        f"- Median repository stars: {median_stars:.0f}",
        f"- Median repository contributors: {median_contributors:.0f}",
        "",
        "### Statistical Analysis",
        "- Test: Stratified Mann-Whitney U test (non-parametric)",
        "- Stratification: PR size and author activity",
        "- Significance threshold: α = 0.05",
        "",
        "## Results",
        "",
        "### Sample Sizes",
        f"- AI-assisted PRs: {ai_count}",
        f"- Non-AI PRs: {non_ai_count}",
        f"- Total PRs analyzed: {ai_count + non_ai_count}",
        "",
        "### Descriptive Statistics (Turnaround Time in Hours)",
        "",
        "| Group | Median | Mean | Std Dev |",
        "|-------|--------|------|---------|",
        f"| AI-assisted | {ai_median:.2f} | {desc_stats.get('ai', {}).get('mean', 0):.2f} | {desc_stats.get('ai', {}).get('std_dev', 0):.2f} |",
        f"| Non-AI | {non_ai_median:.2f} | {desc_stats.get('non_ai', {}).get('mean', 0):.2f} | {desc_stats.get('non_ai', {}).get('std_dev', 0):.2f} |",
        "",
        "### Distribution Characteristics",
        "",
        "Shapiro-Wilk Normality Test:",
        f"- AI group p-value: {ai_shapiro_p:.4f}",
        f"- Non-AI group p-value: {non_ai_shapiro_p:.4f}",
        "",
        "Skewness:",
        f"- AI group: {ai_skew:.4f}",
        f"- Non-AI group: {non_ai_skew:.4f}",
        "",
        "### Statistical Test Results",
        "",
        f"- U-statistic: {u_statistic:.2f}",
        f"- P-value: {p_value:.6f}",
        f"- Effect size (r): {effect_size:.4f}",
        "",
        "#### Conclusion",
        f"{'Significant difference found' if p_value < 0.05 else 'No significant difference found'} "
        f"between AI-assisted and non-AI PR turnaround times (p = {p_value:.4f}).",
        "",
        "### Visualization",
        "",
        f"![Boxplot of Turnaround Times]({os.path.basename(boxplot_path)})",
        "",
        "## Validation and Quality Assurance",
        "",
        "### Spot Check Results",
        f"- Sample size: {total_sample_size}",
        f"- Misclassified AI PRs in non-AI group: {misclassified_count}",
        f"- False negative rate: {false_negative_rate * 100:.2f}%",
        "",
    ]
    
    # T035: Conditional limitation injection
    if false_negative_rate > 0.10:
        limitation_text = (
            "## Limitations\n\n"
            "Limitation: False-negative rate exceeds 10% threshold, indicating potential misclassification in non-AI group.\n\n"
            "This suggests that some AI-assisted PRs may have been incorrectly classified as non-AI, "
            "which could bias the statistical comparison. Future work should improve classification accuracy "
            "through additional features or manual verification."
        )
        report_lines.append(limitation_text)
    else:
        report_lines.extend([
            "## Limitations",
            "",
            "The classification accuracy was within acceptable thresholds (false negative rate ≤ 10%).",
            "No major limitations regarding misclassification were identified.",
            ""
        ])
    
    # Add sensitivity analysis results if available
    if 'adjusted_p_value' in statistical_results:
        report_lines.extend([
            "### Sensitivity Analysis",
            "",
            f"Adjusted p-value (bias-corrected): {statistical_results['adjusted_p_value']:.6f}",
            f"Original p-value: {p_value:.6f}",
            "",
        ])
    
    report_lines.extend([
        "## References",
        "",
        "1. Mann-Whitney U test methodology for non-parametric hypothesis testing",
        "2. IQR-based outlier detection for visualization purposes",
        "3. Stratified sampling for robust statistical comparison",
        "",
        "## Appendix",
        "",
        "### Data Quality Metrics",
        f"- Data quality success rate: {statistical_results.get('data_quality_rate', 'N/A')}",
        "",
    ])
    
    # Write report to file
    report_content = "\n".join(report_lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Final report assembled and saved to: {output_path}")

def main():
    """
    Main entry point for the report generation pipeline.
    
    Steps:
    1. Load statistical results from T029
    2. Load spot check validation results from T020
    3. Generate boxplot (T031) if not already done
    4. Assemble final report with conditional limitation (T035)
    5. Save report to artifacts/final_report.md
    """
    base_path = Path(__file__).parent.parent
    data_path = base_path / 'data'
    artifacts_path = base_path / 'artifacts'
    
    # Ensure output directory exists
    artifacts_path.mkdir(parents=True, exist_ok=True)
    
    # Load statistical results (T029)
    stat_results_path = data_path / 'processed' / 'statistical_results.json'
    if not stat_results_path.exists():
        logger.error(f"Statistical results file not found: {stat_results_path}")
        raise FileNotFoundError(f"Missing statistical results: {stat_results_path}")
    
    with open(stat_results_path, 'r', encoding='utf-8') as f:
        statistical_results = json.load(f)
    
    logger.info("Loaded statistical results")
    
    # Load spot check results (T020)
    spot_check_path = data_path / 'spot_check' / 'validation_report.csv'
    spot_check_results = load_spot_check_results(str(spot_check_path))
    
    # Generate boxplot if not exists (T031, T033)
    boxplot_path = artifacts_path / 'boxplot.png'
    if not boxplot_path.exists():
        logger.info("Boxplot not found, generating...")
        # Import and run visualize module
        from visualize import main as run_visualize
        run_visualize()
    
    # Assemble final report (T034, T035, T036)
    report_path = artifacts_path / 'final_report.md'
    assemble_report(
        statistical_results=statistical_results,
        spot_check_results=spot_check_results,
        boxplot_path=str(boxplot_path),
        output_path=str(report_path)
    )
    
    logger.info("Report generation pipeline completed successfully")
    return 0

if __name__ == '__main__':
    exit(main())