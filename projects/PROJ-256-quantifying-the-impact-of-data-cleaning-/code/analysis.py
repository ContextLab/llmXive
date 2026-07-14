import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats
from sklearn.linear_model import LinearRegression
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def identify_numerical_columns(df: pd.DataFrame) -> List[str]:
    """Identify all numerical columns in a DataFrame."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def identify_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Identify all categorical (object/string) columns in a DataFrame."""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

def run_t_test(df: pd.DataFrame, outcome_col: str, group_col: str) -> Optional[Dict[str, float]]:
    """
    Perform an independent samples t-test.
    Assumes group_col has exactly 2 unique values.
    Returns p-value, confidence interval, and t-statistic.
    """
    try:
        if df[group_col].nunique() != 2:
            logger.warning(f"Group column '{group_col}' does not have exactly 2 unique values.")
            return None

        group1_val, group2_val = df[group_col].unique()
        group1 = df[df[group_col] == group1_val][outcome_col].dropna()
        group2 = df[df[group_col] == group2_val][outcome_col].dropna()

        if len(group1) < 2 or len(group2) < 2:
            logger.warning(f"Insufficient data for t-test in groups of '{group_col}'.")
            return None

        # Welch's t-test (does not assume equal variance)
        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)

        # Calculate 95% CI for the difference in means
        mean1, mean2 = group1.mean(), group2.mean()
        std1, std2 = group1.std(), group2.std()
        n1, n2 = len(group1), len(group2)

        # Standard error of the difference
        se_diff = np.sqrt((std1**2 / n1) + (std2**2 / n2))
        # Degrees of freedom (Welch-Satterthwaite equation)
        df_welch = ((std1**2 / n1) + (std2**2 / n2))**2 / \
                   ((std1**2 / n1)**2 / (n1 - 1) + (std2**2 / n2)**2 / (n2 - 1))
        
        # Critical t-value for 95% CI
        t_crit = stats.t.ppf(0.975, df_welch)
        ci_lower = (mean1 - mean2) - t_crit * se_diff
        ci_upper = (mean1 - mean2) + t_crit * se_diff

        # Validation
        if not (0 < p_val < 1):
            logger.warning(f"Invalid p-value {p_val} for t-test.")
            return None
        if not (np.isfinite(ci_lower) and np.isfinite(ci_upper)):
            logger.warning(f"Non-finite CI bounds for t-test.")
            return None

        return {
            "p_value": p_val,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "statistic": t_stat,
            "mean_diff": mean1 - mean2
        }
    except Exception as e:
        logger.error(f"Error running t-test: {e}")
        return None

def compute_effect_size_cohen_d(df: pd.DataFrame, outcome_col: str, group_col: str) -> Optional[float]:
    """
    Compute Cohen's d effect size for two groups.
    """
    try:
        if df[group_col].nunique() != 2:
            return None

        group1_val, group2_val = df[group_col].unique()
        group1 = df[df[group_col] == group1_val][outcome_col].dropna()
        group2 = df[df[group_col] == group2_val][outcome_col].dropna()

        if len(group1) < 2 or len(group2) < 2:
            return None

        mean1, mean2 = group1.mean(), group2.mean()
        std1, std2 = group1.std(), group2.std()
        n1, n2 = len(group1), len(group2)

        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0.0

        return (mean1 - mean2) / pooled_std
    except Exception as e:
        logger.error(f"Error computing Cohen's d: {e}")
        return None

def run_linear_regression(df: pd.DataFrame, outcome_col: str, predictor_col: str) -> Optional[Dict[str, Any]]:
    """
    Perform a simple linear regression.
    Returns p-value, CI, R-squared, and coefficients.
    """
    try:
        # Ensure numerical
        if not pd.api.types.is_numeric_dtype(df[outcome_col]) or not pd.api.types.is_numeric_dtype(df[predictor_col]):
            logger.warning(f"Columns for regression must be numerical.")
            return None

        # Drop rows with missing values in relevant columns
        clean_df = df[[outcome_col, predictor_col]].dropna()
        if len(clean_df) < 3:
            logger.warning("Insufficient data for linear regression.")
            return None

        X = clean_df[predictor_col].values.reshape(-1, 1)
        y = clean_df[outcome_col].values

        model = LinearRegression()
        model.fit(X, y)

        # Calculate R-squared
        r_squared = model.score(X, y)

        # Calculate p-value for the slope using scipy
        # Correlation test is equivalent for simple linear regression
        corr, p_val = stats.pearsonr(clean_df[predictor_col], clean_df[outcome_col])

        # Calculate CI for the slope (coefficient)
        # Standard error of the slope
        n = len(clean_df)
        x_mean = X.mean()
        ss_x = np.sum((X - x_mean)**2)
        y_pred = model.predict(X)
        mse = np.sum((y - y_pred)**2) / (n - 2)
        se_slope = np.sqrt(mse / ss_x)

        t_crit = stats.t.ppf(0.975, n - 2)
        slope = model.coef_[0]
        ci_lower = slope - t_crit * se_slope
        ci_upper = slope + t_crit * se_slope

        # Validation
        if not (0 < p_val < 1):
            logger.warning(f"Invalid p-value {p_val} for regression.")
            return None
        if not (np.isfinite(ci_lower) and np.isfinite(ci_upper)):
            logger.warning(f"Non-finite CI bounds for regression.")
            return None

        return {
            "p_value": p_val,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "r_squared": r_squared,
            "coefficients": [model.intercept_, slope]
        }
    except Exception as e:
        logger.error(f"Error running linear regression: {e}")
        return None

