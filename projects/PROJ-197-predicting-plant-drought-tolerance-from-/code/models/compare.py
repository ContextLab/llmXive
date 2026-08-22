import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.logging import DataPipelineLog
from config import get_config

# Constants for Validation Logic (SC-005)
VALIDATION_GENE_LIST = [
    "DREB2A", "ERF1", "ABI5", "RD29A", "COR15A",
    "LEA3", "HSP70", "SOD", "APX1", "CAT1",
    "GPX1", "MDHAR", "DHAR", "GSTU", "ZAT12"
]
MIN_VALIDATION_GENE_COUNT = 3
TOP_N_FEATURES = 10

def load_cv_results(metrics_path: str = "data/logs/metrics.json") -> Dict[str, Any]:
    """
    Loads the metrics JSON file containing CV scores and model information.
    """
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}. Run train.py and evaluate.py first.")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def perform_rf_vs_xgb_ttest(metrics: Dict[str, Any]) -> Tuple[float, float]:
    """
    Performs a paired t-test on the CV AUC scores for RF vs XGBoost.
    Returns (t_statistic, p_value).
    """
    # Assuming metrics structure: {'cv_results': {'rf': [scores...], 'xgboost': [scores...]}}
    # This matches the output of T027 implementation logic
    if 'cv_results' not in metrics:
        # Fallback if structure differs, looking for specific keys
        rf_scores = metrics.get('rf_cv_scores', [])
        xgb_scores = metrics.get('xgboost_cv_scores', [])
    else:
        rf_scores = metrics['cv_results'].get('rf', [])
        xgb_scores = metrics['cv_results'].get('xgboost', [])
    
    if not rf_scores or not xgb_scores:
        raise ValueError("No CV scores found in metrics for t-test.")
    
    # Ensure lengths match for paired test
    min_len = min(len(rf_scores), len(xgb_scores))
    rf_scores = rf_scores[:min_len]
    xgb_scores = xgb_scores[:min_len]

    t_stat, p_val = stats.paired_ttest(rf_scores, xgb_scores)
    return t_stat, p_val

def calculate_permutation_importance(model_path: str, X_test: np.ndarray, y_test: np.ndarray, 
                                    feature_names: List[str], n_repeats: int = 5, random_state: int = 42) -> pd.DataFrame:
    """
    Calculates permutation feature importance for the best model.
    Returns a DataFrame with feature names and importance scores.
    """
    from sklearn.inspection import permutation_importance
    
    model = joblib.load(model_path)
    
    # Use sklearn's permutation_importance
    # Note: For XGBoost/RF, this is standard.
    result = permutation_importance(model, X_test, y_test, n_repeats=n_repeats, random_state=random_state, n_jobs=2)
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance_mean': result.importances_mean,
        'importance_std': result.importances_std
    })
    
    return importance_df.sort_values(by='importance_mean', ascending=False)

