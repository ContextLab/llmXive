"""
Analysis module for statistical testing and baseline analysis.
Implements t-tests, linear regressions, and effect size calculations.
"""
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

logger = logging.getLogger(__name__)

def identify_numerical_columns(df: pd.DataFrame) -> List[str]:
    """Identify numerical columns in a dataframe."""
    return df.select_dtypes(include=[np.number]).columns.tolist()

def identify_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Identify categorical columns in a dataframe."""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()

def run_t_test(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Perform an independent t-test between two groups defined by a binary categorical predictor.
    If predictor is numerical, it will be binned or we might need to adjust.
    For this task, we assume we are testing numerical predictors against a numerical outcome?
    No, t-test usually compares groups.
    Let's implement: if predictor is categorical (binary), do t-test on outcome between groups.
    If predictor is numerical, we might do correlation or regression.
    The task asks for t-tests and linear regressions.
    Let's assume:
    - For categorical predictors (binary): t-test on outcome.
    - For numerical predictors: correlation/regression.
    
    To make this robust for the pipeline:
    We will check the type of predictor_col.
    """
    if predictor_col not in df.columns or outcome_col not in df.columns:
        return {"error": "Columns not found"}
    
    # Check if predictor is binary categorical
    pred_vals = df[predictor_col].dropna()
    if pred_vals.dtype == 'object' or str(pred_vals.dtype).startswith('category'):
        unique_vals = pred_vals.unique()
        if len(unique_vals) == 2:
            group1 = df[df[predictor_col] == unique_vals[0]][outcome_col]
            group2 = df[df[predictor_col] == unique_vals[1]][outcome_col]
            
            if len(group1) < 2 or len(group2) < 2:
                return {"error": "Insufficient data for t-test"}
            
            t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False) # Welch's t-test
            return {
                "test": "t-test",
                "predictor": predictor_col,
                "outcome": outcome_col,
                "p_value": float(p_val),
                "t_statistic": float(t_stat),
                "method": "Welch's t-test"
            }
        else:
            # ANOVA or Kruskal-Wallis for >2 groups? For now, return info
            return {"info": "Predictor has >2 categories, skipping t-test (use ANOVA if needed)"}
    else:
        # Numerical predictor: we can do a correlation test (which is related to t-test)
        # Or we can bin it? The task says "t-tests".
        # Let's do a correlation test (Pearson) which returns a t-statistic and p-value.
        # Or we can treat it as a regression.
        # Let's stick to the requirement: "t-tests".
        # If predictor is numerical, maybe we bin it into high/low?
        # To be safe, let's do a correlation test and report it as a t-test equivalent.
        # Actually, Pearson correlation test is a t-test.
        if len(df[predictor_col].dropna()) < 3:
            return {"error": "Insufficient data"}
        corr, p_val = stats.pearsonr(df[predictor_col].dropna(), df[outcome_col].dropna())
        return {
            "test": "correlation (t-test equivalent)",
            "predictor": predictor_col,
            "outcome": outcome_col,
            "p_value": float(p_val),
            "correlation": float(corr),
            "method": "Pearson correlation"
        }

