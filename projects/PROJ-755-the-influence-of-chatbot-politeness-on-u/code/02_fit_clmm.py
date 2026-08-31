"""
Code module for fitting Cumulative Link Mixed-Effects Models (CLMM).

This script loads the scored dialogues dataset, checks for collinearity,
and fits the primary CLMM using rpy2 to interface with R's lme4 package.
It extracts convergence status and saves results to CSV and JSON artifacts.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# R integration
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.packages import importr
from rpy2.rinterface_lib.callbacks import logger as rpy2_logger
import warnings

# Suppress rpy2 conversion warnings for cleaner logs
warnings.filterwarnings("ignore", category=RuntimeWarning)
rpy2_logger.setLevel(logging.ERROR)

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CODE_DIR = PROJECT_ROOT / "code"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required output directories exist."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory: {DATA_PROCESSED_DIR}")

def load_scored_dialogues() -> pd.DataFrame:
    """
    Load the scored dialogues dataset.
    
    Returns:
        pd.DataFrame: The loaded dataset.
    """
    input_path = DATA_PROCESSED_DIR / "scored_dialogues.parquet"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure T018 and T020 have completed successfully."
        )
    
    logger.info(f"Loading scored dialogues from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def calculate_vif(df: pd.DataFrame, predictor_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for predictor variables.
    
    Args:
        df: DataFrame containing the variables.
        predictor_cols: List of column names to check.
        
    Returns:
        Dictionary mapping column names to their VIF values.
    """
    if len(predictor_cols) < 2:
        logger.warning("Not enough predictors to calculate VIF.")
        return {col: 0.0 for col in predictor_cols}

    # Prepare data for VIF calculation
    # We need to handle categorical variables if present, but for VIF
    # we typically look at continuous predictors or dummy variables.
    # Here we assume 'politeness' and 'conversation_length' are numeric.
    
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    vif_data = {}
    X = df[predictor_cols].copy()
    
    # Drop rows with NaN in predictors for VIF calculation
    X = X.dropna()
    
    if X.empty:
        logger.warning("No valid data for VIF calculation after dropping NaNs.")
        return {col: np.nan for col in predictor_cols}

    for i, col in enumerate(predictor_cols):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
        logger.info(f"VIF for {col}: {vif:.4f}")
    
    return vif_data

def check_collinearity(df: pd.DataFrame) -> Tuple[List[str], Dict[str, float]]:
    """
    Check for collinearity and return columns to drop.
    
    Args:
        df: The dataset.
        
    Returns:
        Tuple of (columns_to_drop, vif_scores).
    """
    predictors = ["politeness", "conversation_length"]
    # Filter to only existing columns
    available_predictors = [p for p in predictors if p in df.columns]
    
    if len(available_predictors) < 2:
        logger.warning(f"Insufficient predictors ({available_predictors}) for collinearity check.")
        return [], {}

    vif_scores = calculate_vif(df, available_predictors)
    columns_to_drop = []
    
    for col, vif in vif_scores.items():
        if vif >= 5.0:
            logger.warning(f"High collinearity detected for '{col}' (VIF={vif:.2f}). Dropping variable.")
            columns_to_drop.append(col)
        else:
            logger.info(f"Collinearity acceptable for '{col}' (VIF={vif:.2f}).")
    
    return columns_to_drop, vif_scores

