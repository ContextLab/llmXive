"""
Analysis module for statistical inference.

Provides functions for loading datasets, identifying columns, running t-tests,
linear regressions, and computing effect sizes.
"""
import os
import json
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union, Callable

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.outliers_influence import OLSInfluence

from config import Config

logger = logging.getLogger(__name__)

def load_datasets_from_raw(raw_dir: str) -> List[Tuple[str, pd.DataFrame]]:
    """
    Load all CSV files from the raw directory.
    Returns a list of tuples (dataset_name, dataframe).
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
                name = os.path.splitext(filename)[0]
                datasets.append((name, df))
                logger.info(f"Loaded dataset: {name} with shape {df.shape}")
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
    return datasets

def identify_numerical_columns(df: pd.DataFrame) -> List[str]:
    """Identify numerical columns in a DataFrame."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def identify_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Identify categorical columns in a DataFrame."""
    return df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

def run_t_test(df: pd.DataFrame, group_col: str, value_col: str, 
               groups: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run an independent t-test on a specific column between groups.
    
    Args:
        df: DataFrame
        group_col: Column name containing group labels
        value_col: Column name containing values to test
        groups: Optional list of specific groups to include. If None, uses all.
    
    Returns:
        Dictionary with t-statistic, p-value, and group means.
    """
    if groups:
        sub_df = df[df[group_col].isin(groups)]
    else:
        sub_df = df
    
    if sub_df.empty:
        logger.warning(f"No data found for t-test on {value_col} with groups {groups}")
        return {"t_statistic": None, "p_value": None, "means": {}, "n": 0}

    unique_groups = sub_df[group_col].unique()
    if len(unique_groups) < 2:
        logger.warning(f"Less than 2 groups found for t-test: {unique_groups}")
        return {"t_statistic": None, "p_value": None, "means": {}, "n": 0}

    # Filter to the two largest groups if more than 2, or use all if exactly 2
    # For simplicity in this pipeline, we assume binary comparison or take first two
    if len(unique_groups) > 2:
        logger.info(f"More than 2 groups ({len(unique_groups)}) found. Comparing first two: {unique_groups[:2]}")
        groups_to_compare = unique_groups[:2]
    else:
        groups_to_compare = unique_groups

    try:
        vals_1 = sub_df[sub_df[group_col] == groups_to_compare[0]][value_col].dropna()
        vals_2 = sub_df[sub_df[group_col] == groups_to_compare[1]][value_col].dropna()

        if len(vals_1) < 2 or len(vals_2) < 2:
            logger.warning(f"Insufficient data for t-test in groups {groups_to_compare}")
            return {"t_statistic": None, "p_value": None, "means": {}, "n": 0}

        t_stat, p_val = stats.ttest_ind(vals_1, vals_2)
        return {
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "means": {str(groups_to_compare[0]): float(vals_1.mean()), str(groups_to_compare[1]): float(vals_2.mean())},
            "n": len(vals_1) + len(vals_2)
        }
    except Exception as e:
        logger.error(f"Error running t-test: {e}")
        return {"t_statistic": None, "p_value": None, "means": {}, "n": 0}

def run_linear_regression(df: pd.DataFrame, predictor: str, outcome: str) -> Dict[str, Any]:
    """
    Run a simple linear regression: outcome ~ predictor.
    
    Returns:
        Dictionary with coefficients, R-squared, and p-value for predictor.
    """
    if predictor not in df.columns or outcome not in df.columns:
        logger.error(f"Columns {predictor} or {outcome} not found in dataset.")
        return {"coefficients": {}, "r_squared": None, "p_value": None}

    sub_df = df[[predictor, outcome]].dropna()
    if len(sub_df) < 2:
        logger.warning("Insufficient data for regression.")
        return {"coefficients": {}, "r_squared": None, "p_value": None}

    try:
        formula = f"{outcome} ~ {predictor}"
        model = ols(formula, data=sub_df).fit()
        
        # Extract p-value for the predictor (not intercept)
        p_val = model.pvalues.iloc[1] if len(model.pvalues) > 1 else None
        r_sq = model.rsquared
        
        coeffs = {}
        for i, name in enumerate(model.params.index):
            coeffs[name] = float(model.params.iloc[i])

        return {
            "coefficients": coeffs,
            "r_squared": float(r_sq),
            "p_value": float(p_val) if p_val is not None else None,
            "n": len(sub_df)
        }
    except Exception as e:
        logger.error(f"Error running regression: {e}")
        return {"coefficients": {}, "r_squared": None, "p_value": None}

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> Optional[float]:
    """Compute Cohen's d effect size between two groups."""
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(), group2.std()
    n1, n2 = len(group1), len(group2)
    
    if n1 < 2 or n2 < 2 or (std1 == 0 and std2 == 0):
        return None

    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return None
        
    return float((mean1 - mean2) / pooled_std)

def analyze_dataset(df: pd.DataFrame, dataset_name: str, config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Perform a full statistical analysis on a dataset.
    Identifies a suitable outcome variable (numerical) and predictor (categorical or numerical).
    """
    numerical_cols = identify_numerical_columns(df)
    categorical_cols = identify_categorical_columns(df)
    
    if not numerical_cols:
        logger.warning(f"No numerical columns found in {dataset_name}")
        return {"dataset_name": dataset_name, "error": "No numerical columns"}

    # Simple heuristic: pick the last numerical column as outcome
    outcome_col = numerical_cols[-1]
    results = {
        "dataset_name": dataset_name,
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "outcome_variable": outcome_col,
        "t_tests": [],
        "regressions": [],
        "effect_sizes": []
    }

    # If we have categorical columns, run t-tests
    if categorical_cols:
        # Pick the first categorical column with > 1 unique value
        for cat_col in categorical_cols:
            if df[cat_col].nunique() > 1:
                # Try to run t-test on outcome_col vs cat_col
                # We need to ensure the outcome_col is numeric (it is)
                # We need to ensure cat_col has at least 2 groups
                t_res = run_t_test(df, cat_col, outcome_col)
                if t_res['p_value'] is not None:
                    results['t_tests'].append({
                        "predictor": cat_col,
                        "outcome": outcome_col,
                        "result": t_res
                    })
                    
                    # Compute effect size if we have two groups
                    unique_vals = df[cat_col].unique()
                    if len(unique_vals) >= 2:
                        g1 = df[df[cat_col] == unique_vals[0]][outcome_col]
                        g2 = df[df[cat_col] == unique_vals[1]][outcome_col]
                        d = compute_effect_size_cohen_d(g1, g2)
                        if d is not None:
                            results['effect_sizes'].append({
                                "predictor": cat_col,
                                "outcome": outcome_col,
                                "cohens_d": d
                            })
                break # Just do one t-test for simplicity in this MVP

    # Run regression with the first other numerical column as predictor
    other_numerical = [c for c in numerical_cols if c != outcome_col]
    if other_numerical:
        pred_col = other_numerical[0]
        reg_res = run_linear_regression(df, pred_col, outcome_col)
        if reg_res['r_squared'] is not None:
            results['regressions'].append({
                "predictor": pred_col,
                "outcome": outcome_col,
                "result": reg_res
            })

    return results

def write_output(data: Dict[str, Any], filepath: str):
    """Write analysis results to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Results written to {filepath}")

def run_baseline_analysis(
    input_data: Union[str, pd.DataFrame], 
    output_file: Optional[str] = None,
    dataset_name: Optional[str] = None,
    config: Optional[Config] = None
) -> Union[Dict[str, Any], bool]:
    """
    Main entry point for baseline analysis.
    
    Handles multiple call signatures:
    1. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
       - input_data is a directory path string
    2. run_baseline_analysis(df, dataset_name=..., config=config) -> returns dict
       - input_data is a DataFrame
    3. run_baseline_analysis(filepath, dataset_name=..., config=config) -> returns dict
       - input_data is a file path string (single dataset)
    
    Args:
        input_data: Can be a directory path (str), a file path (str), or a DataFrame.
        output_file: Path to write results (only used if input is a directory).
        dataset_name: Name of the dataset (used if input is DataFrame or single file).
        config: Config object (optional).
    
    Returns:
        If input is a directory: True if successful, False otherwise.
        If input is a single dataset (DF or file): Dictionary of results.
    """
    if config is None:
        config = Config() # Fallback to default config if none provided

    # Determine input type
    if isinstance(input_data, pd.DataFrame):
        # Case 2: DataFrame provided
        if dataset_name is None:
            dataset_name = "unknown_dataset"
        logger.info(f"Running analysis on provided DataFrame: {dataset_name} with shape {input_data.shape}")
        result = analyze_dataset(input_data, dataset_name, config)
        if output_file:
            write_output(result, output_file)
        return result

    elif isinstance(input_data, str):
        # Check if it's a directory or a file
        if os.path.isdir(input_data):
            # Case 1: Directory provided (Batch processing)
            logger.info(f"Running baseline analysis on directory: {input_data}")
            if not output_file:
                logger.error("Output file path required when input is a directory.")
                return False
            
            datasets = load_datasets_from_raw(input_data)
            all_results = []
            success = True
            
            for name, df in datasets:
                try:
                    res = analyze_dataset(df, name, config)
                    all_results.append(res)
                except Exception as e:
                    logger.error(f"Error analyzing dataset {name}: {e}")
                    success = False
            
            output_data = {
                "status": "complete" if success else "partial",
                "timestamp": datetime.now().isoformat(),
                "datasets": all_results
            }
            write_output(output_data, output_file)
            return success
        
        elif os.path.isfile(input_data):
            # Case 3: Single file path provided
            if dataset_name is None:
                dataset_name = os.path.splitext(os.path.basename(input_data))[0]
            
            logger.info(f"Running analysis on single file: {input_data}")
            try:
                df = pd.read_csv(input_data)
                result = analyze_dataset(df, dataset_name, config)
                if output_file:
                    write_output(result, output_file)
                return result
            except Exception as e:
                logger.error(f"Failed to load or analyze file {input_data}: {e}")
                return {"error": str(e), "dataset_name": dataset_name}
        
        else:
            logger.error(f"Input string '{input_data}' is neither a file nor a directory.")
            return {"error": "Invalid input path"}
    
    else:
        logger.error(f"Unsupported input type: {type(input_data)}")
        return {"error": "Unsupported input type"}

def main():
    """CLI entry point for testing."""
    # Example usage for testing
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output = config.get("PROCESSED_DATA_PATH", "data/processed") + "/baseline_test.json"
    
    run_baseline_analysis(raw_dir, output, config=config)

if __name__ == "__main__":
    main()
