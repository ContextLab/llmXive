import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

logger = logging.getLogger(__name__)

def identify_numerical_columns(df: Union[pd.DataFrame, str]) -> List[str]:
    """
    Identify numerical columns in a DataFrame.
    
    Handles both DataFrame objects and file paths (strings).
    If a string is passed, it attempts to load the CSV first.
    """
    if isinstance(df, str):
        logger.info(f"Loading DataFrame from file path: {df}")
        try:
            df = pd.read_csv(df)
        except Exception as e:
            logger.error(f"Failed to load CSV from {df}: {e}")
            return []
    
    if not isinstance(df, pd.DataFrame):
        logger.error(f"Expected DataFrame or file path, got {type(df)}")
        return []
    
    return df.select_dtypes(include=[np.number]).columns.tolist()

def identify_categorical_columns(df: Union[pd.DataFrame, str]) -> List[str]:
    """
    Identify categorical columns in a DataFrame.
    
    Handles both DataFrame objects and file paths (strings).
    """
    if isinstance(df, str):
        logger.info(f"Loading DataFrame from file path: {df}")
        try:
            df = pd.read_csv(df)
        except Exception as e:
            logger.error(f"Failed to load CSV from {df}: {e}")
            return []
    
    if not isinstance(df, pd.DataFrame):
        logger.error(f"Expected DataFrame or file path, got {type(df)}")
        return []
    
    return df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

def run_t_test(df: pd.DataFrame, outcome_col: str, group_col: str) -> Optional[Dict[str, Any]]:
    """
    Run an independent samples t-test.
    
    Returns dict with p_value, t_statistic, ci_lower, ci_upper, significant.
    """
    try:
        # Group data
        groups = df.groupby(group_col)[outcome_col]
        
        if len(groups) < 2:
            logger.warning(f"Not enough groups for t-test in {group_col}")
            return None
        
        # Get group data
        group_data = [g.dropna().values for g in groups]
        
        if len(group_data) < 2:
            logger.warning("Less than 2 groups with data for t-test")
            return None
        
        # Run t-test (assuming equal variance for simplicity)
        t_stat, p_val = stats.ttest_ind(group_data[0], group_data[1], equal_var=True)
        
        # Calculate 95% CI for difference in means
        mean1, mean2 = np.mean(group_data[0]), np.mean(group_data[1])
        std1, std2 = np.std(group_data[0], ddof=1), np.std(group_data[1], ddof=1)
        n1, n2 = len(group_data[0]), len(group_data[1])
        
        se = np.sqrt((std1**2 / n1) + (std2**2 / n2))
        ci_margin = stats.t.ppf(0.975, min(n1, n2) - 1) * se
        
        ci_lower = (mean1 - mean2) - ci_margin
        ci_upper = (mean1 - mean2) + ci_margin
        
        return {
            "p_value": float(p_val),
            "t_statistic": float(t_stat),
            "ci_lower": float(ci_lower),
            "ci_upper": float(ci_upper),
            "significant": bool(p_val < 0.05),
            "method": "independent_t_test"
        }
    except Exception as e:
        logger.error(f"Error running t-test: {e}", exc_info=True)
        return None

def run_linear_regression(df: pd.DataFrame, outcome_col: str, group_col: str) -> Optional[Dict[str, Any]]:
    """
    Run a linear regression with group_col as predictor.
    
    Returns dict with r_squared, f_statistic, p_value, coefficients, significant.
    """
    try:
        # Encode categorical group_col if necessary
        if df[group_col].dtype == 'object' or df[group_col].dtype.name == 'category':
            # One-hot encode or label encode
            df_encoded = pd.get_dummies(df, columns=[group_col], drop_first=True)
            # Find the encoded columns
            encoded_cols = [col for col in df_encoded.columns if col.startswith(f"{group_col}_")]
            
            if not encoded_cols:
                logger.warning("Could not encode group column for regression")
                return None
            
            # Use first encoded column as predictor for simplicity
            predictor_col = encoded_cols[0]
            X = df_encoded[[predictor_col]]
            y = df_encoded[outcome_col]
            
            # Add constant
            X = sm.add_constant(X)
            
            # Fit model
            model = ols(f"{outcome_col} ~ {predictor_col}", data=df_encoded).fit()
            
            return {
                "r_squared": float(model.rsquared),
                "f_statistic": float(model.fvalue),
                "p_value": float(model.f_pvalue),
                "coefficients": [float(c) for c in model.params],
                "significant": bool(model.f_pvalue < 0.05)
            }
        else:
            # Numerical predictor
            X = df[[group_col]]
            y = df[outcome_col]
            
            # Add constant
            X = sm.add_constant(X)
            
            # Fit model
            model = sm.OLS(y, X).fit()
            
            return {
                "r_squared": float(model.rsquared),
                "f_statistic": float(model.fvalue),
                "p_value": float(model.f_pvalue),
                "coefficients": [float(c) for c in model.params],
                "significant": bool(model.f_pvalue < 0.05)
            }
    except Exception as e:
        logger.error(f"Error running linear regression: {e}", exc_info=True)
        return None

