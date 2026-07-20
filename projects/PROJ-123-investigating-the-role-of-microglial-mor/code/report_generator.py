import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime

from code.config import get_path, ensure_dirs, get_project_root

def load_regression_results(results_path: str) -> Dict[str, Any]:
    """
    Load regression results from a JSON file.
    
    Args:
        results_path: Path to the regression results JSON file.
        
    Returns:
        Dictionary containing regression results.
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Regression results file not found: {results_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_vif_check(vif_path: str) -> Dict[str, Any]:
    """
    Load VIF check results from a JSON file.
    
    Args:
        vif_path: Path to the VIF check JSON file.
        
    Returns:
        Dictionary containing VIF check results.
    """
    path = Path(vif_path)
    if not path.exists():
        raise FileNotFoundError(f"VIF check file not found: {vif_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def determine_causality_warning(metadata: Dict[str, Any]) -> bool:
    """
    Determine if a causality warning should be included based on metadata.
    
    Args:
        metadata: Dictionary containing metadata about the analysis.
        
    Returns:
        True if causality warning is needed, False otherwise.
    """
    randomized = metadata.get('randomized', False)
    return not randomized

def generate_markdown_report(
    regression_results: Dict[str, Any],
    vif_check: Dict[str, Any],
    causality_warning: bool,
    output_path: str
) -> None:
    """
    Generate a markdown report from regression results.
    
    Args:
        regression_results: Dictionary containing regression results.
        vif_check: Dictionary containing VIF check results.
        causality_warning: Whether to include a causality warning.
        output_path: Path to write the markdown report.
    """
    lines = []
    lines.append("# Regression Analysis Results")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    if causality_warning:
        lines.append("## ⚠️ Causality Warning")
        lines.append("")
        lines.append("Associational findings only; causality not inferred.")
        lines.append("")
    
    lines.append("## Model Summary")
    lines.append("")
    lines.append("### Regression Coefficients")
    lines.append("")
    lines.append("| Feature | Coefficient | Std Error | t-value | P-value |")
    lines.append("|---------|-------------|-----------|---------|---------|")
    
    coefficients = regression_results.get('coefficients', {})
    for feature, coef_data in coefficients.items():
        lines.append(
            f"| {feature} | {coef_data['coef']:.4f} | {coef_data['std_err']:.4f} | "
            f"{coef_data['t_value']:.4f} | {coef_data['p_value']:.4f} |"
        )
    lines.append("")
    
    lines.append("### Interaction Terms")
    lines.append("")
    interaction_terms = regression_results.get('interaction_terms', {})
    if interaction_terms:
        for term, coef_data in interaction_terms.items():
            lines.append(
                f"- **{term}**: Coefficient = {coef_data['coef']:.4f}, "
                f"P-value = {coef_data['p_value']:.4f}"
            )
    else:
        lines.append("No significant interaction terms found.")
    lines.append("")
    
    lines.append("### VIF Analysis")
    lines.append("")
    lines.append(f"**Max VIF:** {vif_check.get('max_vif', 'N/A'):.4f}")
    lines.append(f"**PCA Triggered:** {vif_check.get('trigger_pca', False)}")
    lines.append("")
    
    vif_scores = vif_check.get('vif_scores', {})
    if vif_scores:
        lines.append("| Feature | VIF Score |")
        lines.append("|---------|-----------|")
        for feature, vif in vif_scores.items():
            lines.append(f"| {feature} | {vif:.4f} |")
        lines.append("")
    
    lines.append("### Model Fit Metrics")
    lines.append("")
    r2 = regression_results.get('r2', 0)
    adj_r2 = regression_results.get('adj_r2', 0)
    f_stat = regression_results.get('f_statistic', 0)
    p_value_f = regression_results.get('f_pvalue', 0)
    
    lines.append(f"- **R²:** {r2:.4f}")
    lines.append(f"- **Adjusted R²:** {adj_r2:.4f}")
    lines.append(f"- **F-statistic:** {f_stat:.4f}")
    lines.append(f"- **F-test p-value:** {p_value_f:.4f}")
    lines.append("")
    
    lines.append("## Conclusion")
    lines.append("")
    lines.append("This analysis examined the relationship between microglial morphological features "
               "and cognitive decline in the context of Alzheimer's pathology. The model included "
               "interaction terms between pathology status and brain region to assess whether the "
               "effect of morphology on cognition varies by anatomical location.")
    lines.append("")
    
    # Save to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

def generate_json_report(
    regression_results: Dict[str, Any],
    vif_check: Dict[str, Any],
    causality_warning: bool,
    output_path: str
) -> None:
    """
    Generate a JSON report from regression results.
    
    Args:
        regression_results: Dictionary containing regression results.
        vif_check: Dictionary containing VIF check results.
        causality_warning: Whether to include a causality warning.
        output_path: Path to write the JSON report.
    """
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'causality_warning': causality_warning
        },
        'regression_results': regression_results,
        'vif_analysis': vif_check
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def run_report_pipeline(
    regression_results_path: str,
    vif_check_path: str,
    metadata: Dict[str, Any],
    output_json_path: str,
    output_md_path: str
) -> None:
    """
    Run the full report generation pipeline.
    
    Args:
        regression_results_path: Path to the regression results JSON file.
        vif_check_path: Path to the VIF check JSON file.
        metadata: Dictionary containing metadata about the analysis.
        output_json_path: Path to write the JSON report.
        output_md_path: Path to write the markdown report.
    """
    # Load inputs
    regression_results = load_regression_results(regression_results_path)
    vif_check = load_vif_check(vif_check_path)
    
    # Determine causality warning
    causality_warning = determine_causality_warning(metadata)
    
    # Ensure output directories exist
    ensure_dirs(Path(output_json_path).parent)
    ensure_dirs(Path(output_md_path).parent)
    
    # Generate reports
    generate_json_report(
        regression_results,
        vif_check,
        causality_warning,
        output_json_path
    )
    
    generate_markdown_report(
        regression_results,
        vif_check,
        causality_warning,
        output_md_path
    )

def main() -> None:
    """Main entry point for the report generation pipeline."""
    import logging
    from code.config import get_path, load_config
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    config = load_config()
    
    # Define paths
    regression_results_path = get_path(config, 'regression_results_json')
    vif_check_path = get_path(config, 'vif_check_json')
    
    output_json_path = get_path(config, 'regression_results_json_output')
    output_md_path = get_path(config, 'regression_results_md_output')
    
    # Load metadata from config or a separate file if available
    metadata = config.get('metadata', {})
    
    logger.info("Starting report generation pipeline...")
    logger.info(f"Regression results: {regression_results_path}")
    logger.info(f"VIF check: {vif_check_path}")
    logger.info(f"JSON output: {output_json_path}")
    logger.info(f"Markdown output: {output_md_path}")
    
    try:
        run_report_pipeline(
            regression_results_path,
            vif_check_path,
            metadata,
            output_json_path,
            output_md_path
        )
        logger.info("Report generation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during report generation: {e}")
        raise

if __name__ == '__main__':
    main()