def run_linear_regression(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """Perform a simple linear regression."""
    if predictor_col not in df.columns or outcome_col not in df.columns:
        return {"error": "Columns not found"}
    
    # Drop rows with missing values in these columns
    subset = df[[predictor_col, outcome_col]].dropna()
    if len(subset) < 3:
        return {"error": "Insufficient data for regression"}
    
    X = subset[[predictor_col]]
    y = subset[outcome_col]
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate R-squared
    r2 = model.score(X, y)
    
    # Calculate p-value for the coefficient (t-test on slope)
    # We can use statsmodels for a full summary, but let's approximate with scipy
    # Or use the formula for t-statistic of the slope
    n = len(subset)
    p_val = 0.0
    t_stat = 0.0
    
    if n > 2:
        # Calculate standard error of the slope
        y_pred = model.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        
        if ss_tot == 0:
            return {"error": "Zero variance in outcome"}
        
        r_squared = 1 - (ss_res / ss_tot)
        se_slope = np.sqrt((ss_res / (n - 2)) / np.sum((X - X.mean()) ** 2))
        t_stat = model.coef_[0] / se_slope
        p_val = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - 2))
    
    return {
        "test": "linear_regression",
        "predictor": predictor_col,
        "outcome": outcome_col,
        "coefficient": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "r_squared": float(r2),
        "p_value": float(p_val),
        "t_statistic": float(t_stat),
        "n_samples": int(n)
    }

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """Compute Cohen's d effect size."""
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(), group2.std()
    n1, n2 = len(group1), len(group2)
    
    if std1 == 0 and std2 == 0:
        return 0.0
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def analyze_dataset(df: pd.DataFrame, dataset_name: str, outcome_col: str) -> Dict[str, Any]:
    """
    Run a suite of statistical tests on a dataset.
    Tests: t-tests (for binary categorical predictors) and linear regressions (for numerical).
    """
    logger.info(f"Analyzing dataset: {dataset_name}")
    
    numerical_cols = identify_numerical_columns(df)
    categorical_cols = identify_categorical_columns(df)
    
    # We need to decide which columns to test.
    # Usually, we test all predictors against the outcome.
    predictors = [c for c in numerical_cols + categorical_cols if c != outcome_col]
    
    if not predictors:
        logger.warning(f"No predictors found in {dataset_name}")
        return {"dataset": dataset_name, "tests": []}
    
    results = []
    
    # For numerical predictors, we can do regression or correlation
    for col in numerical_cols:
        if col == outcome_col:
            continue
        # Regression
        res = run_linear_regression(df, col, outcome_col)
        if "error" not in res:
            results.append(res)
        else:
            logger.debug(f"Regression failed for {col}: {res['error']}")
        
        # Also do correlation if it's numerical
        # (Already covered by regression mostly, but t-test equivalent is there)
    
    # For categorical predictors
    for col in categorical_cols:
        if col == outcome_col:
            continue
        res = run_t_test(df, col, outcome_col)
        if "error" not in res and "info" not in res:
            results.append(res)
        elif "info" in res:
            logger.debug(f"Skipping t-test for {col}: {res['info']}")
    
    return {
        "dataset_name": dataset_name,
        "outcome_column": outcome_col,
        "n_samples": len(df),
        "n_predictors": len(predictors),
        "tests": results
    }

def load_datasets_from_raw(raw_dir: str) -> List[Tuple[str, pd.DataFrame]]:
    """
    Load datasets from a raw directory.
    Handles both CSV files and directories (like UCI HAR).
    """
    datasets = []
    
    if not os.path.exists(raw_dir):
        logger.error(f"Raw directory not found: {raw_dir}")
        return datasets
    
    for item in os.listdir(raw_dir):
        item_path = os.path.join(raw_dir, item)
        
        if item.endswith('.csv'):
            try:
                df = pd.read_csv(item_path)
                datasets.append((item.replace('.csv', ''), df))
            except Exception as e:
                logger.error(f"Error loading {item}: {e}")
        
        elif os.path.isdir(item_path):
            # Handle directory-based datasets (e.g., UCI HAR)
            # Look for a common file pattern, e.g., *.csv inside
            csv_files = [f for f in os.listdir(item_path) if f.endswith('.csv')]
            if csv_files:
                # Try to load the first one or merge?
                # For simplicity, let's assume there's a 'features.csv' or similar, or we merge all
                # But UCI HAR has multiple files.
                # Let's try to load 'X_train.csv' and 'y_train.csv' if they exist
                x_file = os.path.join(item_path, 'X_train.csv')
                y_file = os.path.join(item_path, 'y_train.csv')
                
                if os.path.exists(x_file) and os.path.exists(y_file):
                    try:
                        X = pd.read_csv(x_file)
                        y = pd.read_csv(y_file)
                        # Merge them
                        # y might have a headerless column, rename it to 'activity'
                        if y.shape[1] == 1:
                            y.columns = ['activity']
                        df = pd.concat([X, y], axis=1)
                        datasets.append((item, df))
                    except Exception as e:
                        logger.error(f"Error loading {item} (directory): {e}")
                else:
                    # Fallback: try to load all CSVs and concatenate?
                    # Too complex for now. Log and skip.
                    logger.warning(f"Directory {item} does not contain expected UCI HAR files. Skipping.")
    
    return datasets

