"""
Analysis module for statistical testing and baseline analysis.
Implements t-tests, linear regression, and effect size calculations.
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from sklearn.preprocessing import LabelEncoder

from utils import setup_logging, pin_random_seed
from config import Config

# Configure logger for this module
logger = logging.getLogger(__name__)

def load_datasets_from_raw(raw_dir: str) -> List[Tuple[pd.DataFrame, str]]:
    """
    Load all CSV files from the raw data directory.

    Args:
        raw_dir: Path to the raw data directory.

    Returns:
        List of tuples (DataFrame, dataset_name).
    """
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw data directory not found: {raw_dir}")
        return datasets

    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                dataset_name = os.path.splitext(filename)[0]
                datasets.append((df, dataset_name))
                logger.info(f"Loaded dataset: {dataset_name} with shape {df.shape}")
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")

    return datasets

def identify_numerical_columns(df: pd.DataFrame) -> List[str]:
    """Identify numerical columns in a DataFrame."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def identify_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Identify categorical columns in a DataFrame."""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

def run_t_test(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Run an independent samples t-test.

    Args:
        df: DataFrame containing the data.
        predictor_col: Name of the binary predictor column.
        outcome_col: Name of the outcome column.

    Returns:
        Dictionary with t-statistic, p-value, and confidence interval.
    """
    if predictor_col not in df.columns or outcome_col not in df.columns:
        logger.warning(f"Columns {predictor_col} or {outcome_col} not found in DataFrame.")
        return {}

    # Ensure binary predictor
    unique_vals = df[predictor_col].unique()
    if len(unique_vals) != 2:
        logger.warning(f"Predictor {predictor_col} is not binary. Skipping t-test.")
        return {}

    group1 = df[df[predictor_col] == unique_vals[0]][outcome_col].dropna()
    group2 = df[df[predictor_col] == unique_vals[1]][outcome_col].dropna()

    if len(group1) < 2 or len(group2) < 2:
        logger.warning(f"Insufficient data for t-test on {outcome_col}.")
        return {}

    t_stat, p_val = stats.ttest_ind(group1, group2)

    # Calculate 95% CI for difference in means
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(), group2.std()
    n1, n2 = len(group1), len(group2)

    se_diff = np.sqrt((std1**2 / n1) + (std2**2 / n2))
    ci_lower = (mean1 - mean2) - 1.96 * se_diff
    ci_upper = (mean1 - mean2) + 1.96 * se_diff

    # Validate p-value
    if not (0 < p_val < 1):
        logger.warning(f"P-value {p_val} out of expected range (0, 1) for {outcome_col}.")

    return {
        't_statistic': float(t_stat),
        'p_value': float(p_val),
        'ci_95': [float(ci_lower), float(ci_upper)],
        'ci_width': float(ci_upper - ci_lower),
        'n1': n1,
        'n2': n2
    }
    return result

def run_linear_regression(df: pd.DataFrame, predictor_cols: List[str], outcome_col: str) -> Dict[str, Any]:
    """
    Run a linear regression.

    Args:
        df: DataFrame containing the data.
        predictor_cols: List of predictor column names.
        outcome_col: Name of the outcome column.

    Returns:
        Dictionary with coefficients, R-squared, and p-values.
    """
    if outcome_col not in df.columns:
        logger.warning(f"Outcome column {outcome_col} not found.")
        return {}

    # Encode categorical predictors if any
    df_encoded = df.copy()
    categorical_cols = [c for c in predictor_cols if c in df_encoded.select_dtypes(include=['object', 'category']).columns]
    
    for col in categorical_cols:
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))

    X = df_encoded[predictor_cols].dropna()
    y = df_encoded.loc[X.index, outcome_col].dropna()
    X = X.loc[y.index]

    if len(X) < 2:
        logger.warning("Insufficient data for regression.")
        return {}

    X = sm.add_constant(X)
    model = sm.OLS(y, X)
    result = model.fit()

    if not np.isfinite(result.rsquared):
        logger.warning(f"R-squared is not finite for regression on {outcome_col}.")

    return {
        'coefficients': {
            'intercept': float(result.params.get('const', 0.0)),
            **{col: float(result.params[col]) for col in predictor_cols if col in result.params.index}
        },
        'r_squared': float(result.rsquared) if np.isfinite(result.rsquared) else None,
        'p_values': {col: float(result.pvalues[col]) for col in predictor_cols if col in result.pvalues.index},
        'n_observations': int(result.nobs)
    }

def compute_effect_size_cohen_d(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Optional[float]:
    """
    Compute Cohen's d effect size for a binary predictor.

    Args:
        df: DataFrame.
        predictor_col: Binary predictor column.
        outcome_col: Outcome column.

    Returns:
        Cohen's d value or None.
    """
    t_result = run_t_test(df, predictor_col, outcome_col)
    if not t_result or 't_statistic' not in t_result:
        return None

    # Cohen's d = t * sqrt(1/n1 + 1/n2)
    n1, n2 = t_result['n1'], t_result['n2']
    t_stat = t_result['t_statistic']
    d = t_stat * np.sqrt(1/n1 + 1/n2)
    return float(d)

def analyze_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    predictor_col: str,
    outcome_col: str,
    additional_predictors: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run a full analysis on a single dataset.

    Args:
        df: DataFrame.
        dataset_name: Name of the dataset.
        predictor_col: Primary binary predictor.
        outcome_col: Outcome variable.
        additional_predictors: Optional list of additional predictors for regression.

    Returns:
        Analysis results dictionary.
    """
    result = {
        'dataset_name': dataset_name,
        'dataset_size': len(df),
        't_test': {},
        'regression': {},
        'effect_size': None
    }

    # T-test
    t_result = run_t_test(df, predictor_col, outcome_col)
    if t_result:
        result['t_test'] = t_result

    # Effect size
    if t_result:
        result['effect_size'] = compute_effect_size_cohen_d(df, predictor_col, outcome_col)

    # Regression
    if additional_predictors:
        predictors = [predictor_col] + additional_predictors
        reg_result = run_linear_regression(df, predictors, outcome_col)
        if reg_result:
            result['regression'] = reg_result

    return result

def write_output(data: Dict[str, Any], output_path: str) -> bool:
    """Write analysis results to a JSON file."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Wrote output to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        return False

def run_baseline_analysis(
    input_data: Union[str, pd.DataFrame],
    output_file: Optional[str] = None,
    dataset_name: Optional[str] = None,
    config: Optional[Config] = None
) -> Union[bool, Dict[str, Any]]:
    """
    Run baseline analysis on raw or processed data.

    This function is overloaded to support multiple call patterns:
    1. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
    2. run_baseline_analysis(df, dataset_name=..., config=config) -> returns dict
    3. run_baseline_analysis(df_cleaned, dataset_name=..., config=config) -> returns dict

    Args:
        input_data: Path to raw directory OR DataFrame.
        output_file: Path to write JSON output (optional for DataFrame input).
        dataset_name: Name of the dataset (required for DataFrame input).
        config: Configuration object.

    Returns:
        True/False if writing file, or Dict if analyzing DataFrame.
    """
    if config:
        setup_logging(config.get("LOG_LEVEL", "INFO"))
        pin_random_seed(config.get("RANDOM_SEED", 42))

    # Case 1: Input is a path (string) -> load and analyze multiple datasets
    if isinstance(input_data, str):
        raw_dir = input_data
        datasets = load_datasets_from_raw(raw_dir)
        
        if not datasets:
            logger.error("No datasets found to analyze.")
            return False

        all_results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'datasets': []
        }

        for df, name in datasets:
            # Identify primary binary predictor and outcome
            num_cols = identify_numerical_columns(df)
            if len(num_cols) < 2:
                logger.warning(f"Skipping {name}: insufficient numerical columns.")
                continue

            # Assume first two numerical columns are predictor and outcome
            predictor = num_cols[0]
            outcome = num_cols[1]

            # Check if predictor is binary
            if len(df[predictor].unique()) != 2:
                logger.warning(f"Predictor {predictor} in {name} is not binary. Skipping.")
                continue

            analysis = analyze_dataset(df, name, predictor, outcome)
            all_results['datasets'].append(analysis)

        if output_file:
            return write_output(all_results, output_file)
        else:
            return all_results

    # Case 2: Input is a DataFrame -> analyze single dataset
    elif isinstance(input_data, pd.DataFrame):
        if not dataset_name:
            logger.error("dataset_name is required when input is a DataFrame.")
            return {}

        df = input_data
        num_cols = identify_numerical_columns(df)
        if len(num_cols) < 2:
            logger.warning(f"Insufficient numerical columns in {dataset_name}.")
            return {}

        predictor = num_cols[0]
        outcome = num_cols[1]

        # Check binary
        if len(df[predictor].unique()) != 2:
            logger.warning(f"Predictor {predictor} in {dataset_name} is not binary.")
            return {}

        analysis = analyze_dataset(df, dataset_name, predictor, outcome)
        
        if output_file:
            return write_output(analysis, output_file)
        else:
            return analysis

    else:
        logger.error(f"Unsupported input type: {type(input_data)}")
        return {}

def main():
    """Main entry point for baseline analysis script."""
    config = Config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("PROCESSED_DATA_PATH", "data/processed") + "/baseline_metrics.json"

    success = run_baseline_analysis(raw_dir, output_file, config=config)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())