"""
Report Generation Module for Glass Forming Ability Prediction.
Generates the final REPORT.md with all findings.
"""

import os
import json
import sys
import glob
import logging
from typing import Dict, Any, List, Optional
from utils import get_logger

logger = get_logger("report")
MODEL_DIR = "data/models"
LOG_DIR = "data/logs"
REPORT_PATH = "REPORT.md"

def load_json_file(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def load_csv_file(path: str) -> List[Dict[str, Any]]:
    import pandas as pd
    if os.path.exists(path):
        return pd.read_csv(path).to_dict('records')
    return []

def get_data_summary() -> Dict[str, Any]:
    """
    Get data summary from validation logs.
    """
    status = load_json_file(os.path.join(LOG_DIR, "data_validation_status.json"))
    return {
        "n_total": status.get("n_total", 0),
        "status": status.get("status", "unknown")
    }

def get_model_performance() -> Dict[str, Any]:
    """
    Get model performance metrics.
    """
    test_metrics = load_json_file(os.path.join(MODEL_DIR, "test_metrics.json"))
    cv_metrics = load_json_file(os.path.join(MODEL_DIR, "cv_metrics.json"))
    stat_comparison = load_json_file(os.path.join(MODEL_DIR, "statistical_comparison.json"))
    
    return {
        "test_rmse": test_metrics.get("test_rmse", 0),
        "cv_mean_rmse": cv_metrics.get("mean_rmse", 0),
        "cv_std_rmse": cv_metrics.get("std_rmse", 0),
        "sc002_met": stat_comparison.get("sc002_met", False),
        "p_value": stat_comparison.get("p_value", 0),
        "t_statistic": stat_comparison.get("t_statistic", 0)
    }

def get_feature_importance() -> List[Dict[str, Any]]:
    """
    Get feature importance data.
    """
    return load_json_file(os.path.join(MODEL_DIR, "feature_importance.json"))

def get_sensitivity_analysis() -> Dict[str, Any]:
    """
    Get sensitivity analysis results.
    """
    return load_json_file(os.path.join(MODEL_DIR, "sensitivity_status.json"))

def generate_report_markdown() -> str:
    """
    Generate the final REPORT.md content.
    """
    data_summary = get_data_summary()
    model_perf = get_model_performance()
    feature_imp = get_feature_importance()
    sensitivity = get_sensitivity_analysis()
    
    report = f"""# Glass Forming Region Prediction Report

## Executive Summary
This report presents the findings of a machine learning study aimed at predicting the glass-forming region of alloy systems. All findings are **associational** and not causal.

## Data Summary
- **Total Samples**: {data_summary['n_total']}
- **Status**: {data_summary['status'].upper()}

## Model Performance
- **Test RMSE**: {model_perf['test_rmse']:.4f}
- **5-Fold CV Mean RMSE**: {model_perf['cv_mean_rmse']:.4f} (Primary Metric)
- **CV Std RMSE**: {model_perf['cv_std_rmse']:.4f}

### Statistical Significance (SC-002)
- **Model vs Null Model**: {'PASSED' if model_perf['sc002_met'] else 'FAILED'}
- **P-Value**: {model_perf['p_value']:.4f}
- **T-Statistic**: {model_perf['t_statistic']:.4f}

*Note: A p-value < 0.05 indicates the model is statistically distinguishable from a null model.*

## Feature Importance
| Feature | Importance Score |
|---------|------------------|
"""
    for feat in feature_imp:
        report += f"| {feat['feature']} | {feat['importance_score']:.4f} |\n"
    
    report += f"""
## Sensitivity Analysis (SC-003)
- **Stability Met**: {'YES' if sensitivity.get('stability_met', False) else 'NO'}
- **RMSE Variance**: {sensitivity.get('rmse_variance', 0):.4f}
- **Run Status**: {sensitivity.get('run_status', 'UNKNOWN')}

*Note: Stability indicates robustness of the model to small perturbations near decision boundaries.*

## Limitations and Caveats
1. **Associational Nature**: The dataset is observational; all findings are **associational**, not causal.
2. **Data Quality**: Model performance is bounded by the quality and representativeness of the `matsci/glass-forming-ability` dataset.
3. **Sensitivity Scope**: Sensitivity analysis results are specific to the tested thresholds within the examined range.
4. **Collinearity**: If collinearity was detected, the model may have been retrained with a reduced feature set, potentially affecting generalizability.

## Conclusion
The machine learning model demonstrates {'significant' if model_perf['sc002_met'] else 'limited'} predictive capability for glass-forming ability. The stability of the model under sensitivity analysis {'supports' if sensitivity.get('stability_met', False) else 'challenges'} its robustness. Future work should focus on expanding the dataset and validating findings with experimental data.
"""
    return report

def main():
    """
    Generate the final report.
    """
    logger.info("Generating final report...")
    report_content = generate_report_markdown()
    
    with open(REPORT_PATH, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report generated at {REPORT_PATH}")

if __name__ == "__main__":
    main()