def run_baseline_analysis(
    input_data: Union[str, pd.DataFrame, List[Tuple[str, pd.DataFrame]]],
    output_file: Optional[str] = None,
    dataset_name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Union[bool, Dict[str, Any]]:
    """
    Run baseline analysis on raw data.
    
    Supports multiple call signatures:
    1. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
    2. run_baseline_analysis(df, dataset_name=..., config=config) -> returns dict
    3. run_baseline_analysis(df_cleaned, dataset_name=..., config=config) -> returns dict
    
    Args:
        input_data: Can be a path (str), a DataFrame, or a list of (name, df) tuples.
        output_file: Path to write JSON results (optional).
        dataset_name: Name of the dataset (required if input is DataFrame).
        config: Configuration dictionary.
    
    Returns:
        If output_file is provided: bool (success).
        Else: Dict with analysis results.
    """
    if config is None:
        config = {}
    
    logger.info(f"Running baseline analysis. Input type: {type(input_data)}")
    
    results = []
    datasets_analyzed = []
    
    # Handle input data
    if isinstance(input_data, str):
        # Case 1: Input is a path (raw directory)
        if output_file is None:
            raise ValueError("output_file must be provided when input is a path.")
        
        datasets = load_datasets_from_raw(input_data)
        if not datasets:
            logger.error("No datasets found in the specified path.")
            return False
        
        for name, df in datasets:
            # Infer outcome column
            outcome_col = _infer_outcome_column(df)
            if not outcome_col:
                logger.warning(f"Could not infer outcome for {name}. Skipping.")
                continue
            
            analysis = analyze_dataset(df, name, outcome_col)
            analysis['dataset_name'] = name
            analysis['outcome_column'] = outcome_col
            results.append(analysis)
            datasets_analyzed.append(name)
        
        # Write to file
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "source_path": input_data,
            "datasets": results
        }
        
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Baseline analysis results written to {output_file}")
        return True
    
    elif isinstance(input_data, pd.DataFrame):
        # Case 2 & 3: Input is a DataFrame
        if dataset_name is None:
            raise ValueError("dataset_name must be provided when input is a DataFrame.")
        
        outcome_col = _infer_outcome_column(input_data)
        if not outcome_col:
            logger.error(f"Could not infer outcome column for {dataset_name}.")
            return {"success": False, "error": "No outcome column found"}
        
        analysis = analyze_dataset(input_data, dataset_name, outcome_col)
        analysis['dataset_name'] = dataset_name
        analysis['outcome_column'] = outcome_col
        
        if output_file:
            # Write single result to file
            output_data = {
                "generated_at": datetime.now().isoformat(),
                "datasets": [analysis]
            }
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Analysis for {dataset_name} written to {output_file}")
        
        return {"success": True, "results": {dataset_name: analysis}}
    
    elif isinstance(input_data, list):
        # List of (name, df) tuples
        if output_file is None:
            raise ValueError("output_file must be provided for list input.")
        
        for name, df in input_data:
            outcome_col = _infer_outcome_column(df)
            if not outcome_col:
                logger.warning(f"Skipping {name}: no outcome column.")
                continue
            analysis = analyze_dataset(df, name, outcome_col)
            analysis['dataset_name'] = name
            analysis['outcome_column'] = outcome_col
            results.append(analysis)
        
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "datasets": results
        }
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Batch analysis written to {output_file}")
        return True
    
    else:
        raise ValueError(f"Unsupported input type: {type(input_data)}")

def _infer_outcome_column(df: pd.DataFrame) -> Optional[str]:
    """Infer the outcome column from a dataframe."""
    possible_names = ['outcome', 'target', 'label', 'class', 'activity', 'purchased', 'y', 'dependent']
    for name in possible_names:
        if name in df.columns:
            return name
    
    # Fallback: last numerical column
    numericals = identify_numerical_columns(df)
    if len(numericals) > 1:
        return numericals[-1]
    
    return None

def main():
    """Main entry point for testing."""
    setup_logging("INFO")
    logger.info("Analysis module loaded.")

if __name__ == "__main__":
    main()