def load_datasets_from_raw(raw_dir: str) -> List[pd.DataFrame]:
    """Load all CSV files from a raw data directory."""
    if not os.path.exists(raw_dir):
        logger.error(f"Raw directory {raw_dir} does not exist.")
        return []
    
    datasets = []
    for file in os.listdir(raw_dir):
        if file.endswith('.csv'):
            try:
                df = pd.read_csv(os.path.join(raw_dir, file))
                datasets.append(df)
                logger.info(f"Loaded dataset: {file}")
            except Exception as e:
                logger.error(f"Failed to load {file}: {e}")
    return datasets

def analyze_dataset(df: pd.DataFrame, dataset_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform full analysis on a dataset: identify columns, run t-tests and regressions.
    """
    outcome_col = config.get("outcome_col")
    group_col = config.get("group_col")
    
    result = {
        "dataset_name": dataset_name,
        "timestamp": datetime.now().isoformat(),
        "numerical_columns": identify_numerical_columns(df),
        "categorical_columns": identify_categorical_columns(df),
        "analysis": {}
    }

    # T-Test
    if group_col and group_col in df.columns:
        t_res = run_t_test(df, outcome_col, group_col)
        if t_res:
            result["analysis"]["t_test"] = t_res
            result["analysis"]["t_test"]["effect_size_cohen_d"] = compute_effect_size_cohen_d(df, outcome_col, group_col)

    # Linear Regression
    # Try to find a numerical predictor if group_col isn't one
    predictor = group_col if (group_col and pd.api.types.is_numeric_dtype(df[group_col])) else None
    if not predictor:
        nums = identify_numerical_columns(df)
        if len(nums) >= 2:
            predictor = nums[0] # Use first numerical as predictor
            if outcome_col not in nums:
                outcome_col = nums[-1] # Use last as outcome

    if predictor and predictor in df.columns and outcome_col in df.columns:
        reg_res = run_linear_regression(df, outcome_col, predictor)
        if reg_res:
            result["analysis"]["linear_regression"] = reg_res

    return result

def run_baseline_analysis(raw_dir: str, output_file: str, config: Optional[Dict[str, Any]] = None, dataset_name: Optional[str] = None) -> bool:
    """
    Run baseline analysis on datasets in raw_dir and save to output_file.
    Handles both single dataset paths and directories.
    """
    if config is None:
        config = {}
    
    logger.info(f"Running baseline analysis on {raw_dir}")
    
    # Determine if raw_dir is a file or directory
    if os.path.isfile(raw_dir):
        datasets = [pd.read_csv(raw_dir)]
        names = [os.path.basename(raw_dir)]
    elif os.path.isdir(raw_dir):
        datasets = load_datasets_from_raw(raw_dir)
        names = [os.path.basename(f) for f in os.listdir(raw_dir) if f.endswith('.csv')]
    else:
        logger.error(f"Path {raw_dir} is not a valid file or directory.")
        return False

    if not datasets:
        logger.warning("No datasets found to analyze.")
        return False

    results = []
    for i, df in enumerate(datasets):
        name = names[i] if i < len(names) else f"dataset_{i}"
        # Override name if provided
        if dataset_name:
            name = dataset_name
        
        res = analyze_dataset(df, name, config)
        results.append(res)

    report = {
        "datasets": results,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "source_dir": raw_dir,
            "config": config
        }
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Baseline analysis saved to {output_file}")
    return True

def main():
    """Entry point for direct execution."""
    logger.info("Running analysis module directly.")
    # Example usage
    config = {
        "outcome_col": "target",
        "group_col": "group"
    }
    # This would typically be called by a task script
    # run_baseline_analysis("data/raw", "data/processed/baseline_test.json", config)

if __name__ == "__main__":
    import sys
    sys.exit(main())
