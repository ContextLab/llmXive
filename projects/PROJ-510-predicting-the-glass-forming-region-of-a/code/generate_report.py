"""
Report generation module for glass-forming alloy analysis.
Generates REPORT.md summarizing data, model performance, feature importance, and sensitivity analysis.
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/report.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

REPORT_PATH = "REPORT.md"
DATA_DIR = "data"
MODELS_DIR = "data/models"
LOGS_DIR = "data/logs"

def load_json_file(path: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def load_csv_file(path: str) -> pd.DataFrame:
    """Load CSV file."""
    return pd.read_csv(path)

def get_data_summary():
    """Get data summary from processed data."""
    data_path = os.path.join(DATA_DIR, "processed", "processed_alloys.csv")
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        return {
            "n_samples": len(df),
            "n_features": len([c for c in df.columns if c not in ['composition', 'critical_cooling_rate', 'source_label', 'parsed_composition']])
        }
    return None

def get_model_performance():
    """Get model performance metrics."""
    cv_metrics_path = os.path.join(MODELS_DIR, "cv_metrics.json")
    null_rmse_path = os.path.join(MODELS_DIR, "null_model_rmse.json")
    stat_comp_path = os.path.join(MODELS_DIR, "statistical_comparison.json")
    
    result = {}
    if os.path.exists(cv_metrics_path):
        result['cv_metrics'] = load_json_file(cv_metrics_path)
    if os.path.exists(null_rmse_path):
        result['null_rmse'] = load_json_file(null_rmse_path)
    if os.path.exists(stat_comp_path):
        result['statistical_comparison'] = load_json_file(stat_comp_path)
    
    return result

def get_feature_importance():
    """Get feature importance data."""
    # This would normally load feature_importance.json from T028
    # For now, we return a placeholder
    return None

def get_sensitivity_analysis():
    """Get sensitivity analysis results."""
    status_path = os.path.join(MODELS_DIR, "sensitivity_status.json")
    if os.path.exists(status_path):
        return load_json_file(status_path)
    return None

def generate_report_markdown(data_summary: Dict, model_perf: Dict, 
                             feature_imp: Dict, sensitivity: Dict) -> str:
    """Generate the final report in Markdown format."""
    report = []
    report.append("# Glass Forming Region Prediction Report\n")
    report.append("## Summary\n")
    report.append("This report summarizes the analysis of glass-forming alloys using machine learning.\n")
    report.append("**Important**: All findings are **ASSOCIATIONAL**, not causal.\n")
    
    # Data Summary
    report.append("## Data Summary\n")
    if data_summary:
        report.append(f"- Total samples: {data_summary.get('n_samples', 'N/A')}")
        report.append(f"- Features: {data_summary.get('n_features', 'N/A')}\n")
    
    # Model Performance
    report.append("## Model Performance\n")
    if model_perf and 'cv_metrics' in model_perf:
        cv = model_perf['cv_metrics']
        report.append(f"- **5-fold CV Mean RMSE**: {cv.get('mean_rmse', 'N/A'):.4f} (Primary Metric)")
        report.append(f"- CV Std RMSE: {cv.get('std_rmse', 'N/A'):.4f}")
        report.append(f"- Fold Scores: {cv.get('fold_scores', [])}\n")
    
    if model_perf and 'statistical_comparison' in model_perf:
        stat = model_perf['statistical_comparison']
        report.append("### Statistical Significance (SC-002)\n")
        report.append(f"- P-value: {stat.get('p_value', 'N/A')}")
        report.append(f"- T-statistic: {stat.get('t_statistic', 'N/A')}")
        report.append(f"- SC-002 Met: {stat.get('sc002_met', False)}\n")
    
    # Feature Importance
    report.append("## Feature Importance\n")
    if feature_imp:
        report.append("Feature importance details would go here.\n")
    else:
        report.append("Feature importance analysis not available.\n")
    
    # Sensitivity Analysis
    report.append("## Sensitivity Analysis\n")
    if sensitivity:
        report.append(f"- Stability Met: {sensitivity.get('stability_met', False)}")
        report.append(f"- F1 Margin: {sensitivity.get('f1_margin_pct', 0):.2f}%")
        report.append(f"- Run Status: {sensitivity.get('run_status', 'N/A')}\n")
    else:
        report.append("Sensitivity analysis not available.\n")
    
    # Limitations
    report.append("## Limitations and Caveats\n")
    report.append("1. The dataset is observational; all findings are **associational**, not causal.")
    report.append("2. The model performance is bounded by the quality and representativeness of the `matsci/glass-forming-ability` dataset.")
    report.append("3. The sensitivity analysis results are specific to the tested thresholds {50, 100, 150} K/s.\n")
    
    return "\n".join(report)

def main():
    """Main entry point for report generation."""
    logger.info("Generating report")
    
    # Load data
    data_summary = get_data_summary()
    model_perf = get_model_performance()
    feature_imp = get_feature_importance()
    sensitivity = get_sensitivity_analysis()
    
    # Generate report
    report = generate_report_markdown(data_summary, model_perf, feature_imp, sensitivity)
    
    # Write report
    with open(REPORT_PATH, 'w') as f:
        f.write(report)
    
    logger.info(f"Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    main()
