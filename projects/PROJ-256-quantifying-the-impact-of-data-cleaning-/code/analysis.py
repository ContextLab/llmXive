import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder

# Configure logger for this module
logger = logging.getLogger(__name__)

def load_datasets_from_raw(raw_dir: str) -> List[Tuple[pd.DataFrame, str]]:
    """
    Load all CSV files from the raw directory.
    Returns a list of tuples: (DataFrame, dataset_name).
    """
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return datasets
    
    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                dataset_name = os.path.splitext(filename)[0]
                datasets.append((df, dataset_name))
                logger.info(f"Loaded dataset: {dataset_name} ({len(df)} rows)")
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
    return datasets

def run_t_test(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Perform an independent t-test between two groups defined by predictor_col.
    Assumes predictor_col is binary or can be treated as such for the test.
    """
    if predictor_col not in df.columns or outcome_col not in df.columns:
        logger.error(f"Columns {predictor_col} or {outcome_col} not found.")
        return {"error": "Columns missing", "p_value": None, "ci": None, "statistic": None}

    # Drop rows with missing values in relevant columns
    clean_df = df[[predictor_col, outcome_col]].dropna()

    if clean_df[predictor_col].nunique() < 2:
        logger.warning(f"Not enough unique groups in {predictor_col} for t-test.")
        return {"error": "Insufficient groups", "p_value": None, "ci": None, "statistic": None}

    groups = clean_df.groupby(predictor_col)[outcome_col]
    if len(groups) < 2:
        return {"error": "Less than 2 groups", "p_value": None, "ci": None, "statistic": None}

    try:
        # Perform Welch's t-test (equal_var=False)
        t_stat, p_val = stats.ttest_ind(*[g.values for g in groups])
        
        # Calculate 95% CI for difference in means
        # Note: stats.ttest_ind does not return CI directly, we compute it
        mean_diff = groups.mean().diff().iloc[-1] # Approximate diff
        # Better CI calculation:
        g1, g2 = list(groups)
        n1, n2 = len(g1), len(g2)
        m1, m2 = np.mean(g1), np.mean(g2)
        v1, v2 = np.var(g1, ddof=1), np.var(g2, ddof=1)
        
        se = np.sqrt(v1/n1 + v2/n2)
        dof = (v1/n1 + v2/n2)**2 / ((v1/n1)**2/(n1-1) + (v2/n2)**2/(n2-1))
        t_crit = stats.t.ppf(0.975, dof)
        ci_low = (m1 - m2) - t_crit * se
        ci_high = (m1 - m2) + t_crit * se

        # Validate p-value
        if not (0 < p_val < 1):
            logger.warning(f"Invalid p-value {p_val} for {predictor_col} vs {outcome_col}")
            p_val = np.clip(p_val, 1e-10, 1 - 1e-10)

        return {
            "p_value": float(p_val),
            "ci": [float(ci_low), float(ci_high)],
            "statistic": float(t_stat),
            "n": int(n1 + n2)
        }
    except Exception as e:
        logger.error(f"T-test failed: {e}")
        return {"error": str(e), "p_value": None, "ci": None, "statistic": None}

def run_linear_regression(df: pd.DataFrame, predictor_cols: List[str], outcome_col: str) -> Dict[str, Any]:
    """
    Perform linear regression.
    """
    if outcome_col not in df.columns:
        logger.error(f"Outcome column {outcome_col} not found.")
        return {"error": "Outcome missing", "r_squared": None, "coefficients": [], "p_values": []}

    # Encode categorical predictors if necessary
    df_processed = df.copy()
    for col in predictor_cols:
        if col not in df_processed.columns:
            logger.error(f"Predictor column {col} not found.")
            return {"error": "Predictor missing", "r_squared": None, "coefficients": [], "p_values": []}
        if df_processed[col].dtype == 'object':
            le = LabelEncoder()
            df_processed[col] = le.fit_transform(df_processed[col].astype(str))

    X = df_processed[predictor_cols].dropna()
    y = df_processed.loc[X.index, outcome_col].dropna()
    
    # Align X and y after dropna
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    if len(X) < 2 or len(predictor_cols) == 0:
        logger.warning("Insufficient data for regression.")
        return {"error": "Insufficient data", "r_squared": None, "coefficients": [], "p_values": []}

    try:
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        # Calculate p-values for coefficients (approximate using t-distribution)
        n = len(y)
        p = len(predictor_cols)
        dof = n - p - 1
        
        # Standard errors
        if dof <= 0:
            p_values = [0.0] * len(predictor_cols)
        else:
            mse = ss_res / dof
            X_with_intercept = np.c_[np.ones(len(X)), X]
            try:
                cov_matrix = mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept)
                std_errors = np.sqrt(np.diag(cov_matrix))
                
                # t-stats for coefficients (excluding intercept for p-values list if desired, but usually include all)
                # Here we return p-values for predictors only (index 1 onwards in model)
                coefs = model.coef_
                t_stats = coefs / std_errors[1:] # Skip intercept
                p_values = [2 * (1 - stats.t.cdf(abs(t), dof)) for t in t_stats]
            except np.linalg.LinAlgError:
                logger.warning("Singular matrix in regression, p-values not computed.")
                p_values = [0.0] * len(predictor_cols)

        return {
            "r_squared": float(r_squared),
            "coefficients": [float(c) for c in model.coef_],
            "p_values": [float(p) for p in p_values],
            "n": int(n)
        }
    except Exception as e:
        logger.error(f"Regression failed: {e}")
        return {"error": str(e), "r_squared": None, "coefficients": [], "p_values": []}

def compute_effect_size_cohen_d(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Compute Cohen's d for the difference in means between two groups.
    """
    if predictor_col not in df.columns or outcome_col not in df.columns:
        return {"error": "Columns missing", "cohens_d": None}

    clean_df = df[[predictor_col, outcome_col]].dropna()
    if clean_df[predictor_col].nunique() < 2:
        return {"error": "Insufficient groups", "cohens_d": None}

    groups = list(clean_df.groupby(predictor_col)[outcome_col])
    if len(groups) < 2:
        return {"error": "Less than 2 groups", "cohens_d": None}

    g1, g2 = groups[0].values, groups[1].values
    n1, n2 = len(g1), len(g2)
    m1, m2 = np.mean(g1), np.mean(g2)
    v1, v2 = np.var(g1, ddof=1), np.var(g2, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return {"error": "Zero pooled std", "cohens_d": 0.0}

    d = (m1 - m2) / pooled_std
    return {"cohens_d": float(d), "n": int(n1 + n2)}

def analyze_dataset(df: pd.DataFrame, dataset_name: str, config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Run baseline analysis (t-test and regression) on a single dataset.
    """
    if config is None:
        config = {}
    
    # Default columns if not specified
    outcome_col = config.get("OUTCOME_COLUMN", "outcome")
    predictor_col = config.get("PREDICTOR_COLUMN", "predictor")
    regression_predictors = config.get("REGRESSION_PREDICTORS", ["predictor"])
    
    result = {
        "dataset_name": dataset_name,
        "n_rows": len(df),
        "t_test": run_t_test(df, predictor_col, outcome_col),
        "regression": run_linear_regression(df, regression_predictors, outcome_col),
        "effect_size": compute_effect_size_cohen_d(df, predictor_col, outcome_col)
    }
    return result

def run_baseline_analysis(df: Union[str, pd.DataFrame, None], 
                          output_file: Optional[str] = None, 
                          dataset_name: Optional[str] = None,
                          config: Optional[Dict] = None) -> Union[Dict[str, Any], bool]:
    """
    Main entry point for baseline analysis.
    
    Handles multiple call signatures:
    1. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
    2. run_baseline_analysis(df, dataset_name=..., config=config) -> returns dict
    3. run_baseline_analysis(df_cleaned, dataset_name=..., config=config) -> returns dict
    """
    if config is None:
        config = {}

    # Case 1: Directory input (run on all datasets in raw_dir)
    if isinstance(df, str) and output_file is not None:
        raw_dir = df
        datasets = load_datasets_from_raw(raw_dir)
        if not datasets:
            logger.warning(f"No datasets found in {raw_dir}")
            return False

        all_results = []
        for d_df, d_name in datasets:
            res = analyze_dataset(d_df, d_name, config)
            all_results.append(res)

        output_data = {
            "generated_at": datetime.now().isoformat(),
            "datasets": all_results
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Wrote baseline metrics to {output_file}")
        return True

    # Case 2 & 3: DataFrame input (single dataset analysis)
    if isinstance(df, pd.DataFrame):
        if dataset_name is None:
            dataset_name = "unknown_dataset"
        
        result = analyze_dataset(df, dataset_name, config)
        
        # If output_file is provided, write it (for single dataset mode)
        if output_file:
            output_data = {
                "generated_at": datetime.now().isoformat(),
                "datasets": [result]
            }
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Wrote baseline metrics to {output_file}")
            return {"success": True, "result": result}
        
        return result

    # Fallback
    logger.error("Invalid arguments for run_baseline_analysis")
    return False

def main():
    """
    Main entry point for script execution.
    """
    setup_logging("INFO")
    config = {"OUTCOME_COLUMN": "outcome", "PREDICTOR_COLUMN": "predictor"}
    success = run_baseline_analysis("data/raw", "data/processed/baseline_metrics.json", config=config)
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
