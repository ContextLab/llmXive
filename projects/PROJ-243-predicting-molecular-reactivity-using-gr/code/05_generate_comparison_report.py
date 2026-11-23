import os
import sys
import json
import logging
from typing import Dict, Any

# Add project root to path to allow imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import get_config, ensure_directories

def setup_script_logging():
    """Configure logging for the report generation script."""
    log_dir = os.path.join(project_root, "artifacts", "logs")
    ensure_directories([log_dir])
    log_file = os.path.join(log_dir, "report_generation.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_json_artifact(file_path: str, logger: logging.Logger) -> Dict[str, Any]:
    """Load a JSON artifact from disk."""
    if not os.path.exists(file_path):
        logger.error(f"Required artifact not found: {file_path}")
        raise FileNotFoundError(f"Required artifact not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        raise

def format_comparison_results(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the raw comparison data into the final results schema.
    
    This function transforms the output of statistical tests into a 
    structured report suitable for downstream analysis and archiving.
    """
    logger = logging.getLogger(__name__)
    
    formatted = {
        "report_metadata": {
            "generated_by": "T023e_GenerateComparisonReport",
            "primary_test_method": "Paired t-test",
            "sensitivity_test_method": "Wilcoxon signed-rank test (conditional)",
            "reference_frame": "FR-006 Statistical Rigor"
        },
        "model_performance": {},
        "statistical_analysis": {
            "primary_test": {
                "method": "Paired t-test",
                "description": "Used to compare model prediction errors as mandated by FR-006.",
                "results": {}
            },
            "sensitivity_test": {
                "method": "Wilcoxon signed-rank test",
                "description": "Used as a sensitivity analysis if normality assumptions are violated or errors are correlated.",
                "results": {}
            },
            "normality_assumption": {
                "check": "Shapiro-Wilk",
                "status": raw_data.get("statistical_tests", {}).get("normality_check", "unknown")
            }
        },
        "conclusion": {
            "summary": "",
            "recommended_model": "",
            "confidence_level": ""
        }
    }

    # Extract model performance metrics
    models = ["spectral_gnn", "hetero_gnn", "random_forest"]
    for model in models:
        if model in raw_data:
            formatted["model_performance"][model] = {
                "mse": raw_data[model].get("mse"),
                "mae": raw_data[model].get("mae"),
                "pearson_r": raw_data[model].get("pearson_r")
            }

    # Extract statistical test results
    stat_tests = raw_data.get("statistical_tests", {})
    
    # Primary Test (T-test)
    if "p_value_ttest" in stat_tests:
        formatted["statistical_analysis"]["primary_test"]["results"]["p_value"] = stat_tests["p_value_ttest"]
        formatted["statistical_analysis"]["primary_test"]["results"]["alpha_adjusted"] = stat_tests.get("alpha_adj", 0.05)
        formatted["statistical_analysis"]["primary_test"]["results"]["significant"] = stat_tests["p_value_ttest"] < stat_tests.get("alpha_adj", 0.05)

    # Sensitivity Test (Wilcoxon)
    if "p_value_wilcoxon" in stat_tests:
        formatted["statistical_analysis"]["sensitivity_test"]["results"]["p_value"] = stat_tests["p_value_wilcoxon"]
        formatted["statistical_analysis"]["sensitivity_test"]["results"]["alpha_adjusted"] = stat_tests.get("alpha_adj", 0.05)
        formatted["statistical_analysis"]["sensitivity_test"]["results"]["significant"] = stat_tests["p_value_wilcoxon"] < stat_tests.get("alpha_adj", 0.05)
    else:
        formatted["statistical_analysis"]["sensitivity_test"]["results"]["status"] = "Not executed (conditions not met)"

    # Generate Conclusion
    best_model = None
    best_mse = float('inf')
    
    for model, metrics in formatted["model_performance"].items():
        if metrics["mse"] < best_mse:
            best_mse = metrics["mse"]
            best_model = model

    formatted["conclusion"]["summary"] = (
        f"Analysis indicates that the {best_model} model achieved the lowest MSE ({best_mse:.4f}). "
        f"The primary statistical test (Paired t-test) {'rejected' if formatted['statistical_analysis']['primary_test']['results'].get('significant') else 'did not reject'} "
        f"the null hypothesis of equal performance at the adjusted alpha level."
    )
    formatted["conclusion"]["recommended_model"] = best_model
    formatted["conclusion"]["confidence_level"] = "High" if formatted["statistical_analysis"]["primary_test"]["results"].get("significant") else "Moderate"

    logger.info("Comparison results formatted successfully.")
    return formatted

def generate_justification_document(raw_data: Dict[str, Any]) -> str:
    """
    Generate the Markdown justification document explaining the statistical choices.
    
    This document explicitly references the requirements (FR-006) and the 
    conditional logic used for sensitivity analysis.
    """
    logger = logging.getLogger(__name__)
    
    normality_status = raw_data.get("statistical_tests", {}).get("normality_check", "unknown")
    has_wilcoxon = "p_value_wilcoxon" in raw_data.get("statistical_tests", {})
    alpha_adj = raw_data.get("statistical_tests", {}).get("alpha_adj", 0.05)
    
    justification = f"""# Statistical Justification Report

## 1. Overview
This report documents the statistical methodology used to compare the performance of the Spectral GNN, Heterophily-aware GNN, and Random Forest baseline models in predicting molecular reactivity properties.

## 2. Primary Statistical Test: Paired t-test
**Requirement:** FR-006 mandates the use of a paired t-test for model comparison.
**Rationale:** The paired t-test is appropriate for comparing the means of two related groups (prediction errors of different models on the same test set). It assumes that the differences between pairs are normally distributed.

**Execution:**
- We calculated the prediction errors (residuals) for each model on the test set.
- Pairwise comparisons were performed (Spectral vs. RF, Hetero vs. RF, Spectral vs. Hetero).
- A Bonferroni correction was applied to the significance level (α) to account for multiple comparisons.
  - Adjusted α = 0.05 / N (where N is the number of comparisons).
  - Current Adjusted α: {alpha_adj}

**Result:** The t-test was executed regardless of normality checks to strictly adhere to the project's fixed requirement (FR-006).

## 3. Normality Assumption Check
**Method:** Shapiro-Wilk test on the distribution of prediction errors.
**Status:** {normality_status.upper()}

## 4. Sensitivity Analysis: Wilcoxon Signed-Rank Test
**Trigger Condition:** This test is executed conditionally based on the following logic:
1. If the T023f Independence Check indicates correlated errors (p < 0.05), OR
2. If the Normality Check (Shapiro-Wilk) fails (p < 0.05).

**Current Execution Status:** {"Executed" if has_wilcoxon else "Not Executed (Conditions not met)"}

**Rationale:** The Wilcoxon signed-rank test is a non-parametric alternative to the paired t-test. It does not assume normality and is robust to outliers. It is used here as a sensitivity analysis to verify that the conclusions drawn from the primary t-test are not artifacts of violated assumptions.

## 5. Conclusion
The statistical framework prioritizes the Paired t-test as the primary decision metric to satisfy FR-006. The Wilcoxon test serves as a robustness check. If both tests yield consistent results (both significant or both non-significant), the conclusion is considered robust.

---
*Generated by T023e: Generate Comparison Report & Justification*
"""
    
    logger.info("Justification document generated.")
    return justification

def main():
    """Main entry point for the report generation script."""
    logger = setup_script_logging()
    config = get_config()
    
    # Define paths
    raw_results_path = os.path.join(project_root, "artifacts", "model_comparison_raw.json")
    final_results_path = os.path.join(project_root, "artifacts", "model_comparison_results.json")
    justification_path = os.path.join(project_root, "artifacts", "statistical_justification.md")
    
    ensure_directories([os.path.dirname(final_results_path), os.path.dirname(justification_path)])
    
    try:
        # 1. Load Raw Results
        logger.info(f"Loading raw comparison data from {raw_results_path}...")
        raw_data = load_json_artifact(raw_results_path, logger)
        
        # 2. Format Results
        logger.info("Formatting comparison results...")
        formatted_results = format_comparison_results(raw_data)
        
        # 3. Write Final Results JSON
        with open(final_results_path, 'w') as f:
            json.dump(formatted_results, f, indent=2)
        logger.info(f"Saved formatted results to {final_results_path}")
        
        # 4. Generate and Write Justification
        logger.info("Generating statistical justification document...")
        justification_md = generate_justification_document(raw_data)
        
        with open(justification_path, 'w') as f:
            f.write(justification_md)
        logger.info(f"Saved justification document to {justification_path}")
        
        logger.info("Task T023e completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Critical file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()