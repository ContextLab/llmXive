"""
T028: Generate the final research report compiling model comparison, statistical significance, and SHAP insights.

This script loads the evaluation results from T024/T025 and SHAP insights from T027,
then compiles them into a human-readable Markdown report saved to `docs/reports/`.
"""
import os
import json
import yaml
from pathlib import Path
from datetime import datetime

# Project-relative imports
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVAL_RESULTS_PATH = PROJECT_ROOT / "data" / "outputs" / "model_comparison.json"
SHAP_RESULTS_PATH = PROJECT_ROOT / "data" / "outputs" / "shap_summary.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"
REPORT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "reports"
REPORT_OUTPUT_PATH = REPORT_OUTPUT_DIR / "final_model_report.md"

def load_json_safe(path: Path) -> dict:
    """Load JSON file, returning empty dict if not found."""
    if not path.exists():
        logger.warning(f"Results file not found: {path}. Ensure T025/T027 have run.")
        return {}
    with open(path, "r") as f:
        return json.load(f)

def load_config() -> dict:
    """Load project settings."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def generate_report() -> None:
    """Compile results into a Markdown report."""
    logger.info("Generating final research report...")

    # Ensure output directory exists
    REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load inputs
    eval_data = load_json_safe(EVAL_RESULTS_PATH)
    shap_data = load_json_safe(SHAP_RESULTS_PATH)
    config = load_config()

    # Extract comparison metrics
    r2_thermo = eval_data.get("thermodynamic_model", {}).get("r2_mean", "N/A")
    r2_comp = eval_data.get("composition_model", {}).get("r2_mean", "N/A")
    delta_r2 = eval_data.get("delta_r2", "N/A")
    
    # Statistical test results
    test_type = eval_data.get("statistical_test_type", "N/A")
    p_value = eval_data.get("p_value", "N/A")
    ci_lower = eval_data.get("ci_lower", "N/A")
    ci_upper = eval_data.get("ci_upper", "N/A")
    significance = "Significant" if (isinstance(p_value, (int, float)) and p_value < 0.05) else "Not Significant"

    # SHAP insights
    shap_features = shap_data.get("top_features", [])
    # Format: [{"feature": "name", "value": 0.5, "direction": "positive"}, ...]
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build Markdown content
    report_lines = [
        "# Creep Resistance Prediction: Model Comparison Report",
        "",
        f"**Generated**: {timestamp}",
        "",
        "## Executive Summary",
        "",
        "This report compares two Gradient Boosting Regression models for predicting creep rupture time:",
        "- **Thermodynamic Model**: Uses atomic fractions + mixing enthalpy + radius mismatch.",
        "- **Composition-Only Model**: Uses atomic fractions only.",
        "",
        "## Model Performance Comparison",
        "",
        "| Model | R² (Mean) | RMSE |",
        "| :--- | :--- | :--- |",
        f"| Thermodynamic Features | {r2_thermo} | {eval_data.get('thermodynamic_model', {}).get('rmse_mean', 'N/A')} |",
        f"| Composition-Only | {r2_comp} | {eval_data.get('composition_model', {}).get('rmse_mean', 'N/A')} |",
        "",
        f"**Performance Delta (Thermo - Comp)**: {delta_r2}",
        "",
        "## Statistical Significance Analysis",
        "",
        f"- **Test Method**: {test_type}",
        f"- **P-value**: {p_value}",
        f"- **95% Confidence Interval**: [{ci_lower}, {ci_upper}]",
        f"- **Conclusion**: The difference in performance is **{significance}** (α=0.05).",
        "",
        "## Feature Importance (SHAP Analysis)",
        "",
        "Top 5 most influential features in the Thermodynamic Model:",
        "",
    ]

    if shap_features:
        report_lines.append("| Rank | Feature | Influence (Mean |SHAP|) | Direction |")
        report_lines.append("| :--- | :--- | :--- | :--- |")
        for i, feat in enumerate(shap_features[:5], 1):
            name = feat.get("feature", "Unknown")
            val = feat.get("value", 0.0)
            direction = feat.get("direction", "neutral")
            # Format direction for readability
            dir_text = "Positive (+)" if direction == "positive" else "Negative (-)" if direction == "negative" else "Neutral"
            report_lines.append(f"| {i} | {name} | {val:.4f} | {dir_text} |")
    else:
        report_lines.append("*No SHAP results available. Ensure T027 has been executed.*")

    report_lines.extend([
        "",
        "## Methodology Notes",
        "",
        "- **Data Source**: Processed alloy data from NIMS (or synthetic fallback per T016).",
        "- **Validation**: Nested Cross-Validation (Outer: Stratified/Repeated, Inner: GridSearch).",
        "- **Statistical Test**: Chosen based on sample size (Permutation Test for 20≤N<100, Bootstrap for N<20).",
        "",
        "---",
        f"*Report generated by llmXive pipeline (Task T028)*"
    ])

    # Write report
    report_content = "\n".join(report_lines)
    with open(REPORT_OUTPUT_PATH, "w") as f:
        f.write(report_content)

    logger.info(f"Report successfully saved to: {REPORT_OUTPUT_PATH}")
    print(f"Report generated: {REPORT_OUTPUT_PATH}")

if __name__ == "__main__":
    generate_report()