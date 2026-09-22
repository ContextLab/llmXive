import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Local imports matching API surface
from config import get_config, validate_config, ensure_directories
from utils.logging import DataPipelineLog
from utils.metrics_logger import log_comparison_report

# Validation Gene List (15) as specified in T029
VALIDATION_GENES = [
    "DREB2A", "ERF1", "ABI5", "RD29A", "COR15A",
    "LEA3", "HSP70", "SOD", "APX1", "CAT1",
    "GPX1", "MDHAR", "DHAR", "GSTU", "ZAT12"
]

def load_cv_results(metrics_path: str = "data/logs/metrics.json") -> Dict[str, Any]:
    """
    Load the metrics JSON file containing CV results and feature importance.
    """
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}. "
                                "Run training/evaluation tasks first.")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def perform_rf_vs_xgb_ttest(rf_scores: List[float], xgb_scores: List[float]) -> Tuple[float, float]:
    """
    Perform paired t-test on CV scores for RF vs XGBoost.
    Returns (t_statistic, p_value).
    """
    from scipy import stats
    t_stat, p_val = stats.ttest_rel(rf_scores, xgb_scores)
    return t_stat, p_val

def calculate_permutation_importance(model: Any, X: np.ndarray, y: np.ndarray, 
                                     feature_names: List[str], n_repeats: int = 10, 
                                     random_state: int = 42) -> pd.DataFrame:
    """
    Calculate permutation feature importance.
    """
    from sklearn.inspection import permutation_importance
    
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state,
        scoring='roc_auc'
    )
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance_mean': result.importances_mean,
        'importance_std': result.importances_std
    })
    
    # Sort by importance descending
    importance_df = importance_df.sort_values(by='importance_mean', ascending=False)
    return importance_df

def classify_features(feature_names: List[str]) -> Dict[str, List[str]]:
    """
    Classify features into 'genomic' and 'physiological' based on naming conventions.
    Assumes genomic markers are gene names (uppercase, alphanumeric) and others are physiological.
    """
    genomic = []
    physiological = []
    
    for name in feature_names:
        # Heuristic: if it matches known gene patterns or is in our genomic list
        if name in VALIDATION_GENES or (name.isupper() and name.replace('_', '').isalnum()):
            genomic.append(name)
        else:
            physiological.append(name)
            
    return {
        'genomic': genomic,
        'physiological': physiological
    }

def generate_comparison_report(metrics_data: Dict[str, Any], 
                               feature_importance_df: pd.DataFrame,
                               config: Dict[str, Any]) -> str:
    """
    Generate the final analysis report content (Markdown).
    Includes validation logic: count of validation genes in Top 10 >= 3.
    """
    # Extract top 10 features
    top_10_features = feature_importance_df.head(10)['feature'].tolist()
    
    # Validation Logic
    validation_genes_in_top_10 = [g for g in top_10_features if g in VALIDATION_GENES]
    count_validation = len(validation_genes_in_top_10)
    validation_passed = count_validation >= 3
    
    # Extract model metrics
    best_model_name = metrics_data.get('best_model', 'Unknown')
    best_auc = metrics_data.get('best_auc', 0.0)
    delong_p_value = metrics_data.get('delong_p_value', 'N/A')
    
    # Extract t-test results if available
    t_stat = metrics_data.get('t_statistic', 'N/A')
    p_val_ttest = metrics_data.get('p_value_ttest', 'N/A')
    
    # Classify features
    classification = classify_features(feature_importance_df['feature'].tolist())
    
    # Build Report
    report_lines = [
        "# Final Analysis Report: Plant Drought Tolerance Prediction",
        "",
        "## Executive Summary",
        f"This report summarizes the final analysis of the drought tolerance prediction pipeline.",
        f"Best Model: **{best_model_name}**",
        f"Test ROC-AUC: **{best_auc:.4f}**",
        "",
        "## Statistical Validation",
        "",
        "### DeLong's Test (Model vs Baseline)",
        f"- P-value: {delong_p_value}",
        f"- Significance Threshold: p < 0.05",
        f"- Result: {'Significant' if delong_p_value != 'N/A' and float(delong_p_value) < 0.05 else 'Not Significant or N/A'}",
        "",
        "### Paired T-Test (RF vs XGBoost)",
        f"- T-Statistic: {t_stat}",
        f"- P-Value: {p_val_ttest}",
        "",
        "## Feature Importance Analysis",
        "",
        "### Top 10 Features",
        "Rank | Feature | Importance (Mean)",
        "--- | --- | ---",
    ]
    
    for i, (_, row) in enumerate(feature_importance_df.head(10).iterrows(), 1):
        report_lines.append(f"{i} | {row['feature']} | {row['importance_mean']:.4f}")
    
    report_lines.extend([
        "",
        "### Feature Classification",
        f"- **Genomic Markers**: {len(classification['genomic'])} features",
        f"- **Physiological Traits**: {len(classification['physiological'])} features",
        "",
        "## Validation Check (SC-005)",
        "",
        f"**Validation Gene List (15)**: {', '.join(VALIDATION_GENES)}",
        f"- Count of validation genes in Top 10 features: **{count_validation}**",
        f"- Threshold: >= 3",
        f"- **Result**: {'✅ PASSED' if validation_passed else '❌ FAILED'}",
        "",
        "## Conclusion",
        "",
        "The pipeline successfully trained and evaluated models for drought tolerance prediction.",
        f"The validation check {'passed' if validation_passed else 'failed'}, indicating {'strong' if validation_passed else 'weak'} predictive signal from known drought-responsive genes.",
        "",
        "## Reproducibility",
        f"- Config Seed: {config.get('random_seed', 42)}",
        f"- Models saved to: `data/models/`",
        f"- Metrics logged to: `data/logs/metrics.json`"
    ])
    
    return "\n".join(report_lines)