def classify_features(feature_importance_df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Classifies top features into 'genomic' and 'physiological' based on naming conventions.
    Assumes genomic features contain gene names or specific prefixes, others are physiological.
    Returns a dict: {'genomic': [...], 'physiological': [...]}
    """
    genomic_features = []
    physiological_features = []
    
    # Heuristic: If feature name is in the known gene list or looks like a gene name
    # We rely on the synthetic generation logic where genomic features are named after genes
    # and physiological traits have different naming (e.g., 'sl', 'sw', 'ls').
    # Since we have the VALIDATION_GENE_LIST, we can use that as a strong indicator.
    # Also, the synthetic genomics file (T012) uses specific gene names.
    
    for _, row in feature_importance_df.iterrows():
        fname = row['feature']
        # Check if it matches known validation genes or other synthetic gene names
        # The synthetic data generator (T012) uses a specific list of 20 genes.
        # We can assume any feature in the top list that matches a known gene pattern is genomic.
        if fname in VALIDATION_GENE_LIST or fname in get_config()['gene_list']:
            genomic_features.append(fname)
        else:
            physiological_features.append(fname)
            
    return {
        'genomic': genomic_features,
        'physiological': physiological_features
    }

def generate_comparison_report(metrics: Dict[str, Any], importance_df: pd.DataFrame, 
                              classified_features: Dict[str, List[str]], 
                              output_path: str = "docs/reports/final_analysis.md") -> Dict[str, Any]:
    """
    Generates the final analysis report at docs/reports/final_analysis.md.
    Implements Validation Logic (SC-005):
    - Check if count of Validation Genes in Top 10 >= 3.
    """
    top_10_features = importance_df.head(TOP_N_FEATURES)['feature'].tolist()
    
    # Count validation genes in top 10
    validation_genes_in_top_10 = [g for g in top_10_features if g in VALIDATION_GENE_LIST]
    count_validation = len(validation_genes_in_top_10)
    
    validation_passed = count_validation >= MIN_VALIDATION_GENE_COUNT
    
    # Prepare report content
    report_lines = [
        "# Final Analysis Report: Drought Tolerance Prediction",
        "",
        "## 1. Model Comparison",
        "",
        f"**Best Model**: {metrics.get('best_model_name', 'Unknown')}",
        f"**Best AUC**: {metrics.get('best_model_auc', 0.0):.4f}",
        "",
        "### RF vs XGBoost Paired T-Test",
        "",
        "A paired t-test was performed on the cross-validation AUC scores to determine if the difference in performance between Random Forest and XGBoost is statistically significant.",
        "",
        f"- **t-statistic**: {metrics.get('t_statistic', 0.0):.4f}",
        f"- **p-value**: {metrics.get('p_value', 0.0):.4f}",
        "",
        "## 2. Feature Importance Analysis",
        "",
        "Permutation feature importance was calculated for the best model to identify the most predictive features.",
        "",
        "### Top 10 Features",
        "",
        "| Rank | Feature | Mean Importance | Std Dev |",
        "|------|---------|-----------------|---------|",
    ]
    
    for i, (_, row) in enumerate(importance_df.head(10).iterrows(), 1):
        report_lines.append(f"| {i} | {row['feature']} | {row['importance_mean']:.4f} | {row['importance_std']:.4f} |")
        
    report_lines.extend([
        "",
        "### Feature Classification",
        "",
        "Features were classified based on their biological origin:",
        "",
        f"- **Genomic Markers (Top 10)**: {', '.join(classified_features['genomic']) if classified_features['genomic'] else 'None'}",
        f"- **Physiological Traits (Top 10)**: {', '.join(classified_features['physiological']) if classified_features['physiological'] else 'None'}",
        "",
        "## 3. Validation Check (SC-005)",
        "",
        "The model's predictive power was validated against a set of known drought-responsive genes.",
        "",
        f"- **Validation Gene List Count**: {len(VALIDATION_GENE_LIST)} genes",
        f"- **Validation Genes in Top 10**: {count_validation}",
        f"- **Threshold**: >= {MIN_VALIDATION_GENE_COUNT}",
        f"- **Result**: {'**PASSED**' if validation_passed else '**FAILED**'}",
        "",
        "### Validation Genes Identified in Top 10:",
        ""
    ])
    
    if validation_genes_in_top_10:
        for gene in validation_genes_in_top_10:
            report_lines.append(f"- {gene}")
    else:
        report_lines.append("- None found in Top 10.")
        
    report_lines.extend([
        "",
        "## 4. Conclusion",
        "",
        "This analysis confirms the predictive capability of the model using both genomic and physiological data. " +
        ("The validation check passed, indicating the model successfully identified key drought-tolerance genes." if validation_passed else 
         "The validation check did not meet the threshold, suggesting further feature engineering or data collection may be needed.")
    ])
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    return {
        'validation_passed': validation_passed,
        'validation_count': count_validation,
        'top_10_features': top_10_features,
        'validation_genes_in_top_10': validation_genes_in_top_10
    }

def main():
    """
    Main entry point for T029: Generate final analysis report.
    """
    logger = DataPipelineLog()
    logger.info("Starting Final Analysis Report Generation (T029)")
    
    config = get_config()
    metrics_path = "data/logs/metrics.json"
    model_path = config.get('model_path', 'models/best_model.joblib')
    test_data_path = "data/processed/test_set.csv"
    
    try:
        # 1. Load Metrics
        metrics = load_cv_results(metrics_path)
        logger.info(f"Loaded metrics from {metrics_path}")
        
        # 2. Perform T-Test (if not already in metrics, do it now)
        # Assuming T027 might have saved this, but we re-calculate to ensure freshness if needed
        if 'p_value' not in metrics or 't_statistic' not in metrics:
            t_stat, p_val = perform_rf_vs_xgb_ttest(metrics)
            metrics['t_statistic'] = t_stat
            metrics['p_value'] = p_val
            # Save updated metrics if needed, but for report generation we just need the values
            logger.info(f"Performed t-test: t={t_stat:.4f}, p={p_val:.4f}")
        
        # 3. Load Test Data for Permutation Importance
        if not os.path.exists(test_data_path):
            raise FileNotFoundError(f"Test data not found at {test_data_path}. Run data/split.py first.")
        
        test_df = pd.read_csv(test_data_path)
        
        # Identify feature columns (exclude 'species_id' and 'label')
        # The exact column names depend on the ingest pipeline. 
        # We assume 'label' is the target and 'species_id' is an ID.
        # All other columns are features.
        feature_cols = [c for c in test_df.columns if c not in ['species_id', 'label', 'drought_label']]
        if 'drought_label' not in test_df.columns and 'label' in test_df.columns:
            # Handle potential naming variation
            pass 
        
        # Determine target column name
        target_col = 'label' if 'label' in test_df.columns else 'drought_label'
        
        X_test = test_df[feature_cols].values
        y_test = test_df[target_col].values
        
        logger.info(f"Loaded test data with {X_test.shape[0]} samples and {len(feature_cols)} features")
        
        # 4. Calculate Permutation Importance
        importance_df = calculate_permutation_importance(
            model_path, X_test, y_test, feature_cols, n_repeats=5, random_state=42
        )
        logger.info("Calculated permutation importance")
        
        # 5. Classify Features
        classified_features = classify_features(importance_df)
        logger.info(f"Classified features: {len(classified_features['genomic'])} genomic, {len(classified_features['physiological'])} physiological")
        
        # 6. Generate Report
        report_results = generate_comparison_report(metrics, importance_df, classified_features)
        logger.info(f"Generated report at docs/reports/final_analysis.md")
        logger.info(f"Validation Result: {'PASSED' if report_results['validation_passed'] else 'FAILED'}")
        
        # Log the validation outcome to the main log
        logger.record_analysis_result(
            task="T029",
            validation_passed=report_results['validation_passed'],
            validation_count=report_results['validation_count'],
            top_features=report_results['top_10_features']
        )
        
        print(f"Final Analysis Complete. Validation: {'PASSED' if report_results['validation_passed'] else 'FAILED'}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        raise

if __name__ == "__main__":
    main()