def compute_effect_size_cohen_d(df: pd.DataFrame, outcome_col: str, group_col: str) -> Optional[Dict[str, Any]]:
    """
    Compute Cohen's d effect size for the difference between groups.
    """
    try:
        groups = df.groupby(group_col)[outcome_col]
        
        if len(groups) < 2:
            return None
        
        group_data = [g.dropna().values for g in groups]
        
        if len(group_data) < 2:
            return None
        
        mean1, mean2 = np.mean(group_data[0]), np.mean(group_data[1])
        std1, std2 = np.std(group_data[0], ddof=1), np.std(group_data[1], ddof=1)
        n1, n2 = len(group_data[0]), len(group_data[1])
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return None
        
        cohen_d = (mean1 - mean2) / pooled_std
        
        return {
            "cohen_d": float(cohen_d)
        }
    except Exception as e:
        logger.error(f"Error computing Cohen's d: {e}", exc_info=True)
        return None

def load_datasets_from_raw(raw_dir: str) -> List[Dict[str, Any]]:
    """
    Load datasets from the raw data directory.
    Returns list of dicts with dataset info.
    """
    datasets = []
    
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return datasets
    
    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                datasets.append({
                    "filepath": filepath,
                    "filename": filename,
                    "dataset_name": filename.replace('.csv', ''),
                    "n_rows": len(df),
                    "n_columns": len(df.columns)
                })
            except Exception as e:
                logger.error(f"Failed to load {filepath}: {e}")
    
    return datasets

def analyze_dataset(
    df: Union[pd.DataFrame, str],
    dataset_name: str,
    outcome_col: str,
    group_col: str
) -> Optional[Dict[str, Any]]:
    """
    Run full analysis on a dataset: t-test, regression, effect size.
    
    Handles both DataFrame objects and file paths (strings).
    """
    logger.info(f"Analyzing dataset: {dataset_name}")
    
    # Load if string
    if isinstance(df, str):
        try:
            df = pd.read_csv(df)
        except Exception as e:
            logger.error(f"Failed to load dataset from {df}: {e}")
            return None
    
    if not isinstance(df, pd.DataFrame):
        logger.error(f"Expected DataFrame, got {type(df)}")
        return None
    
    # Validate columns exist
    if outcome_col not in df.columns:
        logger.error(f"Outcome column '{outcome_col}' not found in dataset")
        return None
    
    if group_col not in df.columns:
        logger.error(f"Group column '{group_col}' not found in dataset")
        return None
    
    # Run analyses
    t_test_result = run_t_test(df, outcome_col, group_col)
    regression_result = run_linear_regression(df, outcome_col, group_col)
    effect_size_result = compute_effect_size_cohen_d(df, outcome_col, group_col)
    
    if not t_test_result and not regression_result:
        logger.warning(f"No valid analysis results for {dataset_name}")
        return None
    
    return {
        "dataset_name": dataset_name,
        "t_test": t_test_result,
        "regression": regression_result,
        "effect_size": effect_size_result
    }

