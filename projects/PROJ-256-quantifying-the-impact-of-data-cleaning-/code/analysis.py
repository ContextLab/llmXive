import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from utils import setup_logging, pin_random_seed
from config import Config

logger = setup_logging("INFO")

def identify_numerical_columns(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()

def identify_categorical_columns(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

def run_t_test(df: pd.DataFrame, group_col: str, value_col: str) -> Dict[str, Any]:
    from scipy import stats
    groups = df.groupby(group_col)[value_col]
    if groups.ngroups < 2:
        return {"error": "Less than 2 groups"}
    
    group_names = list(groups.groups.keys())[:2]
    g1 = groups.get_group(group_names[0])
    g2 = groups.get_group(group_names[1])
    
    t_stat, p_val = stats.ttest_ind(g1, g2)
    return {
        "type": "t_test",
        "group_col": group_col,
        "value_col": value_col,
        "groups": [str(group_names[0]), str(group_names[1])],
        "t_statistic": float(t_stat),
        "p_value": float(p_val)
    }

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(), group2.std()
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1+n2-2))
    if pooled_std == 0:
        return 0.0
    return float((mean1 - mean2) / pooled_std)

def run_linear_regression(df: pd.DataFrame, outcome: str, predictors: List[str]) -> Dict[str, Any]:
    import statsmodels.api as sm
    y = df[outcome].dropna()
    X = df[predictors].loc[y.index]
    
    mask = ~X.isna().any(axis=1)
    y = y[mask]
    X = X[mask]
    
    if len(y) < 10:
        return {"error": "Insufficient samples"}
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    return {
        "type": "linear_regression",
        "outcome": outcome,
        "predictors": predictors,
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "coefficients": {str(k): float(v) for k, v in model.params.items()},
        "p_values": {str(k): float(v) for k, v in model.pvalues.items()}
    }

def load_datasets_from_raw(raw_dir: str) -> List[Tuple[str, pd.DataFrame]]:
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return datasets
    
    for f in os.listdir(raw_dir):
        if f.endswith('.csv'):
            path = os.path.join(raw_dir, f)
            try:
                df = pd.read_csv(path)
                datasets.append((f, df))
            except Exception as e:
                logger.error(f"Failed to load {f}: {e}")
    return datasets

def analyze_dataset(df: pd.DataFrame, dataset_name: str, outcome_col: str, predictor_cols: Optional[List[str]] = None) -> Dict[str, Any]:
    result = {
        "dataset_name": dataset_name,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "tests": {}
    }
    
    if outcome_col not in df.columns:
        logger.warning(f"Outcome column {outcome_col} not found in {dataset_name}")
        return result
    
    if not predictor_cols:
        predictor_cols = identify_numerical_columns(df)
        if outcome_col in predictor_cols:
            predictor_cols.remove(outcome_col)
    
    # T-test on first categorical column if available
    cat_cols = identify_categorical_columns(df)
    if cat_cols and pd.api.types.is_numeric_dtype(df[outcome_col]):
        cat_col = cat_cols[0]
        result["tests"][f"t_test_{cat_col}"] = run_t_test(df, cat_col, outcome_col)
    
    # Regression
    if predictor_cols:
        result["tests"]["linear_regression"] = run_linear_regression(df, outcome_col, predictor_cols[:3])
    
    return result

def run_baseline_analysis(raw_dir: str, output_file: str, analysis_config: Optional[Dict[str, Any]] = None, **kwargs) -> List[Dict[str, Any]]:
    """
    Runs baseline analysis on datasets in raw_dir.
    Accepts various call signatures:
    1. (raw_dir, output_file, analysis_config)
    2. (raw_dir, output_file, config) where config is a dict
    3. (temp_path, dataset_name=..., config={})
    """
    # Handle flexible arguments
    if analysis_config is None:
        analysis_config = kwargs.get('config', {})
    
    if not isinstance(analysis_config, dict):
        # If passed a Config object or similar, try to extract dict or treat as config
        if hasattr(analysis_config, 'get'):
            analysis_config = {k: analysis_config.get(k) for k in ['OUTCOME_COLUMN', 'PREDICTOR_COLUMNS'] if analysis_config.get(k)}
        else:
            analysis_config = {}

    outcome_col = analysis_config.get('OUTCOME_COLUMN') or kwargs.get('dataset_name') # Fallback logic for kwargs
    # If outcome_col is still None, try to infer or use a default
    if not outcome_col:
        # Try to load one file to guess
        raw_files = [f for f in os.listdir(raw_dir) if f.endswith('.csv')]
        if raw_files:
            sample_df = pd.read_csv(os.path.join(raw_dir, raw_files[0]))
            possible = ['target', 'outcome', 'label', 'class', 'activity', 'purchase']
            for p in possible:
                if p in sample_df.columns:
                    outcome_col = p
                    break
            if not outcome_col:
                outcome_col = sample_df.columns[-1]
    
    all_results = []
    datasets = load_datasets_from_raw(raw_dir)
    
    for name, df in datasets:
        logger.info(f"Analyzing {name}...")
        result = analyze_dataset(df, name, outcome_col)
        result['analysis_timestamp'] = datetime.now().isoformat()
        all_results.append(result)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Baseline metrics saved to {output_file}")
    return all_results

def main():
    config = Config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    analysis_config = {
        "OUTCOME_COLUMN": config.get("OUTCOME_COLUMN")
    }
    
    run_baseline_analysis(raw_dir, output_file, analysis_config)

if __name__ == "__main__":
    main()
