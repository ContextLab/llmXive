import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from scipy import stats
import statsmodels.api as sm

logger = logging.getLogger(__name__)

def identify_numerical_columns(df: Union[pd.DataFrame, Any]) -> List[str]:
    """
    Identify numerical columns in a DataFrame.
    Handles both DataFrame objects and other input types gracefully.
    """
    if isinstance(df, str):
        logger.warning(f"Received string instead of DataFrame: {df}")
        return []
    if not isinstance(df, pd.DataFrame):
        logger.warning(f"Expected pandas DataFrame, got {type(df)}")
        return []

    return df.select_dtypes(include=[np.number]).columns.tolist()

def identify_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Identify categorical columns in a DataFrame."""
    if not isinstance(df, pd.DataFrame):
        return []
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

def run_t_test(df: pd.DataFrame, group_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Run an independent samples t-test.
    Returns p-value, confidence interval, and effect size.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {'p_value': None, 'ci': None, 't_statistic': None}

    try:
        groups = df[group_col].unique()
        if len(groups) < 2:
            return {'p_value': None, 'ci': None, 't_statistic': None}

        # Extract data for each group
        group_data = [df[df[group_col] == g][outcome_col].dropna() for g in groups]

        if any(len(g) < 2 for g in group_data):
            return {'p_value': None, 'ci': None, 't_statistic': None}

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(*group_data)

        # Calculate confidence interval (95%)
        # Using the difference in means
        mean1, mean2 = group_data[0].mean(), group_data[1].mean()
        diff = mean1 - mean2

        # Pooled standard error
        n1, n2 = len(group_data[0]), len(group_data[1])
        var1, var2 = group_data[0].var(), group_data[1].var()
        se = np.sqrt((var1 / n1) + (var2 / n2))

        # 95% CI
        ci_low = diff - 1.96 * se
        ci_high = diff + 1.96 * se

        return {
            'p_value': float(p_value),
            'ci': [float(ci_low), float(ci_high)],
            't_statistic': float(t_stat),
            'n1': n1,
            'n2': n2
        }

    except Exception as e:
        logger.warning(f"Error running t-test: {e}")
        return {'p_value': None, 'ci': None, 't_statistic': None}

def run_linear_regression(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Run a simple linear regression.
    Returns coefficients, R-squared, and p-values.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {'r_squared': None, 'coefficients': [], 'p_values': []}

    try:
        X = df[predictor_col].dropna()
        y = df[outcome_col].dropna()

        # Ensure same length
        min_len = min(len(X), len(y))
        X = X.iloc[:min_len]
        y = y.iloc[:min_len]

        if len(X) < 2:
            return {'r_squared': None, 'coefficients': [], 'p_values': []}

        # Add constant for intercept
        X_with_const = sm.add_constant(X)

        # Fit model
        model = sm.OLS(y, X_with_const).fit()

        return {
            'r_squared': float(model.rsquared),
            'coefficients': [float(c) for c in model.params],
            'p_values': [float(p) for p in model.pvalues],
            'n_obs': int(model.nobs)
        }

    except Exception as e:
        logger.warning(f"Error running linear regression: {e}")
        return {'r_squared': None, 'coefficients': [], 'p_values': []}

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> Optional[float]:
    """Compute Cohen's d effect size."""
    if len(group1) < 2 or len(group2) < 2:
        return None

    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(), group2.std()

    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return None

    return (mean1 - mean2) / pooled_std

def load_datasets_from_raw(raw_dir: str) -> List[Dict[str, Any]]:
    """Load datasets from the raw data directory."""
    datasets = []

    if not os.path.exists(raw_dir):
        logger.warning(f"Raw data directory not found: {raw_dir}")
        return datasets

    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                datasets.append({
                    'name': filename.replace('.csv', ''),
                    'path': filepath,
                    'df': df,
                    'n_rows': len(df)
                })
            except Exception as e:
                logger.warning(f"Error loading {filename}: {e}")

    return datasets

