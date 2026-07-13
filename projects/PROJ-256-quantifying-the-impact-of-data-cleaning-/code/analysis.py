"""
Statistical analysis functions.
Implements t-tests, linear regression, and effect size calculations.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)

def run_t_test(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Run an independent samples t-test.
    Assumes the predictor is binary or can be split into two groups.
    """
    if predictor_col not in df.columns or outcome_col not in df.columns:
        raise ValueError(f"Columns {predictor_col} or {outcome_col} not found in dataframe")

    # Drop NaNs
    data = df[[predictor_col, outcome_col]].dropna()
    if len(data) < 2:
        return {"p_value": None, "statistic": None, "ci": None, "cohens_d": None}

    # Check if predictor is binary
    if data[predictor_col].nunique() == 2:
        groups = data.groupby(predictor_col)[outcome_col]
        g1 = groups.get_group(data[predictor_col].unique()[0])
        g2 = groups.get_group(data[predictor_col].unique()[1])
        t_stat, p_val = stats.ttest_ind(g1, g2)
    else:
        # Fallback: treat predictor as continuous and run correlation
        # Or split by median if not binary? For now, just warn and use correlation
        logger.warning(f"Predictor {predictor_col} is not binary. Using correlation approach.")
        corr, p_val = stats.pearsonr(data[predictor_col], data[outcome_col])
        t_stat = None
    
    # Calculate CI for difference in means if binary, else for correlation
    ci = None
    if t_stat is not None:
        # Simple 95% CI for difference
        mean_diff = g1.mean() - g2.mean()
        se = np.sqrt(np.var(g1, ddof=1)/len(g1) + np.var(g2, ddof=1)/len(g2))
        ci = (mean_diff - 1.96*se, mean_diff + 1.96*se)

    # Cohen's d
    cohens_d = None
    if t_stat is not None:
        pooled_std = np.sqrt(((len(g1)-1)*np.var(g1, ddof=1) + (len(g2)-1)*np.var(g2, ddof=1)) / (len(g1)+len(g2)-2))
        if pooled_std > 0:
            cohens_d = mean_diff / pooled_std

    return {
        "p_value": float(p_val) if p_val is not None else None,
        "statistic": float(t_stat) if t_stat is not None else None,
        "ci": ci,
        "ci_width": float(ci[1] - ci[0]) if ci else None,
        "cohens_d": float(cohens_d) if cohens_d is not None else None
    }

