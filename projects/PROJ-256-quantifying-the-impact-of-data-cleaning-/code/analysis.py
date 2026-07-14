import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from utils import pin_random_seed, compute_file_checksum

logger = logging.getLogger(__name__)

def identify_numerical_columns(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=[np.number]).columns.tolist()

def identify_categorical_columns(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

def run_t_test(
    df: pd.DataFrame,
    outcome_col: str,
    group_col: str,
    group_a_val: Any,
    group_b_val: Any
) -> Dict[str, float]:
    """
    Perform an independent samples t-test between two groups.
    """
    pin_random_seed(42) # Ensure reproducibility for internal calcs if needed

    group_a = df[df[group_col] == group_a_val][outcome_col]
    group_b = df[df[group_col] == group_b_val][outcome_col]

    if len(group_a) < 2 or len(group_b) < 2:
        raise ValueError("Not enough samples in one or both groups for t-test.")

    t_stat, p_val = stats.ttest_ind(group_a, group_b, equal_var=False) # Welch's t-test

    # Calculate Cohen's d
    mean_a, mean_b = group_a.mean(), group_b.mean()
    std_a, std_b = group_a.std(), group_b.std()
    n_a, n_b = len(group_a), len(group_b)
    
    pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = (mean_a - mean_b) / pooled_std

    # 95% CI for difference in means
    # Using scipy's confint if available, otherwise manual approximation
    # scipy.stats.ttest_ind does not return CI directly in older versions, so we calculate manually
    diff = mean_a - mean_b
    se = np.sqrt((std_a**2 / n_a) + (std_b**2 / n_b))
    df_deg = (n_a + n_b - 2) # Simplified df for pooled, or use Welch-Satterthwaite
    # Using Welch-Satterthwaite for better accuracy with unequal variances
    df_welch = ( (std_a**2/n_a + std_b**2/n_b)**2 ) / ( (std_a**2/n_a)**2/(n_a-1) + (std_b**2/n_b)**2/(n_b-1) )
    t_crit = stats.t.ppf(0.975, df_welch)
    ci_lower = diff - t_crit * se
    ci_upper = diff + t_crit * se

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "effect_size_cohen_d": float(cohens_d),
        "n_a": int(n_a),
        "n_b": int(n_b)
    }

def run_linear_regression(
    df: pd.DataFrame,
    outcome_col: str,
    predictor_cols: List[str]
) -> Dict[str, Any]:
    """
    Run linear regression and return R^2, p-values, coefficients.
    """
    X = df[predictor_cols].values
    y = df[outcome_col].values

    # Handle missing values if any (drop rows with NaN in relevant columns)
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X_clean = X[mask]
    y_clean = y[mask]

    if len(X_clean) < len(predictor_cols) + 1:
        raise ValueError("Not enough data points for regression after cleaning.")

    model = LinearRegression()
    model.fit(X_clean, y_clean)

    y_pred = model.predict(X_clean)
    ss_res = np.sum((y_clean - y_pred) ** 2)
    ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)

    # Calculate p-values for coefficients using t-distribution
    # Residuals
    residuals = y_clean - y_pred
    dof = len(y_clean) - X_clean.shape[1] - 1
    mse = np.sum(residuals**2) / dof
    
    # Standard errors of coefficients
    # (X'X)^-1 * MSE
    try:
        XtX_inv = np.linalg.inv(X_clean.T @ X_clean)
        se = np.sqrt(np.diag(XtX_inv) * mse)
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix in regression. P-values may be unreliable.")
        se = np.zeros(len(predictor_cols))

    t_stats = model.coef_ / se
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), dof))

    return {
        "r_squared": float(r_squared),
        "coefficients": [float(c) for c in model.coef_],
        "intercept": float(model.intercept_),
        "p_values": [float(p) for p in p_values],
        "n_samples": int(len(y_clean))
    }

def compute_effect_size_cohen_d(
    group_a: pd.Series,
    group_b: pd.Series
) -> float:
    mean_a, mean_b = group_a.mean(), group_b.mean()
    std_a, std_b = group_a.std(), group_b.std()
    n_a, n_b = len(group_a), len(group_b)
    
    pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))
    if pooled_std == 0:
        return 0.0
    return (mean_a - mean_b) / pooled_std

def load_datasets_from_raw(raw_dir: str) -> List[Dict[str, pd.DataFrame]]:
    """
    Load all CSVs from raw_dir.
    """
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return datasets
    
    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            path = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(path)
                datasets.append({
                    "name": filename.replace('.csv', ''),
                    "path": path,
                    "df": df
                })
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
    return datasets

def analyze_dataset(
    df: pd.DataFrame,
    outcome_col: str,
    group_col: Optional[str] = None,
    predictor_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run baseline analysis (t-test, regression) on a single dataset.
    """
    results = {}
    
    # T-Test
    if group_col and group_col in df.columns:
        unique_vals = df[group_col].unique()
        if len(unique_vals) >= 2:
            try:
                t_res = run_t_test(df, outcome_col, group_col, unique_vals[0], unique_vals[1])
                results["t_test"] = t_res
            except Exception as e:
                results["t_test"] = {"error": str(e)}
    
    # Regression
    if predictor_cols:
        try:
            reg_res = run_linear_regression(df, outcome_col, predictor_cols)
            results["regression"] = reg_res
        except Exception as e:
            results["regression"] = {"error": str(e)}
    
    return results

def run_baseline_analysis(
    raw_dir: Union[str, pd.DataFrame],
    output_file: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    dataset_name: Optional[str] = None
) -> Union[bool, Dict[str, Any]]:
    """
    Flexible baseline analysis runner.
    
    Signatures supported:
    1. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
       - raw_dir: path to directory of CSVs
       - output_file: path to JSON output
    2. run_baseline_analysis(df, dataset_name, config) -> returns dict
       - df: pandas DataFrame
       - dataset_name: name for the result
    """
    if config is None:
        config = {}

    outcome_col = config.get("outcome_col", "outcome")
    group_col = config.get("group_col", None)
    predictor_cols = config.get("predictors", None)

    # Case 2: DataFrame input
    if isinstance(raw_dir, pd.DataFrame):
        if dataset_name is None:
            dataset_name = "unknown"
        df = raw_dir
        res = analyze_dataset(df, outcome_col, group_col, predictor_cols)
        return {
            "dataset_name": dataset_name,
            "analysis": res,
            "row_count": len(df),
            "checksum": "memory"
        }

    # Case 1: Directory input
    if isinstance(raw_dir, str) and os.path.isdir(raw_dir):
        datasets = load_datasets_from_raw(raw_dir)
        all_results = []
        for ds in datasets:
            res = analyze_dataset(ds["df"], outcome_col, group_col, predictor_cols)
            all_results.append({
                "dataset_name": ds["name"],
                "analysis": res,
                "row_count": len(ds["df"]),
                "checksum": compute_file_checksum(ds["path"])
            })
        
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2)
            return True
        return all_results

    # Fallback
    logger.error("Invalid arguments for run_baseline_analysis")
    return False

def main():
    """
    Main entry point for testing/running analysis directly.
    """
    setup_logging("INFO")
    # Example usage logic would go here if run as script
    logger.info("Analysis module loaded.")

if __name__ == "__main__":
    main()