def analyze_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    outcome_col: str,
    group_col: str
) -> Dict[str, Any]:
    """
    Perform statistical analysis on a dataset.
    Returns t-test results, regression results, and effect sizes.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {
            'dataset_name': dataset_name,
            't_test': {'p_value': None, 'ci': None},
            'regression': {'r_squared': None, 'coefficients': []},
            'effect_size': None
        }

    # Identify numerical columns if not specified
    numerical_cols = identify_numerical_columns(df)
    if not numerical_cols:
        logger.warning(f"No numerical columns found in {dataset_name}")
        return {
            'dataset_name': dataset_name,
            't_test': {'p_value': None, 'ci': None},
            'regression': {'r_squared': None, 'coefficients': []},
            'effect_size': None
        }

    # If outcome_col or group_col not provided, try to infer
    if outcome_col not in df.columns:
        if outcome_col in numerical_cols:
            pass  # Use inferred
        else:
            outcome_col = numerical_cols[0]

    if group_col not in df.columns:
        categorical_cols = identify_categorical_columns(df)
        if categorical_cols:
            group_col = categorical_cols[0]
        else:
            # If no categorical column, use first numerical as predictor
            group_col = None

    result = {
        'dataset_name': dataset_name,
        'n_rows': len(df),
        'outcome_col': outcome_col,
        'group_col': group_col
    }

    # T-test
    if group_col and group_col in df.columns:
        t_test_result = run_t_test(df, group_col, outcome_col)
        result['t_test'] = t_test_result

        # Effect size
        if t_test_result.get('p_value') is not None:
            groups = df[group_col].unique()
            if len(groups) >= 2:
                group1_data = df[df[group_col] == groups[0]][outcome_col]
                group2_data = df[df[group_col] == groups[1]][outcome_col]
                effect_size = compute_effect_size_cohen_d(group1_data, group2_data)
                result['effect_size'] = effect_size
    else:
        result['t_test'] = {'p_value': None, 'ci': None}

    # Linear regression (if we have a numeric group/predictor)
    if group_col and group_col in df.columns and pd.api.types.is_numeric_dtype(df[group_col]):
        reg_result = run_linear_regression(df, group_col, outcome_col)
        result['regression'] = reg_result
    else:
        # Try first numerical column as predictor
        if len(numerical_cols) > 1:
            predictor = numerical_cols[1] if numerical_cols[0] == outcome_col else numerical_cols[0]
            reg_result = run_linear_regression(df, predictor, outcome_col)
            result['regression'] = reg_result
        else:
            result['regression'] = {'r_squared': None, 'coefficients': []}

    return result

def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """Save data to a JSON file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved results to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file: {e}")
        return False

def run_baseline_analysis(
    input_data: Union[str, pd.DataFrame, Dict[str, Any]],
    output_file: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Union[bool, Dict[str, Any]]:
    """
    Run baseline analysis on a dataset or directory of datasets.
    This function is flexible to accept different input types:
    - str: path to a CSV file or directory
    - pd.DataFrame: a DataFrame to analyze
    - Dict: with 'df' key containing DataFrame and 'name' key for dataset name
    """
    if config is None:
        config = {}

    datasets_to_analyze = []

    # Handle different input types
    if isinstance(input_data, str):
        # Could be a file path or directory
        if os.path.isdir(input_data):
            # Load all CSVs from directory
            datasets_to_analyze = load_datasets_from_raw(input_data)
        elif os.path.isfile(input_data) and input_data.endswith('.csv'):
            # Load single file
            try:
                df = pd.read_csv(input_data)
                datasets_to_analyze = [{
                    'name': os.path.basename(input_data).replace('.csv', ''),
                    'path': input_data,
                    'df': df,
                    'n_rows': len(df)
                }]
            except Exception as e:
                logger.error(f"Failed to load CSV: {e}")
                return False
        else:
            logger.error(f"Invalid input path: {input_data}")
            return False

    elif isinstance(input_data, pd.DataFrame):
        # Single DataFrame
        datasets_to_analyze = [{
            'name': config.get('dataset_name', 'unknown'),
            'df': input_data,
            'n_rows': len(input_data)
        }]

    elif isinstance(input_data, dict):
        # Dict with df and name
        if 'df' in input_data:
            datasets_to_analyze = [{
                'name': input_data.get('name', 'unknown'),
                'df': input_data['df'],
                'n_rows': len(input_data['df'])
            }]
        else:
            logger.error("Dict input missing 'df' key")
            return False

    else:
        logger.error(f"Unsupported input type: {type(input_data)}")
        return False

    if not datasets_to_analyze:
        logger.warning("No datasets to analyze")
        return False

    # Configuration for analysis
    outcome_col = config.get('outcome_col', 'outcome')
    group_col = config.get('group_col', 'group')

    # Analyze each dataset
    results = {
        'generated_at': datetime.now().isoformat(),
        'datasets': []
    }

    for dataset_info in datasets_to_analyze:
        df = dataset_info['df']
        dataset_name = dataset_info['name']

        logger.info(f"Analyzing dataset: {dataset_name}")

        # Analyze
        analysis_result = analyze_dataset(df, dataset_name, outcome_col, group_col)

        # Add dataset info
        analysis_result['dataset_name'] = dataset_name
        analysis_result['n_rows'] = len(df)
        analysis_result['outcome_col'] = outcome_col
        analysis_result['group_col'] = group_col

        results['datasets'].append(analysis_result)

    # Save if output file specified
    if output_file:
        success = save_json_file(results, output_file)
        if success:
            logger.info(f"Baseline analysis complete. Results saved to {output_file}")
            return True
        else:
            return False

    return results

def main():
    """Main entry point for analysis module."""
    logger.info("Analysis module loaded")
    # This module is typically called by other scripts
    return True

if __name__ == "__main__":
    main()
