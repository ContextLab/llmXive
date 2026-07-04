import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report

from config import get_path, get_data_path, get_processed_path, get_results_path, setup_logging

logger = logging.getLogger(__name__)

def load_static_baseline(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load the static baseline CSV."""
    if filepath is None:
        filepath = get_data_path("static_baseline.csv")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Static baseline not found at {filepath}")
    return pd.read_csv(filepath)

def load_semantic_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load the semantic results JSON as a DataFrame."""
    if filepath is None:
        filepath = get_processed_path("semantic_results.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Semantic results not found at {filepath}")
    with open(filepath, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

def merge_datasets(static_df: pd.DataFrame, semantic_df: pd.DataFrame) -> pd.DataFrame:
    """Merge static and semantic datasets on function_id."""
    # Ensure function_id is string for consistent joining
    static_df = static_df.copy()
    semantic_df = semantic_df.copy()
    
    if 'function_id' not in static_df.columns or 'function_id' not in semantic_df.columns:
        # Fallback if column names differ, assuming 'id' or index
        if 'id' in static_df.columns:
            static_df = static_df.rename(columns={'id': 'function_id'})
        if 'id' in semantic_df.columns:
            semantic_df = semantic_df.rename(columns={'id': 'function_id'})
    
    merged = pd.merge(static_df, semantic_df, on='function_id', how='inner')
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def validate_merged_dataset(df: pd.DataFrame, min_completeness: float = 0.95) -> bool:
    """Validate that the merged dataset has sufficient completeness."""
    required_cols = ['code', 'loc', 'cyclomatic_complexity', 'static_smell_labels', 'llm_labels']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check for nulls in key columns
    null_counts = df[required_cols].isnull().sum()
    if null_counts.any():
        logger.warning(f"Null values found in required columns: {null_counts[null_counts > 0].to_dict()}")
    
    non_null_rows = df[required_cols].dropna().shape[0]
    completeness = non_null_rows / len(df)
    logger.info(f"Dataset completeness: {completeness:.2%}")
    return completeness >= min_completeness

def parse_smell_labels(labels_str: str) -> List[str]:
    """Parse a string representation of labels into a list."""
    if pd.isna(labels_str) or not isinstance(labels_str, str):
        return []
    # Handle various formats: "['smell1', 'smell2']", "smell1, smell2", etc.
    labels_str = labels_str.strip("[]").strip("'\"").strip()
    if not labels_str:
        return []
    # Split by comma or space, handling quotes
    parts = [p.strip().strip("'\"") for p in labels_str.split(',')]
    return [p for p in parts if p]

def create_detection_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a binary detection matrix for each smell category.
    Columns: 'smell_<category>_static', 'smell_<category>_llm'
    Values: 1 if detected, 0 otherwise.
    """
    all_smells = set()
    for labels in df['static_smell_labels'].dropna():
        all_smells.update(parse_smell_labels(labels))
    for labels in df['llm_labels'].dropna():
        all_smells.update(parse_smell_labels(labels))
    
    smell_categories = sorted(list(all_smells))
    logger.info(f"Found {len(smell_categories)} unique smell categories: {smell_categories}")
    
    matrix_data = []
    for _, row in df.iterrows():
        static_labels = parse_smell_labels(row['static_smell_labels'])
        llm_labels = parse_smell_labels(row['llm_labels'])
        
        row_data = {'function_id': row.get('function_id', -1)}
        for smell in smell_categories:
            row_data[f'smell_{smell}_static'] = 1 if smell in static_labels else 0
            row_data[f'smell_{smell}_llm'] = 1 if smell in llm_labels else 0
        matrix_data.append(row_data)
    
    return pd.DataFrame(matrix_data)

def run_mcnemar_test(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform McNemar's test for each smell category.
    Returns a dictionary of results per category.
    """
    results = {}
    matrix_df = create_detection_matrix(df)
    
    smell_cols = [c for c in matrix_df.columns if c.startswith('smell_') and c.endswith('_static')]
    
    for col in smell_cols:
        smell_name = col.replace('smell_', '').replace('_static', '')
        llm_col = col.replace('_static', '_llm')
        
        if llm_col not in matrix_df.columns:
            logger.warning(f"Skipping {smell_name}: {llm_col} not found")
            continue
        
        static_col_data = matrix_df[col]
        llm_col_data = matrix_df[llm_col]
        
        # Create contingency table:
        # Rows: Static (0, 1)
        # Cols: LLM (0, 1)
        # We need counts of (0,0), (0,1), (1,0), (1,1)
        # McNemar's test focuses on discordant pairs: (0,1) and (1,0)
        
        contingency = pd.crosstab(static_col_data, llm_col_data)
        
        # Ensure 2x2 table
        if contingency.shape != (2, 2):
            # Reindex to ensure 0 and 1 exist
            contingency = contingency.reindex([0, 1], fill_value=0)
        
        b = contingency.loc[0, 1]  # Static=0, LLM=1
        c = contingency.loc[1, 0]  # Static=1, LLM=0
        
        if b + c == 0:
            results[smell_name] = {
                "p_value": None,
                "statistic": None,
                "discordant_pairs": 0,
                "message": "No discordant pairs found"
            }
            logger.info(f"McNemar for {smell_name}: No discordant pairs")
            continue
        
        # McNemar's test (exact or asymptotic)
        # Using scipy.stats.mcnemar
        try:
            stat, p_val = stats.mcnemar(contingency, exact=False) # asymptotic
            results[smell_name] = {
                "p_value": float(p_val),
                "statistic": float(stat),
                "discordant_pairs": int(b + c),
                "contingency_table": contingency.to_dict(),
                "significant": p_val < 0.05
            }
            logger.info(f"McNemar for {smell_name}: p={p_val:.4f}, stat={stat:.4f}")
        except Exception as e:
            logger.error(f"Error running McNemar for {smell_name}: {e}")
            results[smell_name] = {
                "p_value": None,
                "statistic": None,
                "error": str(e)
            }
    
    return results

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for given features."""
    X = df[feature_cols].dropna()
    if X.shape[0] < 2:
        return {col: float('inf') for col in feature_cols}
    
    vif_data = {}
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
    return vif_data

def fit_logistic_regression(df: pd.DataFrame, target_col: str, feature_cols: List[str], vif_threshold: float = 5.0) -> Dict[str, Any]:
    """Fit logistic regression, excluding high VIF features."""
    # Filter rows with complete data
    valid_df = df.dropna(subset=[target_col] + feature_cols)
    if valid_df.empty:
        return {"error": "No valid data for regression"}
    
    # Calculate VIF
    vif_scores = calculate_vif(valid_df, feature_cols)
    logger.info(f"VIF scores: {vif_scores}")
    
    # Filter features
    safe_features = [f for f, v in vif_scores.items() if v < vif_threshold]
    high_vif = [f for f, v in vif_scores.items() if v >= vif_threshold]
    
    if not safe_features:
        return {"error": "All features have VIF >= threshold", "vif_scores": vif_scores}
    
    if safe_features != feature_cols:
        logger.warning(f"Excluding high VIF features: {high_vif}")
    
    X = valid_df[safe_features]
    y = valid_df[target_col]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)
    
    return {
        "coefficients": dict(zip(safe_features, model.coef_[0].tolist())),
        "intercept": float(model.intercept_[0]),
        "vif_scores": vif_scores,
        "excluded_features": high_vif,
        "included_features": safe_features,
        "model_score": float(model.score(X_scaled, y))
    }

def run_sensitivity_analysis(df: pd.DataFrame, loc_thresholds: List[int] = [50, 100, 150]) -> Dict[str, Any]:
    """Run sensitivity analysis sweeping LOC thresholds."""
    results = {}
    for threshold in loc_thresholds:
        subset = df[df['loc'] >= threshold]
        if subset.empty:
            results[str(threshold)] = {"message": "No data points above threshold"}
            continue
        
        # Compare static vs LLM detection on this subset
        # We'll count agreement/disagreement
        agreement = 0
        total = len(subset)
        
        for _, row in subset.iterrows():
            static_set = set(parse_smell_labels(row['static_smell_labels']))
            llm_set = set(parse_smell_labels(row['llm_labels']))
            if static_set == llm_set:
                agreement += 1
        
        results[str(threshold)] = {
            "sample_size": total,
            "agreement_rate": agreement / total if total > 0 else 0,
            "agreement_count": agreement
        }
    return results

def generate_sensitivity_report(df: pd.DataFrame, loc_thresholds: List[int] = [50, 100, 150]) -> str:
    """Generate a markdown report for sensitivity analysis."""
    lines = ["# Sensitivity Analysis Report", ""]
    
    # Unique smells
    all_smells = set()
    for labels in df['static_smell_labels'].dropna():
        all_smells.update(parse_smell_labels(labels))
    for labels in df['llm_labels'].dropna():
        all_smells.update(parse_smell_labels(labels))
    
    lines.append(f"### Smell Categories Analyzed: {sorted(all_smells)}")
    lines.append("")
    
    # Static only vs LLM only
    static_only = set()
    llm_only = set()
    both = set()
    
    for _, row in df.iterrows():
        s_set = set(parse_smell_labels(row['static_smell_labels']))
        l_set = set(parse_smell_labels(row['llm_labels']))
        static_only.update(s_set - l_set)
        llm_only.update(l_set - s_set)
        both.update(s_set & l_set)
    
    lines.append("### Detection Patterns")
    lines.append(f"- Detected only by Static Analysis: {sorted(static_only)}")
    lines.append(f"- Detected only by LLM: {sorted(llm_only)}")
    lines.append(f"- Detected by Both: {sorted(both)}")
    lines.append("")
    
    # Threshold analysis
    lines.append("### LOC Threshold Sensitivity")
    sens_results = run_sensitivity_analysis(df, loc_thresholds)
    for thresh, res in sens_results.items():
        lines.append(f"- LOC >= {thresh}: Agreement = {res.get('agreement_rate', 0):.2%} (n={res.get('sample_size', 0)})")
    
    return "\n".join(lines)

def run_statistical_analysis(
    static_baseline_path: Optional[str] = None,
    semantic_results_path: Optional[str] = None,
    results_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Orchestrates the full statistical analysis pipeline.
    1. Load and merge data.
    2. Run McNemar's test.
    3. Run VIF and Logistic Regression.
    4. Run Sensitivity Analysis.
    5. Save results.
    """
    if results_dir is None:
        results_dir = get_results_path()
    
    logger.info("Starting Statistical Analysis Pipeline")
    
    # Load Data
    static_df = load_static_baseline(static_baseline_path)
    semantic_df = load_semantic_results(semantic_results_path)
    merged_df = merge_datasets(static_df, semantic_df)
    
    if not validate_merged_dataset(merged_df):
        logger.error("Validation failed. Aborting analysis.")
        return {"error": "Validation failed"}
    
    # 1. McNemar's Test
    logger.info("Running McNemar's Test...")
    mcnemar_results = run_mcnemar_test(merged_df)
    
    # Save McNemar results
    mcnemar_path = os.path.join(results_dir, "statistical_significance.json")
    with open(mcnemar_path, 'w') as f:
        json.dump(mcnemar_results, f, indent=2, default=str)
    logger.info(f"Saved McNemar results to {mcnemar_path}")
    
    # 2. Logistic Regression (Example: Predicting 'Complexity' or a specific smell)
    # For demonstration, we'll predict a synthetic 'high_complexity' target based on LOC
    merged_df['high_complexity'] = (merged_df['loc'] > 100).astype(int)
    
    features = ['loc', 'cyclomatic_complexity']
    if 'semantic_mean' in merged_df.columns:
        features.append('semantic_mean')
    
    logger.info(f"Running Logistic Regression with features: {features}...")
    lr_results = fit_logistic_regression(merged_df, 'high_complexity', features)
    
    # Save LR results
    lr_path = os.path.join(results_dir, "logistic_regression.json")
    with open(lr_path, 'w') as f:
        json.dump(lr_results, f, indent=2, default=str)
    logger.info(f"Saved Logistic Regression results to {lr_path}")
    
    # 3. Sensitivity Analysis
    logger.info("Running Sensitivity Analysis...")
    report_md = generate_sensitivity_report(merged_df)
    report_path = os.path.join(results_dir, "sensitivity_report.md")
    with open(report_path, 'w') as f:
        f.write(report_md)
    logger.info(f"Saved Sensitivity Report to {report_path}")
    
    return {
        "mcnemar": mcnemar_results,
        "logistic_regression": lr_results,
        "report_path": report_path
    }

def main():
    """Entry point for the script."""
    setup_logging()
    try:
        result = run_statistical_analysis()
        print("Analysis completed successfully.")
        print(f"McNemar results count: {len(result['mcnemar'])}")
        print(f"Logistic Regression features used: {result['logistic_regression'].get('included_features', [])}")
    except Exception as e:
        logger.exception("Analysis failed")
        raise

if __name__ == "__main__":
    main()