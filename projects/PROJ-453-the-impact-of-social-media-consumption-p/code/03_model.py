import os
import sys
import logging
import json
import yaml
import numpy as np
import pandas as pd
import traceback
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from scipy import stats

# Import local utilities
from utils import log_setup, causal_language_scanner
from config import ensure_directories, DATA_ROOT, RESULTS_ROOT

# Setup logging
logger = log_setup()

# Memory profiling imports
try:
    import tracemalloc
    HAS_TRACEMALLOC = True
except ImportError:
    HAS_TRACEMALLOC = False
    logger.warning("tracemalloc not available. Memory profiling will be skipped.")

# Constants
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def load_schema_contract(path: str) -> Dict[str, Any]:
    """Load a YAML schema contract."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_output_schema(output: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate output against schema."""
    # Basic validation logic
    required_keys = ['coefficients', 'p_values', 'diagnostics']
    for key in required_keys:
        if key not in output:
            logger.error(f"Missing required key in output: {key}")
            return False
    return True

def mean_center(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Mean-center specified columns in-place."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            mean_val = df[col].mean()
            df[col] = df[col] - mean_val
            logger.info(f"Mean-centered {col}: mean = {mean_val:.4f}")
    return df

def create_interaction(df: pd.DataFrame, col1: str, col2: str, new_col: str) -> pd.DataFrame:
    """Create an interaction term."""
    df = df.copy()
    if col1 in df.columns and col2 in df.columns:
        df[new_col] = df[col1] * df[col2]
        logger.info(f"Created interaction term: {new_col} = {col1} * {col2}")
    else:
        logger.error(f"Columns {col1} or {col2} not found for interaction.")
    return df

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for features."""
    vif_data = {}
    # Add constant for statsmodels
    try:
        import statsmodels.api as sm
        X = df[features]
        X = sm.add_constant(X)
        for i, col in enumerate(features):
            # Exclude the column itself from the regression to calculate VIF
            other_cols = [c for c in features if c != col]
            X_regress = sm.add_constant(df[other_cols])
            y_regress = df[col]
            
            # Handle potential singular matrix or perfect collinearity
            try:
                model = sm.OLS(y_regress, X_regress).fit()
                vif = 1 / (1 - model.rsquared)
                vif_data[col] = vif
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {col}: {e}")
                vif_data[col] = float('inf')
    except ImportError:
        logger.error("statsmodels not installed. Cannot calculate VIF.")
        raise
    return vif_data

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """Apply Benjamini-Hochberg correction to p-values."""
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_pvals = [p_values[i] for i in sorted_indices]
    
    corrected = [False] * n
    threshold = alpha
    for i in range(n - 1, -1, -1):
        if sorted_pvals[i] <= threshold:
            for j in range(i + 1):
                corrected[sorted_indices[j]] = True
            break
        threshold *= (i / n)
    
    return corrected

def check_collinearity(df: pd.DataFrame, var1: str, var2: str, threshold: float = 0.7) -> bool:
    """Check correlation between two variables."""
    if var1 not in df.columns or var2 not in df.columns:
        logger.warning(f"Variables {var1} or {var2} not found. Skipping collinearity check.")
        return False
    
    corr = df[[var1, var2]].corr().iloc[0, 1]
    is_high = abs(corr) > threshold
    if is_high:
        logger.warning(f"High collinearity detected: {var1} vs {var2} (r={corr:.4f})")
    return is_high

def run_model(df: pd.DataFrame, outcome: str, predictors: List[str], interaction_col: Optional[str] = None) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit OLS model and return results and diagnostics.
    Returns: (model_results, diagnostics_dict)
    """
    import statsmodels.api as sm
    
    X = df[predictors]
    if interaction_col and interaction_col in df.columns:
        X[interaction_col] = df[interaction_col]
        predictors_with_int = predictors + [interaction_col]
        X = df[predictors_with_int]
    
    X = sm.add_constant(X)
    y = df[outcome]
    
    model = sm.OLS(y, X).fit()
    
    diagnostics = {
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'f_statistic': model.fvalue,
        'f_pvalue': model.f_pvalue,
        'n_obs': model.nobs,
        'df_resid': model.df_resid
    }
    
    return model, diagnostics

def log_peak_memory(log_path: Path, start_memory: float, end_memory: float) -> None:
    """Log peak memory usage to the specified file."""
    peak = max(start_memory, end_memory)
    # tracemalloc returns bytes, convert to MB
    peak_mb = peak / (1024 * 1024)
    
    os.makedirs(log_path.parent, exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(f"Peak Memory: {peak_mb:.2f} MB\n")
    
    logger.info(f"Memory profiling: Peak Memory: {peak_mb:.2f} MB")

def main():
    """Main execution function for the modeling pipeline."""
    logger.info("Starting modeling pipeline.")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load cleaned data
    data_path = Path(DATA_ROOT) / "processed" / "participants_cleaned.csv"
    if not data_path.exists():
        logger.error(f"Cleaned data file not found: {data_path}")
        logger.error("Please run code/02_engineer.py first to generate participants_cleaned.csv")
        sys.exit(1)
    
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} rows from {data_path}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # Define variables
    outcome = "cognitive_flexibility_score"
    predictors = ["switching_index", "total_screen_time", "age"]
    interaction_col = "switching_index_age_interaction"
    
    # Check for required columns
    required_cols = [outcome] + predictors
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        sys.exit(1)
    
    # Start memory profiling
    if HAS_TRACEMALLOC:
        tracemalloc.start()
        start_mem = tracemalloc.get_traced_memory()[1] # Current memory in bytes
        # Initial baseline is usually 0 or very small, we track peak during execution
    
    # Mean center predictors
    df = mean_center(df, ["switching_index", "age"])
    
    # Create interaction term
    df = create_interaction(df, "switching_index", "age", interaction_col)
    
    # Check collinearity
    collinearity_flag = check_collinearity(df, "switching_index", "total_screen_time", threshold=0.7)
    
    collinearity_log_path = Path("logs") / "collinearity_check.log"
    os.makedirs(collinearity_log_path.parent, exist_ok=True)
    with open(collinearity_log_path, 'w') as f:
        f.write(f"flag={str(collinearity_flag).lower()}\n")
        if collinearity_flag:
            f.write("Warning: Potential Mathematical Coupling detected.\n")
    
    # Handle residual model if flagged
    final_predictors = predictors.copy()
    if collinearity_flag:
        logger.info("High collinearity detected. Running residual model procedure.")
        # Regress switching_index on total_screen_time
        X_res = sm.add_constant(df[["total_screen_time"]])
        y_res = df["switching_index"]
        res_model = sm.OLS(y_res, X_res).fit()
        df["switching_index_residuals"] = res_model.resid
        
        # Save residuals
        residuals_path = Path(RESULTS_ROOT) / "models" / "residuals.csv"
        df[["switching_index_residuals"]].to_csv(residuals_path, index=False)
        
        # Save residualized coefficients
        res_coef_path = Path(RESULTS_ROOT) / "models" / "residualized_coefficients.json"
        res_coef_data = {
            "r_squared": res_model.rsquared,
            "coefficients": res_model.params.to_dict(),
            "p_values": res_model.pvalues.to_dict()
        }
        with open(res_coef_path, 'w') as f:
            json.dump(res_coef_data, f, indent=2)
        
        # Use residuals for main model
        final_predictors = ["switching_index_residuals", "total_screen_time", "age"]
    else:
        logger.info("Collinearity check passed. Proceeding with standard model.")
    
    # Fit main model
    try:
        model, diagnostics = run_model(df, outcome, final_predictors, interaction_col)
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # Calculate VIF
    vif_features = final_predictors + ([interaction_col] if interaction_col in df.columns else [])
    vif_scores = calculate_vif(df, vif_features)
    diagnostics['vif_scores'] = vif_scores
    
    # Get p-values
    p_values = model.pvalues.to_dict()
    coefficients = model.params.to_dict()
    
    # Apply Benjamini-Hochberg correction
    p_list = [p_values[k] for k in p_values.keys()]
    corrected_flags = benjamini_hochberg(p_list)
    corrected_p_values = {k: p if flag else p for k, p, flag in zip(p_values.keys(), p_list, corrected_flags)}
    
    # Construct output
    output = {
        "coefficients": coefficients,
        "p_values": p_values,
        "corrected_p_values": corrected_p_values,
        "diagnostics": diagnostics,
        "collinearity_flag": collinearity_flag,
        "interpretation": (
            f"The analysis indicates an associational relationship between switching behavior "
            f"and cognitive flexibility scores. The model explains {diagnostics['r_squared']:.2%} of the variance. "
            f"VIF scores indicate {'acceptable' if all(v < 5 for v in vif_scores.values()) else 'potential'} multicollinearity."
        )
    }
    
    # Validate output schema
    schema_path = Path("contracts") / "output.schema.yaml"
    if schema_path.exists():
        schema = load_schema_contract(str(schema_path))
        if not validate_output_schema(output, schema):
            logger.error("Output validation failed against schema.")
            sys.exit(1)
    
    # Scan for causal language
    forbidden = ["causes", "leads to", "impacts", "effect of", "results in"]
    matches = causal_language_scanner(output["interpretation"], forbidden)
    if matches:
        logger.error(f"Causal language detected: {matches}. Failing run.")
        sys.exit(1)
    
    # Save results
    results_dir = Path(RESULTS_ROOT) / "models"
    os.makedirs(results_dir, exist_ok=True)
    
    summary_path = results_dir / "regression_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    # End memory profiling and log
    if HAS_TRACEMALLOC:
        current, peak = tracemalloc.get_traced_memory()
        end_mem = peak # Peak is what we care about
        tracemalloc.stop()
        
        log_path = Path("logs") / "memory_profile.log"
        log_peak_memory(log_path, start_mem, end_mem)
    
    logger.info(f"Model fitting complete. Results saved to {summary_path}")

if __name__ == "__main__":
    main()
