import os
import sys
import json
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from statsmodels.stats.outliers_influence import variance_inflation_factor
from config import get_random_state, get_project_root

def hyperbolic_function(d, k, A):
    """Hyperbolic discounting function."""
    return A / (1 + k * d)

def fit_hyperbolic_model(data: pd.DataFrame) -> pd.DataFrame:
    """Fits hyperbolic model to data."""
    # Re-implementation for modeling module context if needed
    # Or simply delegates if already done in ingestion
    return data

def load_and_prepare_data() -> pd.DataFrame:
    """Loads the harmonized dataset."""
    project_root = get_project_root()
    path = project_root / "data/processed/harmonized_dataset.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    df = pd.read_parquet(path)
    return df

def transform_and_center(df: pd.DataFrame) -> pd.DataFrame:
    """Transforms discount rate and centers predictors."""
    df = df.copy()
    # Log transform k
    df["log_k"] = np.log(df["discount_rate_k"] + 1e-6)
    
    # Center predictors
    for col in ["wm_accuracy", "wm_rt"]:
        if col in df.columns:
            df[f"{col}_centered"] = df[col] - df[col].mean()
    
    return df

def calculate_vif(df: pd.DataFrame, features: list) -> Dict[str, float]:
    """Calculates Variance Inflation Factor for features."""
    X = df[features].dropna()
    vif_data = {}
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
    return vif_data

def run_regression(df: pd.DataFrame) -> Dict:
    """Runs the OLS regression with interaction term."""
    import statsmodels.api as sm
    
    # Prepare data
    df_clean = df.dropna(subset=["log_k", "procrastination_score", "wm_accuracy"])
    
    # Create interaction
    df_clean["interaction"] = df_clean["log_k"] * df_clean["wm_accuracy"]
    
    # Read config
    project_root = get_project_root()
    config_path = project_root / "data/processed/model_config.json"
    config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
    
    # Select features
    features = ["log_k", "wm_accuracy_centered", "interaction"]
    if config.get("reduced_model"):
        # Exclude covariates if reduced model
        pass
    
    X = df_clean[features]
    X = sm.add_constant(X)
    y = df_clean["procrastination_score"]
    
    model = sm.OLS(y, X).fit()
    
    return {
        "summary": model.summary().tables[1].as_html(),
        "params": model.params.to_dict(),
        "pvalues": model.pvalues.to_dict(),
        "rsquared": model.rsquared
    }

def save_regression_results(results: Dict, output_path: Path):
    """Saves regression results to JSON."""
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

def run_full_analysis():
    """Runs the full analysis pipeline."""
    df = load_and_prepare_data()
    df = transform_and_center(df)
    results = run_regression(df)
    project_root = get_project_root()
    output_path = project_root / "data/processed/regression_results.json"
    save_regression_results(results, output_path)
    print("Regression analysis complete.")

if __name__ == "__main__":
    run_full_analysis()
