"""
Modeling Module.
Handles log-transformation, OLS regression, VIF calculation, and result saving.
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.formula.api import ols

try:
    from config import get_project_root, get_random_state
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_project_root, get_random_state

from pathlib import Path

PROJECT_ROOT = get_project_root()
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def hyperbolic_function(delay: float, k: float, A: float = 1.0) -> float:
    """
    Calculates the hyperbolic discounting value.
    """
    return A / (1 + k * delay)

def fit_hyperbolic_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fits a hyperbolic model to participant data to estimate k.
    Excludes participants where fitting fails.
    """
    # Placeholder for fitting logic if needed
    return df

def load_and_prepare_data() -> Tuple[pd.DataFrame, bool]:
    """
    Loads the harmonized dataset and prepares it for regression.
    Returns DataFrame and reduced_model flag.
    """
    parquet_path = DATA_PROCESSED_DIR / "harmonized_dataset.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(f"Harmonized dataset not found at {parquet_path}")
    
    df = pd.read_parquet(parquet_path)
    
    # Check for reduced model config
    config_path = DATA_PROCESSED_DIR / "model_config.json"
    reduced_model = False
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            reduced_model = config.get('reduced_model', False)
    
    return df, reduced_model

def transform_and_center(df: pd.DataFrame) -> pd.DataFrame:
    """
    Log-transforms discount rate and mean-centers predictors.
    """
    df = df.copy()
    
    # Log transform k
    df['log_k'] = np.log(df['discount_rate_k'] + 1e-6)
    
    # Mean center predictors
    predictors = ['procrastination_score', 'wm_accuracy', 'wm_rt', 'age']
    for col in predictors:
        if col in df.columns:
            df[col] = df[col] - df[col].mean()
    
    return df

def calculate_vif(df: pd.DataFrame, formula: str) -> List[Dict]:
    """
    Calculates Variance Inflation Factor for the model.
    """
    y, X = sm.dmatrices(formula, df, return_type='dataframe')
    X = sm.add_constant(X)
    
    vif_data = []
    for i, col in enumerate(X.columns):
        if col != 'const':
            vif = variance_inflation_factor(X.values, i)
            vif_data.append({'variable': col, 'vif': float(vif)})
    
    return vif_data

def run_regression(df: pd.DataFrame, reduced_model: bool = False) -> Tuple[sm.RegressionResultsWrapper, str]:
    """
    Runs the OLS regression with interaction term.
    """
    start_time = time.time()
    
    if reduced_model:
        formula = "log_k ~ procrastination_score * wm_accuracy"
    else:
        formula = "log_k ~ procrastination_score * wm_accuracy + wm_rt + age"
    
    required_cols = ['log_k', 'procrastination_score', 'wm_accuracy']
    if not all(c in df.columns for c in required_cols):
        raise ValueError(f"Missing columns for regression. Found: {df.columns.tolist()}")
    
    try:
        model = ols(formula, data=df).fit()
    except Exception as e:
        raise RuntimeError(f"Regression failed: {e}")
    
    elapsed = time.time() - start_time
    if elapsed > 21600 * 0.5:
        raise SystemExit("CRITICAL: Execution time exceeded 50% of limit.")
    
    return model, formula

def save_regression_results(results: sm.RegressionResultsWrapper, formula: str) -> Dict:
    """
    Saves regression results to JSON files.
    """
    summary = {
        'formula': formula,
        'rsquared': float(results.rsquared),
        'rsquared_adj': float(results.rsquared_adj),
        'aic': float(results.aic),
        'bic': float(results.bic),
        'coefficients': {},
        'pvalues': {},
        'conf_int': {}
    }
    
    for name, param in results.params.items():
        summary['coefficients'][name] = float(param)
        summary['pvalues'][name] = float(results.pvalues[name])
        conf_int = results.conf_int()
        summary['conf_int'][name] = [float(conf_int.loc[name, 0]), float(conf_int.loc[name, 1])]
    
    vif_data = calculate_vif(results.model.data.frame, formula)
    summary['vif'] = vif_data
    
    # Write VIF report
    vif_path = DATA_PROCESSED_DIR / "vif_report.json"
    with open(vif_path, 'w') as f:
        json.dump({'vif': vif_data}, f, indent=2)
    
    # Write interaction results
    interaction_results = {
        'interaction_coef': summary['coefficients'].get('procrastination_score:wm_accuracy'),
        'interaction_pval': summary['pvalues'].get('procrastination_score:wm_accuracy'),
        'interaction_ci': summary['conf_int'].get('procrastination_score:wm_accuracy')
    }
    int_path = DATA_PROCESSED_DIR / "interaction_results.json"
    with open(int_path, 'w') as f:
        json.dump(interaction_results, f, indent=2)
    
    # Write full regression results
    reg_path = DATA_PROCESSED_DIR / "regression_results.json"
    with open(reg_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

def run_full_analysis(seed: int = 42) -> None:
    """
    Runs the full modeling pipeline.
    """
    print("Loading data...")
    df, reduced_model = load_and_prepare_data()
    
    print("Transforming and centering...")
    df = transform_and_center(df)
    
    print("Running regression...")
    results, formula = run_regression(df, reduced_model)
    
    print("Saving results...")
    save_regression_results(results, formula)
    
    print("Modeling complete.")

if __name__ == "__main__":
    run_full_analysis()
