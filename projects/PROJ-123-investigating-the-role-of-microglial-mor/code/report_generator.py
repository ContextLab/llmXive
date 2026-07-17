import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from code.config import get_path, ensure_dirs
import logging

logger = logging.getLogger(__name__)

def load_regression_results() -> Optional[Dict[str, Any]]:
    """Load regression results from the JSON file."""
    json_path = get_path("reports", "regression_results.json")
    if not os.path.exists(json_path):
        logger.warning(f"Regression results file not found at {json_path}")
        return None
    
    with open(json_path, 'r') as f:
        return json.load(f)

def load_vif_check() -> Optional[Dict[str, Any]]:
    """Load VIF check results from the JSON file."""
    json_path = get_path("data", "intermediates", "vif_check.json")
    if not os.path.exists(json_path):
        logger.warning(f"VIF check file not found at {json_path}")
        return None
    
    with open(json_path, 'r') as f:
        return json.load(f)

def determine_causality_warning(metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Determine if a causality warning is needed based on metadata.
    
    Logic:
    - Check metadata['randomized'].
    - If True, causality_warning = False.
    - If False or missing, causality_warning = True.
    
    Returns:
        bool: True if warning is needed, False otherwise.
    """
    if metadata is None:
        return True
    
    randomized = metadata.get('randomized')
    if randomized is True:
        return False
    return True

def generate_markdown_report(
    regression_results: Dict[str, Any],
    vif_check: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate a Markdown report from regression results.
    
    Args:
        regression_results: Dictionary containing regression results.
        vif_check: Optional dictionary containing VIF check results.
        metadata: Optional dictionary containing study metadata (for causality check).
        output_path: Optional path to write the report. If None, returns the string.
    
    Returns:
        str: The generated Markdown report content.
    """
    # Determine causality warning
    causality_warning = determine_causality_warning(metadata)
    
    lines = []
    lines.append("# Regression Analysis Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Causality Warning Section
    lines.append("## Causality Warning")
    lines.append("")
    if causality_warning:
        lines.append("⚠️ **Associational findings only; causality not inferred**")
        lines.append("")
        lines.append("This study is observational. The metadata indicates the study was not randomized ")
        lines.append("or the randomized status is missing. Therefore, no causal inferences should be drawn ")
        lines.append("from the observed correlations.")
        lines.append("")
    else:
        lines.append("✅ **Causal inference permitted**")
        lines.append("")
        lines.append("The study design was randomized. Causal interpretations of the regression coefficients ")
        lines.append("are supported by the experimental design.")
        lines.append("")
    
    # Model Summary
    lines.append("## Model Summary")
    lines.append("")
    if 'model_summary' in regression_results:
        summary = regression_results['model_summary']
        lines.append(f"- **R² Score:** {summary.get('r2', 'N/A')}")
        lines.append(f"- **Adjusted R²:** {summary.get('adj_r2', 'N/A')}")
        lines.append(f"- **F-statistic:** {summary.get('f_statistic', 'N/A')}")
        lines.append(f"- **P-value (F-test):** {summary.get('f_pvalue', 'N/A')}")
    lines.append("")
    
    # Coefficients
    lines.append("## Regression Coefficients")
    lines.append("")
    lines.append("| Variable | Coefficient | Std Error | t-statistic | P-value | 95% CI |")
    lines.append("|----------|-------------|-----------|-------------|---------|--------|")
    
    if 'coefficients' in regression_results:
        coeffs = regression_results['coefficients']
        for var, data in coeffs.items():
            ci_lower = data.get('ci_lower', 'N/A')
            ci_upper = data.get('ci_upper', 'N/A')
            lines.append(f"| {var} | {data.get('coef', 'N/A'):.4f} | {data.get('std_err', 'N/A'):.4f} | {data.get('t_value', 'N/A'):.4f} | {data.get('pvalue', 'N/A'):.4f} | [{ci_lower}, {ci_upper}] |")
    lines.append("")
    
    # Interaction Terms
    if 'interaction_terms' in regression_results and regression_results['interaction_terms']:
        lines.append("## Interaction Terms")
        lines.append("")
        for term, data in regression_results['interaction_terms'].items():
            lines.append(f"- **{term}**: Coefficient = {data.get('coef', 'N/A'):.4f}, P-value = {data.get('pvalue', 'N/A'):.4f}")
        lines.append("")
    
    # VIF Scores
    if vif_check and 'vif_scores' in vif_check:
        lines.append("## Variance Inflation Factors (VIF)")
        lines.append("")
        lines.append("| Variable | VIF Score |")
        lines.append("|----------|-----------|")
        for var, vif in vif_check['vif_scores'].items():
            lines.append(f"| {var} | {vif:.4f} |")
        lines.append("")
        if vif_check.get('trigger_pca', False):
            lines.append("**Note:** PCA was applied due to high multicollinearity (VIF > 5).")
        else:
            lines.append("**Note:** No PCA was required as all VIF scores were below the threshold (5.0).")
        lines.append("")
    
    # Validation Metrics
    if 'validation_metrics' in regression_results:
        lines.append("## Validation Metrics")
        lines.append("")
        val = regression_results['validation_metrics']
        lines.append(f"- **Cross-validated R² (mean):** {val.get('r2_mean', 'N/A')}")
        lines.append(f"- **Cross-validated R² (std):** {val.get('r2_std', 'N/A')}")
        lines.append(f"- **Sensitivity Variation:** {val.get('sensitivity_variation', 'N/A')}")
        lines.append("")
    
    if output_path:
        ensure_dirs(output_path)
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        logger.info(f"Markdown report written to {output_path}")
    
    return '\n'.join(lines)

def generate_json_report(
    regression_results: Dict[str, Any],
    vif_check: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a JSON report from regression results.
    
    Args:
        regression_results: Dictionary containing regression results.
        vif_check: Optional dictionary containing VIF check results.
        metadata: Optional dictionary containing study metadata.
        output_path: Optional path to write the JSON report.
    
    Returns:
        dict: The generated JSON report content.
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "causality_warning": determine_causality_warning(metadata),
        "regression_results": regression_results,
        "vif_check": vif_check
    }
    
    if output_path:
        ensure_dirs(output_path)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"JSON report written to {output_path}")
    
    return report

def run_report_pipeline(
    regression_results: Optional[Dict[str, Any]] = None,
    vif_check: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Run the full report generation pipeline.
    
    Args:
        regression_results: Pre-loaded regression results (optional).
        vif_check: Pre-loaded VIF check (optional).
        metadata: Study metadata for causality check.
        output_dir: Directory to write reports (defaults to config).
    
    Returns:
        dict: Paths to generated reports.
    """
    if regression_results is None:
        regression_results = load_regression_results()
    
    if vif_check is None:
        vif_check = load_vif_check()
    
    if output_dir is None:
        output_dir = get_path("reports")
    
    json_path = os.path.join(output_dir, "regression_results.json")
    md_path = os.path.join(output_dir, "regression_results.md")
    
    # Generate JSON report
    generate_json_report(regression_results, vif_check, metadata, json_path)
    
    # Generate Markdown report
    generate_markdown_report(regression_results, vif_check, metadata, md_path)
    
    return {
        "json_report": json_path,
        "md_report": md_path
    }
