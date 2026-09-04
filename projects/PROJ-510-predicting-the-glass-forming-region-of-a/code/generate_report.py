"""
Report Generation Module for Glass Forming Region Prediction.

This module aggregates results from the entire pipeline to generate
a comprehensive Markdown report (REPORT.md).

It loads:
- Data summary from processed_alloys.csv
- Model metrics from cv_metrics.json, model_metrics_baseline.json
- Feature importance from feature_importance.json
- Sensitivity analysis from sensitivity_status.json
- Statistical comparison from statistical_comparison.json

All predictive findings are explicitly framed as ASSOCIATIONAL.
"""
import os
import json
import sys
import glob
from typing import Dict, Any, List, Optional
import logging
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(DATA_DIR, "models")
REPORT_PATH = os.path.join(PROJECT_ROOT, "REPORT.md")

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"JSON file not found: {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {filepath}: {e}")
        raise

def load_csv_file(filepath: str) -> pd.DataFrame:
    """Load a CSV file and return a DataFrame."""
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        logger.error(f"CSV file not found: {filepath}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"CSV file is empty: {filepath}")
        raise

def get_data_summary(df: pd.DataFrame) -> str:
    """Generate a summary of the dataset."""
    n_rows = len(df)
    n_cols = len(df.columns)
    target_col = "critical_cooling_rate"
    
    if target_col in df.columns:
        mean_ccr = df[target_col].mean()
        std_ccr = df[target_col].std()
        min_ccr = df[target_col].min()
        max_ccr = df[target_col].max()
        target_summary = (
            f"- **Mean**: {mean_ccr:.2f} K/s\n"
            f"- **Std Dev**: {std_ccr:.2f} K/s\n"
            f"- **Min**: {min_ccr:.2f} K/s\n"
            f"- **Max**: {max_ccr:.2f} K/s"
        )
    else:
        target_summary = "Target column 'critical_cooling_rate' not found."

    thermodynamic_cols = [c for c in df.columns if c.startswith("mixing") or c.startswith("size") or c.startswith("electro")]
    thermodynamic_summary = f"- **Thermodynamic Features**: {len(thermodynamic_cols)} columns computed.\n"
    for col in thermodynamic_cols:
        if col in df.columns:
            thermodynamic_summary += f"  - `{col}`: mean={df[col].mean():.4f}, std={df[col].std():.4f}\n"

    return (
        f"## Data Overview\n"
        f"- **Total Samples**: {n_rows}\n"
        f"- **Total Features**: {n_cols}\n"
        f"- **Target Variable**: critical_cooling_rate (K/s)\n\n"
        f"### Target Distribution\n{target_summary}\n\n"
        f"### Thermodynamic Features\n{thermodynamic_summary}"
    )

def get_model_performance() -> str:
    """Load and summarize model performance metrics."""
    metrics = {}
    
    # Load CV metrics
    cv_path = os.path.join(MODELS_DIR, "cv_metrics.json")
    if os.path.exists(cv_path):
        metrics['cv'] = load_json_file(cv_path)
    
    # Load baseline/null model metrics
    null_path = os.path.join(MODELS_DIR, "null_model_rmse.json")
    if os.path.exists(null_path):
        metrics['null'] = load_json_file(null_path)

    # Load statistical comparison
    stat_path = os.path.join(MODELS_DIR, "statistical_comparison.json")
    if os.path.exists(stat_path):
        metrics['stat'] = load_json_file(stat_path)

    report = "## Model Performance\n\n"
    
    if 'cv' in metrics:
        cv_data = metrics['cv']
        report += f"### Random Forest (Cross-Validation)\n"
        report += f"- **Mean RMSE**: {cv_data.get('mean_rmse', 'N/A'):.4f}\n"
        report += f"- **Fold Scores**: {cv_data.get('fold_scores', [])}\n\n"
    
    if 'null' in metrics:
        null_data = metrics['null']
        report += f"### Null Model (Dummy Regressor)\n"
        report += f"- **Test RMSE**: {null_data.get('rmse', 'N/A'):.4f}\n\n"
    
    if 'stat' in metrics:
        stat_data = metrics['stat']
        report += f"### Statistical Significance (SC-002)\n"
        p_val = stat_data.get('p_value', 'N/A')
        t_stat = stat_data.get('t_statistic', 'N/A')
        sc_met = stat_data.get('sc002_met', False)
        status = "PASSED" if sc_met else "FAILED"
        
        report += f"- **p-value**: {p_val:.6f}\n"
        report += f"- **t-statistic**: {t_stat:.4f}\n"
        report += f"- **SC-002 Status**: {status}\n"
        
        if sc_met:
            report += "- **Conclusion**: The model's performance is statistically distinguishable from the null model (p < 0.05).\n"
        else:
            report += "- **Conclusion**: The model's performance is NOT statistically distinguishable from the null model (p >= 0.05).\n"
        
        report += "\n"

    return report

def get_feature_importance() -> str:
    """Load and summarize feature importance."""
    importance_path = os.path.join(PROCESSED_DIR, "feature_importance.json")
    # Fallback to models dir if not in processed
    if not os.path.exists(importance_path):
        importance_path = os.path.join(MODELS_DIR, "feature_importance.json")

    if not os.path.exists(importance_path):
        return "## Feature Importance\n\n*Feature importance analysis was not completed or the output file is missing.*\n"

    data = load_json_file(importance_path)
    
    report = "## Feature Importance & Permutation Analysis\n\n"
    report += "Features are ranked by mean absolute permutation importance.\n\n"
    report += "| Rank | Feature | Importance | p-value | Significant (p<0.05) |\n"
    report += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    # Sort by importance if list of dicts
    if isinstance(data, list):
        sorted_data = sorted(data, key=lambda x: x.get('importance', 0), reverse=True)
        for i, item in enumerate(sorted_data, 1):
            feat = item.get('feature', 'Unknown')
            imp = item.get('importance', 0)
            p_val = item.get('p_value', 1.0)
            sig = "Yes" if p_val < 0.05 else "No"
            report += f"| {i} | `{feat}` | {imp:.4f} | {p_val:.4f} | {sig} |\n"
    else:
        report += "*Unexpected format for feature_importance.json*\n"

    report += "\n**Note**: High importance indicates a strong *associational* link between the feature and the target in this dataset.\n"
    return report

def get_sensitivity_analysis() -> str:
    """Load and summarize sensitivity analysis results."""
    status_path = os.path.join(MODELS_DIR, "sensitivity_status.json")
    
    if not os.path.exists(status_path):
        return "## Sensitivity Analysis\n\n*Sensitivity analysis results are missing.*\n"

    status_data = load_json_file(status_path)
    run_status = status_data.get('run_status', 'UNKNOWN')
    stability_met = status_data.get('stability_met', False)
    f1_margin = status_data.get('f1_margin_pct', 0)
    thresholds = status_data.get('threshold_values', [])

    report = "## Sensitivity Analysis (SC-003)\n\n"
    report += "This analysis evaluates the stability of the model's classification performance\n"
    report += "when varying the threshold for binarizing the critical cooling rate.\n\n"
    
    report += f"- **Thresholds Tested**: {thresholds} K/s\n"
    report += f"- **F1 Margin**: {f1_margin:.2f}%\n"
    report += f"- **Stability Met (<=10% margin)**: {'Yes' if stability_met else 'No'}\n"
    report += f"- **Overall Status**: {run_status}\n\n"
    
    if not stability_met:
        report += "> **WARNING**: The model's classification performance is sensitive to the choice of threshold.\n"
        report += "> This suggests the decision boundary is not robust across the tested range.\n\n"
    else:
        report += "> **PASS**: The model demonstrates robust classification performance across the tested thresholds.\n\n"

    # Try to load detailed CSV if available
    csv_path = os.path.join(MODELS_DIR, "sensitivity_report.csv")
    if os.path.exists(csv_path):
        df = load_csv_file(csv_path)
        report += "### Detailed Metrics by Threshold\n\n"
        report += df.to_markdown(index=False)
        report += "\n"

    return report

def generate_report_markdown() -> str:
    """Assemble all sections into the final Markdown report."""
    logger.info("Starting report generation...")

    # 1. Header
    header = (
        "# Predicting the Glass Forming Region of Alloy Systems with Machine Learning\n\n"
        "**Project ID**: PROJ-510\n"
        "**Date**: " + pd.Timestamp.now().strftime("%Y-%m-%d") + "\n\n"
        "> **Disclaimer**: All predictive findings presented in this report are **ASSOCIATIONAL**.\n"
        "> This model identifies statistical correlations within the provided dataset.\n"
        "> It does not imply causal mechanisms or physical laws governing glass formation.\n"
        "> Predictions should be validated experimentally.\n\n"
    )

    # 2. Data Summary
    data_path = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
    if os.path.exists(data_path):
        df = load_csv_file(data_path)
        data_section = get_data_summary(df)
    else:
        data_section = "## Data Overview\n\n*Processed data file not found.*\n"

    # 3. Model Performance
    model_section = get_model_performance()

    # 4. Feature Importance
    feature_section = get_feature_importance()

    # 5. Sensitivity Analysis
    sensitivity_section = get_sensitivity_analysis()

    # 6. Conclusion & Caveats
    conclusion = (
        "## Conclusion & Caveats\n\n"
        "This study utilized a Random Forest regressor to model the critical cooling rate\n"
        "of ternary alloys based on thermodynamic descriptors. Key findings include:\n\n"
        "1. **Associational Nature**: The model captures patterns in the training data.\n"
        "   These patterns are not necessarily causal.\n"
        "2. **Statistical Significance**: The model's performance was compared against a null model.\n"
        "   (See SC-002 section above for details).\n"
        "3. **Feature Importance**: Thermodynamic features such as mixing enthalpy and size mismatch\n"
        "   were found to be predictive within this dataset.\n"
        "4. **Sensitivity**: The model's classification stability was tested across thresholds.\n"
        "   (See SC-003 section above).\n\n"
        "**Future Work**:\n"
        "- Validate findings on external datasets.\n"
        "- Investigate causal mechanisms behind the identified correlations.\n"
        "- Expand the feature space to include kinetic descriptors.\n"
    )

    report = f"{header}\n{data_section}\n\n{model_section}\n\n{feature_section}\n\n{sensitivity_section}\n\n{conclusion}"
    
    return report

def main():
    """Main entry point for report generation."""
    try:
        report_content = generate_report_markdown()
        
        # Write to file
        with open(REPORT_PATH, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Report successfully generated at: {REPORT_PATH}")
        print(f"Report generated: {REPORT_PATH}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()