import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
from code.config import get_path, ensure_dirs
from code.analysis import run_regression_with_interaction
import logging

logger = logging.getLogger(__name__)

def load_regression_results() -> Optional[Dict[str, Any]]:
    """Load regression results from the analysis pipeline if available."""
    # The analysis pipeline is expected to have populated a temporary or intermediate
    # results structure, or we re-run the core regression logic to capture the state.
    # For this implementation, we assume the analysis pipeline returns the results
    # when called, or we load from a cached intermediate file if T027 saved one.
    # Based on T027 description, it generates the model. We will re-run the core
    # analysis to get the fresh results for the report, or load from a saved state.
    # To be robust, we will re-run the regression step to ensure data consistency
    # with the latest `morphological_metrics.csv` and `vif_check.json`.
    
    try:
        # Re-run the regression logic to get the latest results
        # This function is defined in code/analysis.py
        from code.analysis import run_regression_with_interaction
        results = run_regression_with_interaction()
        return results
    except Exception as e:
        logger.error(f"Failed to load or run regression results: {e}")
        return None

def load_vif_check() -> Optional[Dict[str, Any]]:
    """Load VIF check results from the intermediate file."""
    vif_path = get_path("data/intermediates/vif_check.json")
    if not vif_path or not os.path.exists(vif_path):
        logger.warning(f"VIF check file not found at {vif_path}")
        return None
    
    try:
        with open(vif_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse VIF check JSON: {e}")
        return None

def generate_json_report(regression_results: Dict[str, Any], vif_check: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate the structured JSON report."""
    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "pipeline_version": "1.0.0",
            "task_id": "T029"
        },
        "vif_analysis": vif_check,
        "regression_results": regression_results,
        "conclusion": "Analysis complete. See regression_results for coefficients and p-values."
    }
    return report

def generate_markdown_report(regression_results: Dict[str, Any], vif_check: Optional[Dict[str, Any]], causality_warning: bool) -> str:
    """Generate the Markdown report."""
    md_lines = [
        "# Regression Analysis Report: Microglial Morphology and Cognitive Decline",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Methodology",
        "This report presents the results of a multiple linear regression analysis predicting cognitive status",
        "based on microglial morphological metrics (branch points, total length, soma area, Sholl intersections).",
        "The model includes interaction terms between Pathology Status and Brain Region.",
        "",
        "## VIF Analysis"
    ]
    
    if vif_check:
        md_lines.append(f"- **PCA Triggered:** {vif_check.get('trigger_pca', False)}")
        md_lines.append(f"- **VIF Scores:** {vif_check.get('vif_scores', {})}")
        if vif_check.get('trigger_pca'):
            md_lines.append("- *Note: Multicollinearity was detected (VIF > 5.0). PCA was applied to generate orthogonal predictors.*")
        else:
            md_lines.append("- *No multicollinearity detected. Original predictors used.*")
    else:
        md_lines.append("- VIF check data not available.")
    
    md_lines.extend([
        "",
        "## Regression Results"
    ])
    
    if regression_results:
        coeffs = regression_results.get('coefficients', {})
        p_values = regression_results.get('p_values', {})
        interaction_terms = regression_results.get('interaction_terms', [])
        
        md_lines.append("### Coefficients")
        md_lines.append("| Variable | Coefficient | P-Value |")
        md_lines.append("|---|---|---|")
        for var, coef in coeffs.items():
            p_val = p_values.get(var, 'N/A')
            md_lines.append(f"| {var} | {coef:.4f} | {p_val:.4f} |")
        
        if interaction_terms:
            md_lines.extend([
                "",
                "### Interaction Terms"
            ])
            for term in interaction_terms:
                md_lines.append(f"- {term}")
        
        # Causality Warning
        if causality_warning:
            md_lines.extend([
                "",
                "## ⚠️ Causality Warning",
                "",
                "Associational findings only; causality not inferred. The study design was not randomized."
            ])
    else:
        md_lines.append("Regression results could not be computed or loaded.")
    
    md_lines.extend([
        "",
        "---",
        "*Report generated by llmXive automated science pipeline.*"
    ])
    
    return "\n".join(md_lines)

def run_report_pipeline() -> bool:
    """
    Main entry point for T029.
    1. Loads regression results.
    2. Loads VIF check.
    3. Determines causality warning flag (from T028 logic).
    4. Generates JSON and Markdown reports.
    5. Writes to reports/regression_results.json and reports/regression_results.md
    """
    logger.info("Starting report generation pipeline (T029)...")
    
    # Ensure output directory exists
    output_dir = get_path("reports")
    if output_dir:
        ensure_dirs(output_dir)
    else:
        logger.error("Could not determine reports directory path.")
        return False

    # Load Data
    regression_results = load_regression_results()
    vif_check = load_vif_check()

    if not regression_results:
        logger.error("Failed to retrieve regression results. Cannot generate report.")
        return False

    # Determine Causality Warning
    # T028 logic: Check metadata['randomized']. If False or missing, set warning.
    # We need to check the global config or a metadata file. 
    # Assuming the config or a global state holds this. 
    # Based on T028 description, we check a flag. Let's assume we read from a config 
    # or a specific metadata file if it exists, otherwise default to True (observational).
    causality_warning = True 
    try:
        from code.config import load_config
        config = load_config()
        # Check if a 'randomized' flag exists in the analysis config or metadata
        if config and 'analysis' in config:
            if config['analysis'].get('randomized', False):
                causality_warning = False
        # Also check if there's a specific metadata file
        # If not found, default to True (observational study)
    except Exception:
        pass

    # Generate Reports
    json_report = generate_json_report(regression_results, vif_check)
    md_report = generate_markdown_report(regression_results, vif_check, causality_warning)

    # Write JSON
    json_path = os.path.join(output_dir, "regression_results.json")
    try:
        with open(json_path, 'w') as f:
            json.dump(json_report, f, indent=2)
        logger.info(f"JSON report written to {json_path}")
    except Exception as e:
        logger.error(f"Failed to write JSON report: {e}")
        return False

    # Write Markdown
    md_path = os.path.join(output_dir, "regression_results.md")
    try:
        with open(md_path, 'w') as f:
            f.write(md_report)
        logger.info(f"Markdown report written to {md_path}")
    except Exception as e:
        logger.error(f"Failed to write Markdown report: {e}")
        return False

    logger.info("Report generation pipeline completed successfully.")
    return True

if __name__ == "__main__":
    # Setup logging if not already done
    logging.basicConfig(level=logging.INFO)
    run_report_pipeline()