def save_json_file(filepath: str, data: Dict[str, Any]) -> bool:
    """
    Save data to a JSON file.
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved JSON to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON to {filepath}: {e}")
        return False

def run_baseline_analysis(
    raw_dir_or_df: Union[str, pd.DataFrame],
    output_file_or_name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Union[bool, Dict[str, Any]]:
    """
    Run baseline analysis on datasets.
    
    Flexible signature to handle multiple call patterns:
    1. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
    2. run_baseline_analysis(df, dataset_name=..., config=config) -> returns dict
    3. run_baseline_analysis(dataset_path, temp_output, config={}) -> writes file, returns bool
    4. run_baseline_analysis(df, dataset_name=...) -> returns dict
    
    Args:
        raw_dir_or_df: Either a directory path (str), a single file path (str), or a DataFrame
        output_file_or_name: Either an output file path (str), a dataset name (str), or None
        config: Configuration dict with outcome_col, group_col, etc.
    
    Returns:
        bool if writing to file, dict if returning results
    """
    logger = logging.getLogger(__name__)
    logger.info("Running baseline analysis with flexible signature")
    
    # Determine what was passed
    if isinstance(raw_dir_or_df, pd.DataFrame):
        # Case 2 or 4: DataFrame passed
        df = raw_dir_or_df
        dataset_name = output_file_or_name if isinstance(output_file_or_name, str) else "unknown"
        
        # Get columns from config or defaults
        outcome_col = config.get("outcome_col") if config else None
        group_col = config.get("group_col") if config else None
        
        # Infer if not provided
        if not outcome_col:
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            outcome_col = categorical_cols[0] if categorical_cols else df.columns[0]
        
        if not group_col:
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            if len(categorical_cols) > 1:
                group_col = categorical_cols[1]
            else:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                group_col = numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        result = analyze_dataset(df, dataset_name, outcome_col, group_col)
        return result if result else {"status": "error", "message": "Analysis failed"}
    
    elif isinstance(raw_dir_or_df, str):
        # Case 1 or 3: String passed (could be dir or file)
        if os.path.isdir(raw_dir_or_df):
            # Case 1: Directory
            datasets = load_datasets_from_raw(raw_dir_or_df)
            all_results = []
            
            for ds in datasets:
                df = pd.read_csv(ds["filepath"])
                outcome_col = config.get("outcome_col") if config else None
                group_col = config.get("group_col") if config else None
                
                if not outcome_col:
                    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    outcome_col = categorical_cols[0] if categorical_cols else df.columns[0]
                
                if not group_col:
                    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    if len(categorical_cols) > 1:
                        group_col = categorical_cols[1]
                    else:
                        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                        group_col = numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]
                
                result = analyze_dataset(df, ds["dataset_name"], outcome_col, group_col)
                if result:
                    all_results.append(result)
            
            if output_file_or_name:
                output_data = {
                    "status": "success",
                    "total_datasets_analyzed": len(all_results),
                    "datasets": all_results,
                    "generated_at": datetime.now().isoformat()
                }
                success = save_json_file(output_file_or_name, output_data)
                return success
            else:
                return {"status": "success", "datasets": all_results}
        
        else:
            # Case 3: Single file
            try:
                df = pd.read_csv(raw_dir_or_df)
                dataset_name = os.path.basename(raw_dir_or_df).replace('.csv', '')
                
                outcome_col = config.get("outcome_col") if config else None
                group_col = config.get("group_col") if config else None
                
                if not outcome_col:
                    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    outcome_col = categorical_cols[0] if categorical_cols else df.columns[0]
                
                if not group_col:
                    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    if len(categorical_cols) > 1:
                        group_col = categorical_cols[1]
                    else:
                        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                        group_col = numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]
                
                result = analyze_dataset(df, dataset_name, outcome_col, group_col)
                
                if output_file_or_name and result:
                    output_data = {
                        "status": "success",
                        "datasets": [result],
                        "generated_at": datetime.now().isoformat()
                    }
                    success = save_json_file(output_file_or_name, output_data)
                    return success
                
                return result if result else {"status": "error"}
            except Exception as e:
                logger.error(f"Failed to process file {raw_dir_or_df}: {e}")
                return False
    else:
        logger.error(f"Unsupported input type: {type(raw_dir_or_df)}")
        return False

def main():
    """
    Main entry point for analysis module.
    """
    logger.info("Analysis module loaded")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