def main():
    """
    Main entry point for T029.
    1. Load metrics and feature importance from previous steps.
    2. Calculate permutation importance if not already done (or load pre-calculated).
    3. Generate the report content.
    4. Write report to `docs/reports/final_analysis.md`.
    5. Log the validation result.
    """
    config = get_config()
    ensure_directories(config)
    
    logger = DataPipelineLog(config)
    logger.info("Starting Final Analysis Report Generation (T029)")
    
    # Paths
    metrics_path = Path("data/logs/metrics.json")
    report_path = Path("docs/reports/final_analysis.md")
    model_path = Path("data/models/best_model.joblib")
    test_data_path = Path("data/processed/split_test_data.npz") # Assumed output from split/evaluate
    
    # Load Metrics
    try:
        metrics_data = load_cv_results(str(metrics_path))
    except FileNotFoundError as e:
        logger.error(f"Metrics file missing: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    
    # Load Model and Test Data for Permutation Importance
    # Note: If metrics already contains feature_importance, we can skip re-calculation.
    # However, to be robust, we re-calculate if the model and data exist.
    feature_importance_df = None
    
    if 'feature_importance' in metrics_data and isinstance(metrics_data['feature_importance'], list):
        # Load from metrics if available (simplified representation)
        # We expect the metrics to have been populated by T028
        feature_importance_df = pd.DataFrame(metrics_data['feature_importance'])
    else:
        # Re-calculate if possible
        if model_path.exists() and test_data_path.exists():
            logger.info("Calculating Permutation Feature Importance...")
            model = joblib.load(str(model_path))
            
            # Load test data
            test_data = np.load(str(test_data_path), allow_pickle=True)
            X_test = test_data['X']
            y_test = test_data['y']
            feature_names = test_data.get('feature_names', None)
            
            if feature_names is None:
                # Fallback to column names from metrics if available, else generic
                if 'feature_names' in metrics_data:
                    feature_names = metrics_data['feature_names']
                else:
                    feature_names = [f"feature_{i}" for i in range(X_test.shape[1])]
            
            feature_importance_df = calculate_permutation_importance(
                model, X_test, y_test, feature_names
            )
            
            # Update metrics for logging
            metrics_data['feature_importance'] = feature_importance_df.to_dict('records')
            with open(metrics_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
        else:
            logger.warning("Model or test data not found. Using placeholder or exiting.")
            # If we can't calculate, we might need to fail or use dummy data if strictly required to produce a file.
            # However, per constraints, we must produce real results. If data is missing, we fail loudly.
            if not model_path.exists():
                raise FileNotFoundError(f"Best model not found at {model_path}. Run training first.")
            if not test_data_path.exists():
                raise FileNotFoundError(f"Test data not found at {test_data_path}. Run split/evaluate first.")
            
    if feature_importance_df is None:
        raise RuntimeError("Could not obtain feature importance data.")
    
    # Generate Report
    report_content = generate_comparison_report(metrics_data, feature_importance_df, config)
    
    # Write Report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report generated at {report_path}")
    
    # Log Validation Result
    validation_genes_in_top_10 = [g for g in feature_importance_df.head(10)['feature'].tolist() if g in VALIDATION_GENES]
    log_comparison_report(
        path="data/logs/metrics.json",
        validation_passed=len(validation_genes_in_top_10) >= 3,
        validation_count=len(validation_genes_in_top_10)
    )
    
    print(f"Task T029 Complete. Report: {report_path}")

if __name__ == "__main__":
    main()