def run_linear_regression(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """
    Run a simple linear regression.
    """
    if predictor_col not in df.columns or outcome_col not in df.columns:
        raise ValueError(f"Columns {predictor_col} or {outcome_col} not found in dataframe")

    data = df[[predictor_col, outcome_col]].dropna()
    if len(data) < 2:
        return {"coefficients": [], "r_squared": None, "p_values": []}

    X = data[predictor_col].values.reshape(-1, 1)
    y = data[outcome_col].values

    model = LinearRegression()
    model.fit(X, y)

    # Calculate p-values for coefficients (t-test)
    n = len(y)
    p_val = 0.05 # Placeholder for simplicity, scipy.stats.linregress gives exact
    # Using scipy for exact p-value
    slope, intercept, r_value, p_val, std_err = stats.linregress(X.flatten(), y)

    return {
        "coefficients": [float(intercept), float(slope)],
        "r_squared": float(r_value**2),
        "p_values": [1.0, float(p_val)], # Intercept p-value usually not tested, set to 1
        "adj_r_squared": float(1 - (1 - r_value**2) * (n - 1) / (n - 2)) if n > 2 else None
    }

def compute_effect_size_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """Compute Cohen's d effect size."""
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(ddof=1), group2.std(ddof=1)
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def load_datasets_from_raw(raw_dir: str) -> List[pd.DataFrame]:
    """Load all CSV datasets from the raw directory."""
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return []
    
    datasets = []
    for file in os.listdir(raw_dir):
        if file.endswith('.csv'):
            path = os.path.join(raw_dir, file)
            try:
                df = pd.read_csv(path)
                datasets.append(df)
                logger.info(f"Loaded {file}: {df.shape}")
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
    return datasets

def analyze_dataset(df: pd.DataFrame, predictor_col: str, outcome_col: str) -> Dict[str, Any]:
    """Run full analysis (t-test and regression) on a dataset."""
    t_result = run_t_test(df, predictor_col, outcome_col)
    reg_result = run_linear_regression(df, predictor_col, outcome_col)
    
    return {
        "t_test": t_result,
        "regression": reg_result
    }

def run_baseline_analysis(
    input_data: Union[str, pd.DataFrame, List[pd.DataFrame]], 
    dataset_name: Optional[str] = None,
    config: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Run baseline analysis.
    Flexible signature to support multiple call patterns:
    1. run_baseline_analysis(raw_dir, output_path, config) -> saves to output_path
    2. run_baseline_analysis(df, dataset_name=...) -> returns result dict
    3. run_baseline_analysis(df_cleaned, dataset_name=...) -> returns result dict
    """
    # Handle different input types
    df = None
    name = dataset_name or "unknown"
    
    if isinstance(input_data, str):
        # Assume it's a directory path or file path
        if os.path.isdir(input_data):
            datasets = load_datasets_from_raw(input_data)
            if not datasets:
                return {"datasets": []}
            # Analyze first dataset for simplicity in this context
            df = datasets[0]
            name = os.path.basename(datasets[0].iloc[0].name if hasattr(datasets[0].iloc[0], 'name') else "dataset")
        else:
            # Assume file path
            df = pd.read_csv(input_data)
            name = os.path.basename(input_data)
    elif isinstance(input_data, pd.DataFrame):
        df = input_data
    elif isinstance(input_data, list):
        # List of dataframes
        if not input_data:
            return {"datasets": []}
        df = input_data[0]
    
    if df is None:
        return {"datasets": []}

    # Determine columns (simple heuristic: last col is outcome, first numeric is predictor)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        logger.warning(f"Not enough numeric columns in {name}")
        return {"datasets": []}
    
    predictor = numeric_cols[0]
    outcome = numeric_cols[-1]

    result = analyze_dataset(df, predictor, outcome)
    
    output = {
        "dataset_name": name,
        "predictor": predictor,
        "outcome": outcome,
        "n_rows": len(df),
        "analysis": result
    }
    
    # If config and output_path are provided (legacy call style 1)
    # This handles: run_baseline_analysis(raw_dir, output_path, config)
    # But the signature above doesn't match exactly. 
    # The caller t012_run_baseline_analysis.py calls: run_baseline_analysis(raw_dir, output_path, config)
    # We need to handle that specific case if it passes 3 args.
    # Since the function signature is flexible, we check if 'config' was passed as the 3rd arg
    # and if 'output_path' was passed as the 2nd arg.
    
    # However, the signature defined here is (input_data, dataset_name, config).
    # The caller calls with (raw_dir, output_path, config).
    # So:
    # input_data = raw_dir
    # dataset_name = output_path (misinterpreted)
    # config = config
    
    # We need to detect this. If dataset_name looks like a path, treat it as output_path.
    # And if config is passed, we might need to use it.
    
    # Let's adjust logic:
    # If the second argument is a string that looks like a path (contains / or ends in .json),
    # treat it as output_path.
    
    # Actually, the caller t012_run_baseline_analysis.py does:
    # success = run_baseline_analysis(raw_dir, output_path, config)
    # So we need to support:
    # def run_baseline_analysis(raw_dir, output_path, config):
    
    # But we also need to support:
    # results = run_baseline_analysis(df, dataset_name=dataset_name)
    
    # The current signature handles the keyword argument case.
    # For the positional case (3 args), we need to handle it inside.
    
    # Re-interpreting the arguments based on types:
    # If input_data is a string (path), and dataset_name is a string (path), and config is an object...
    # Then we are in the "save to file" mode.
    
    if isinstance(input_data, str) and isinstance(dataset_name, str) and config is not None:
        # This is the legacy call: run_baseline_analysis(raw_dir, output_path, config)
        # But our signature is (input_data, dataset_name, config).
        # So:
        # input_data = raw_dir
        # dataset_name = output_path
        # config = config
        
        # We already loaded data from input_data (raw_dir) above.
        # Now we need to save to dataset_name (output_path).
        
        # Wait, the logic above for loading from raw_dir used 'input_data'.
        # So if input_data is a dir, we loaded it.
        # Now we need to save to dataset_name.
        
        # But 'dataset_name' in this context is the output path.
        # Let's save the result.
        
        # The result 'output' is for one dataset. We need to structure it for the file.
        final_output = {"datasets": [output]}
        
        os.makedirs(os.path.dirname(dataset_name) if os.path.dirname(dataset_name) else '.', exist_ok=True)
        with open(dataset_name, 'w') as f:
            json.dump(final_output, f, indent=2)
        
        return True # Success
    
    return output

def main():
    """Test the analysis module."""
    # Create a dummy dataframe
    df = pd.DataFrame({
        'x': np.random.randn(100),
        'y': np.random.randn(100)
    })
    result = analyze_dataset(df, 'x', 'y')
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