def fit_clmm(df: pd.DataFrame, drop_cols: List[str]) -> Tuple[Optional[Any], str, Dict[str, Any]]:
    """
    Fit the primary CLMM using rpy2 and R's lme4 package.
    
    Args:
        df: Preprocessed DataFrame.
        drop_cols: List of columns to drop due to collinearity.
        
    Returns:
        Tuple of (model_object, convergence_status, metrics_dict).
    """
    # Prepare predictors
    predictors = ["politeness", "conversation_length"]
    active_predictors = [p for p in predictors if p not in drop_cols and p in df.columns]
    
    if not active_predictors:
        raise ValueError("No predictors left after collinearity check. Cannot fit model.")

    # Prepare formula
    # Formula: quality_rating ~ politeness + conversation_length + (1|user_id)
    # We need to ensure quality_rating is a factor (ordered)
    df_fit = df.copy()
    
    # Convert target to ordered factor
    if "quality_rating" not in df_fit.columns:
        raise ValueError("Column 'quality_rating' missing in dataset.")
    
    # Ensure quality_rating is treated as a factor
    df_fit["quality_rating"] = pd.Categorical(
        df_fit["quality_rating"], 
        ordered=True
    )
    
    # Drop rows with missing values in required columns
    required_cols = ["quality_rating", "user_id"] + active_predictors
    df_fit = df_fit.dropna(subset=required_cols)
    
    if df_fit.empty:
        raise ValueError("No valid data remaining after dropping NaNs.")

    logger.info(f"Fitting CLMM with formula: quality_rating ~ {' + '.join(active_predictors)} + (1|user_id)")
    logger.info(f"Data size: {len(df_fit)} rows")

    # Initialize R packages
    try:
        base = importr('base')
        stats = importr('stats')
        lme4 = importr('lme4')
        ordinal = importr('ordinal') # clmm is in ordinal package
    except Exception as e:
        logger.error(f"Failed to import R packages: {e}")
        raise

    # Convert pandas DataFrame to R DataFrame
    with localconverter(ro.default_converter + pandas2ri.converter):
        r_df = ro.conversion.py2rpy(df_fit)

    # Construct formula string
    fixed_part = " + ".join(active_predictors)
    formula_str = f"quality_rating ~ {fixed_part} + (1|user_id)"
    logger.info(f"R Formula: {formula_str}")
    
    # Create R formula object
    r_formula = ro.Formula(formula_str)

    # Fit the model using clmm from ordinal package
    # clmm(response ~ fixed_effects + (random_effects), data = data)
    try:
        # Using clmm from ordinal package which is more robust for CLMM
        model = ordinal.clmm(
            r_formula, 
            data=r_df, 
            link="logit",
            nAGQ=0 # Faster, approximate integration
        )
    except Exception as e:
        logger.error(f"CLMM fitting failed: {e}")
        # Fallback to basic lme4 if ordinal fails (though ordinal is preferred)
        try:
            logger.info("Attempting fallback to lme4::clmm...")
            model = lme4.clmm(r_formula, data=r_df)
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}")
            return None, "failed", {}

    # Extract convergence status
    # clmm objects have a 'convergence' attribute (0 = success)
    conv_status = None
    try:
        # Check the convergence attribute
        conv_val = model.rx2("convergence")[0]
        if conv_val == 0:
            conv_status = "success"
        else:
            conv_status = "failed"
            logger.warning(f"Model did not converge. Code: {conv_val}")
    except Exception as e:
        logger.warning(f"Could not extract convergence status: {e}")
        conv_status = "unknown"

    # Extract coefficients and p-values
    # summary(model) gives us the fixed effects
    try:
        summ = ordinal.summary(model)
        # The fixed effects table is usually in summ.rx2('coefficients')
        # We need to extract coefficients, SEs, z-values, p-values
        fixed_eff = summ.rx2('coefficients')
        if fixed_eff is not None:
            # Convert R matrix to numpy/pandas
            with localconverter(ro.default_converter + pandas2ri.converter):
                coefs_df = ro.conversion.rpy2py(fixed_eff)
            
            # Ensure column names are clean
            coefs_df.columns = ['Estimate', 'Std. Error', 'z value', 'Pr(>|z|)']
            
            # Add term names
            coefs_df.index.name = 'term'
            coefs_df = coefs_df.reset_index()
            coefs_df['term'] = coefs_df['term'].str.replace(' ', '_')
            
            logger.info("Successfully extracted model coefficients.")
        else:
            logger.warning("Could not extract coefficients from summary.")
            coefs_df = pd.DataFrame()
    except Exception as e:
        logger.error(f"Error extracting summary: {e}")
        coefs_df = pd.DataFrame()

    metrics = {
        "n_observations": len(df_fit),
        "n_levels_response": len(df_fit["quality_rating"].cat.categories),
        "convergence_code": conv_status,
        "formula": formula_str
    }

    return coefs_df, conv_status, metrics

def save_convergence_report(metrics: Dict[str, Any], output_path: Path):
    """
    Save the convergence status and metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics.
        output_path: Path to save the JSON.
    """
    report = {
        "convergence_status": metrics.get("convergence_code", "unknown"),
        "model_type": "clmm",
        "n_observations": metrics.get("n_observations"),
        "n_levels_response": metrics.get("n_levels_response"),
        "formula": metrics.get("formula")
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved convergence report to {output_path}")

def save_results(df: pd.DataFrame, output_path: Path):
    """
    Save the model results to a CSV file.
    
    Args:
        df: DataFrame containing coefficients.
        output_path: Path to save the CSV.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Saved results to {output_path}")

def main():
    """Main entry point for the CLMM fitting script."""
    parser = argparse.ArgumentParser(description="Fit CLMM to scored dialogues.")
    parser.add_argument("--input", type=str, default=None, help="Path to input parquet (optional)")
    args = parser.parse_args()

    try:
        # 1. Setup
        ensure_directories()
        
        # 2. Load Data
        df = load_scored_dialogues()
        
        # 3. Check Collinearity
        drop_cols, vif_scores = check_collinearity(df)
        
        # 4. Fit Model
        results_df, conv_status, metrics = fit_clmm(df, drop_cols)
        
        if results_df is None:
            logger.error("Model fitting failed. No results to save.")
            sys.exit(1)
        
        # 5. Save Results
        output_csv = DATA_PROCESSED_DIR / "clmm_primary_results.csv"
        save_results(results_df, output_csv)
        
        output_json = DATA_PROCESSED_DIR / "project_status.json"
        save_convergence_report(metrics, output_json)
        
        logger.info("CLMM fitting completed successfully.")
        
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        raise

if __name__ == "__main__":
    main()