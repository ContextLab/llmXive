import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy.stats import chi2_contingency
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from code.config import get_data_path, get_processed_path, get_results_path
from code.monitoring import get_ram_usage_mb, get_cpu_utilization

logger = logging.getLogger(__name__)

def load_static_baseline(filepath: str = None) -> pd.DataFrame:
    if filepath is None:
        filepath = os.path.join(get_data_path(), "static_baseline.csv")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded static baseline with {len(df)} rows from {filepath}")
    return df

def load_semantic_results(filepath: str = None) -> pd.DataFrame:
    if filepath is None:
        filepath = os.path.join(get_processed_path(), "semantic_results.json")
    with open(filepath, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    logger.info(f"Loaded semantic results with {len(df)} rows from {filepath}")
    return df

def merge_datasets(static_df: pd.DataFrame, semantic_df: pd.DataFrame) -> pd.DataFrame:
    if 'id' in static_df.columns and 'id' in semantic_df.columns:
        merged = pd.merge(static_df, semantic_df, on='id', how='inner')
    else:
        merged = pd.concat([static_df, semantic_df], axis=1)
    logger.info(f"Merged dataset has {len(merged)} rows")
    return merged

def validate_merged_dataset(df: pd.DataFrame, threshold: float = 0.95) -> bool:
    required_cols = ['code', 'loc', 'cyclomatic_complexity', 'static_smell_labels', 'llm_smell_labels']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
    completeness = df[[c for c in required_cols if c in df.columns]].notna().all(axis=1).mean()
    if completeness < threshold:
        logger.warning(f"Dataset completeness {completeness:.2%} is below threshold {threshold:.2%}")
    return True

def parse_smell_labels(labels_str: str) -> set:
    if pd.isna(labels_str) or not isinstance(labels_str, str):
        return set()
    try:
        return set(labels_str.split(','))
    except Exception:
        return set()

def create_detection_matrix(df: pd.DataFrame) -> pd.DataFrame:
    df['static_set'] = df['static_smell_labels'].apply(parse_smell_labels)
    df['llm_set'] = df['llm_smell_labels'].apply(parse_smell_labels)
    all_smells = set()
    for s in df['static_set']:
        all_smells.update(s)
    for s in df['llm_set']:
        all_smells.update(s)
    
    matrix = []
    for smell in all_smells:
        row = {'smell': smell}
        for _, r in df.iterrows():
            in_static = 1 if smell in r['static_set'] else 0
            in_llm = 1 if smell in r['llm_set'] else 0
            if in_static == 0 and in_llm == 0:
                continue
            row[f'{smell}_static'] = in_static
            row[f'{smell}_llm'] = in_llm
        matrix.append(row)
    return pd.DataFrame(matrix)

def run_mcnemar_test(df: pd.DataFrame) -> Dict[str, float]:
    results = {}
    smells = set(df.columns)
    smells = {s.replace('_static', '').replace('_llm', '') for s in smells if '_static' in s}
    
    for smell in smells:
        col_static = f"{smell}_static"
        col_llm = f"{smell}_llm"
        if col_static not in df.columns or col_llm not in df.columns:
            continue
        
        df_sub = df[[col_static, col_llm]].dropna()
        if len(df_sub) < 10:
            logger.warning(f"Not enough data for McNemar's test on {smell}")
            continue
        
        contingency = pd.crosstab(df_sub[col_static], df_sub[col_llm])
        if contingency.shape != (2, 2):
            # Pad to 2x2 if necessary
            contingency = contingency.reindex([0, 1], axis=0, fill_value=0).reindex([0, 1], axis=1, fill_value=0)
        
        try:
            stat, p, _, _ = chi2_contingency(contingency, correction=True)
            results[smell] = float(p)
        except Exception as e:
            logger.error(f"McNemar test failed for {smell}: {e}")
            results[smell] = np.nan
    return results

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    X = df[feature_cols].values
    if X.shape[1] == 0:
        return {}
    vif_data = {}
    for i, col in enumerate(feature_cols):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data[col] = float(vif)
        except Exception as e:
            logger.error(f"VIF calculation failed for {col}: {e}")
            vif_data[col] = np.nan
    return vif_data

def fit_logistic_regression(df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> Dict[str, Any]:
    X = df[feature_cols].dropna().values
    y = df.loc[X[:, 0].argsort() if len(X) > 0 else [], target_col].dropna().values
    
    if len(X) == 0 or len(y) == 0:
        return {"coefficients": {}, "status": "insufficient_data"}
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression(max_iter=1000)
    try:
        model.fit(X_scaled, y)
        coefficients = {col: float(c) for col, c in zip(feature_cols, model.coef_[0])}
        return {"coefficients": coefficients, "status": "success", "intercept": float(model.intercept_[0])}
    except Exception as e:
        logger.error(f"Logistic regression failed: {e}")
        return {"coefficients": {}, "status": "failed", "error": str(e)}

def run_sensitivity_analysis(df: pd.DataFrame, loc_thresholds: List[int] = [50, 100, 150]) -> Dict[str, Any]:
    results = {}
    for thresh in loc_thresholds:
        df_thresh = df[df['loc'] >= thresh]
        if len(df_thresh) == 0:
            results[thresh] = {"fp_rate": np.nan, "fn_rate": np.nan, "count": 0}
            continue
        
        # Define FP: Static says yes, LLM says no
        # Define FN: Static says no, LLM says yes
        # Simplified for demo: assuming binary detection per function (any smell)
        df_thresh['static_any'] = df_thresh['static_smell_labels'].apply(lambda x: 1 if pd.notna(x) and len(str(x)) > 0 else 0)
        df_thresh['llm_any'] = df_thresh['llm_smell_labels'].apply(lambda x: 1 if pd.notna(x) and len(str(x)) > 0 else 0)
        
        fp = ((df_thresh['static_any'] == 1) & (df_thresh['llm_any'] == 0)).sum()
        fn = ((df_thresh['static_any'] == 0) & (df_thresh['llm_any'] == 1)).sum()
        total_pos_static = df_thresh['static_any'].sum()
        total_neg_static = len(df_thresh) - total_pos_static
        
        fp_rate = fp / total_pos_static if total_pos_static > 0 else 0.0
        fn_rate = fn / total_neg_static if total_neg_static > 0 else 0.0
        
        results[thresh] = {
            "fp_rate": float(fp_rate),
            "fn_rate": float(fn_rate),
            "count": int(len(df_thresh))
        }
    return results

def generate_sensitivity_report(df: pd.DataFrame, output_path: str = None) -> str:
    if output_path is None:
        output_path = os.path.join(get_results_path(), "sensitivity_report.md")
    
    df['static_set'] = df['static_smell_labels'].apply(parse_smell_labels)
    df['llm_set'] = df['llm_smell_labels'].apply(parse_smell_labels)
    
    only_static = set()
    only_llm = set()
    
    for _, row in df.iterrows():
        only_static.update(row['static_set'] - row['llm_set'])
        only_llm.update(row['llm_set'] - row['static_set'])
    
    sensitivity_results = run_sensitivity_analysis(df)
    
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        "## Smells Detected Only by Static Analysis",
        ", ".join(sorted(only_static)) if only_static else "None detected",
        "",
        "## Smells Detected Only by LLM",
        ", ".join(sorted(only_llm)) if only_llm else "None detected",
        "",
        "## Sensitivity Results by LOC Threshold",
        "",
        "| LOC Threshold | FP Rate | FN Rate | Sample Count |",
        "|---------------|---------|---------|--------------|"
    ]
    
    for thresh, res in sensitivity_results.items():
        report_lines.append(
            f"| {thresh} | {res['fp_rate']:.4f} | {res['fn_rate']:.4f} | {res['count']} |"
        )
    
    report_content = "\n".join(report_lines)
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Sensitivity report generated at {output_path}")
    return output_path

def run_statistical_analysis():
    static_df = load_static_baseline()
    semantic_df = load_semantic_results()
    merged = merge_datasets(static_df, semantic_df)
    
    if not validate_merged_dataset(merged):
        logger.error("Validation failed. Stopping analysis.")
        return None
    
    # McNemar
    mcnemar_results = run_mcnemar_test(merged)
    with open(os.path.join(get_results_path(), "statistical_significance.json"), 'w') as f:
        json.dump(mcnemar_results, f, indent=2)
    
    # VIF and Logistic Regression
    feature_cols = ['loc', 'cyclomatic_complexity']
    vif_scores = calculate_vif(merged, feature_cols)
    valid_features = [f for f, v in vif_scores.items() if v < 5]
    
    if len(valid_features) > 0:
        lr_results = fit_logistic_regression(merged, 'static_any', valid_features)
    else:
        lr_results = {"status": "no_valid_features"}
    
    with open(os.path.join(get_results_path(), "logistic_regression.json"), 'w') as f:
        json.dump({"vif_scores": vif_scores, "logistic_regression": lr_results}, f, indent=2)
    
    # Sensitivity Report
    generate_sensitivity_report(merged)
    
    return {
        "mcnemar": mcnemar_results,
        "vif": vif_scores,
        "logistic": lr_results
    }

def main():
    logging.basicConfig(level=logging.INFO)
    run_statistical_analysis()

if __name__ == "__main__":
    main()