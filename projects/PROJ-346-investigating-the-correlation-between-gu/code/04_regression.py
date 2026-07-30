import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, KFold
import warnings

# Import shared utilities from utils.py (must exist in code/)
from utils import get_project_root_path, get_data_processed_path, setup_logger, get_logger

# Configure logging
logger = setup_logger(__name__)
log = get_logger(__name__)

# Constants
PROJECT_ROOT = get_project_root_path()
PROCESSED_DATA_DIR = get_data_processed_path()
MERGED_DATASET_PATH = PROCESSED_DATA_DIR / "merged_dataset.parquet"
REGRESSION_OUTPUT_PATH = PROCESSED_DATA_DIR / "regression_results.json"
REGRESSION_COEFFS_PATH = PROCESSED_DATA_DIR / "regression_coefficients.csv"

def load_merged_data():
    """
    Load the merged dataset from the processed data directory.
    Raises FileNotFoundError if the file does not exist.
    """
    if not MERGED_DATASET_PATH.exists():
        raise FileNotFoundError(f"Merged dataset not found at {MERGED_DATASET_PATH}")
    
    logger.info(f"Loading merged dataset from {MERGED_DATASET_PATH}")
    df = pd.read_parquet(MERGED_DATASET_PATH)
    return df

def apply_clr_transform(df, taxa_columns):
    """
    Apply Centered Log-Ratio (CLR) transform to taxa columns.
    Handles zeros by adding a small pseudocount (1e-6) before log transform.
    """
    df_transformed = df.copy()
    pseudocount = 1e-6
    
    for col in taxa_columns:
        if col in df_transformed.columns:
            # Add pseudocount to avoid log(0)
            safe_values = df_transformed[col] + pseudocount
            # Calculate geometric mean for the row across taxa columns
            # Note: Geometric mean of a row across specific columns
            row_geom_means = np.exp(np.mean(np.log(safe_values[taxa_columns].add(pseudocount)), axis=1))
            # CLR = ln(x_i / g(x)) where g(x) is geometric mean of the composition
            # Since we are doing this per row, we need to align indices
            # However, for simplicity in this context, we often use a global geometric mean
            # or row-wise. Let's do row-wise as is standard for compositional data.
            # Re-calculation for row-wise CLR:
            # CLR(x)_i = ln(x_i / g(x)) where g(x) = (product(x_j))^(1/D)
            
            # To vectorize:
            # 1. Add pseudocount to all taxa columns
            taxa_data = df_transformed[taxa_columns].add(pseudocount)
            # 2. Log transform
            log_data = np.log(taxa_data)
            # 3. Row-wise mean (log of geometric mean)
            log_geom_mean = log_data.mean(axis=1)
            # 4. Subtract row-wise mean from each log value
            clr_data = log_data.sub(log_geom_mean, axis=0)
            
            df_transformed[taxa_columns] = clr_data
        else:
            logger.warning(f"Taxa column {col} not found in dataframe")
    
    return df_transformed

def prepare_features(df, target_col='cognitive_score_z', covariates=None):
    """
    Prepare features (X) and target (y) for regression.
    Includes CLR-transformed taxa and covariates (age, sex, BMI).
    """
    if covariates is None:
        covariates = ['age', 'sex', 'bmi']
    
    # Identify taxa columns (assuming they start with 'taxa_' or are the remaining numeric columns not in covariates/target)
    # For robustness, let's assume taxa columns are those not in covariates and not the target, and are numeric
    all_cols = df.columns.tolist()
    feature_cols = [c for c in all_cols if c not in covariates and c != target_col]
    
    # Filter to only numeric columns for taxa
    taxa_cols = [c for c in feature_cols if df[c].dtype in ['float64', 'float32', 'int64', 'int32']]
    
    if not taxa_cols:
        raise ValueError("No taxa columns found for regression.")
    
    # Apply CLR transform to taxa
    df_clr = apply_clr_transform(df, taxa_cols)
    
    # Prepare X
    X = df_clr[taxa_cols + covariates].copy()
    
    # Handle categorical covariates (e.g., 'sex') if necessary
    # Assuming 'sex' is already encoded (0/1) or needs one-hot. 
    # If 'sex' is string, we need to encode it.
    if 'sex' in X.columns and X['sex'].dtype == 'object':
        X = pd.get_dummies(X, columns=['sex'], drop_first=True)
    
    # Prepare y
    y = df_clr[target_col]
    
    # Drop rows with any NaN
    mask = y.notna() & X.notna().all(axis=1)
    X = X[mask]
    y = y[mask]
    
    return X, y, taxa_cols + covariates

def fit_lasso_elasticnet(X, y, l1_ratio=0.5, alpha=0.1, n_folds=5):
    """
    Fit Elastic Net model (Lasso is ElasticNet with l1_ratio=1.0).
    Returns the best model and cross-validation scores.
    """
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Cross-validation
    kfold = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    model = ElasticNet(l1_ratio=l1_ratio, alpha=alpha, random_state=42, max_iter=10000)
    
    # Fit
    model.fit(X_scaled, y)
    
    # Cross-validation scores
    cv_scores = cross_val_score(model, X_scaled, y, cv=kfold, scoring='neg_mean_squared_error')
    mse_scores = -cv_scores
    
    return model, scaler, mse_scores

def save_results(model, scaler, mse_scores, feature_names, output_path, coeffs_path):
    """
    Save regression results to JSON and coefficients to CSV.
    """
    # Coefficients
    coefficients = model.coef_
    intercept = model.intercept_
    
    # Map coefficients to feature names
    coef_dict = dict(zip(feature_names, coefficients.tolist()))
    coef_dict['intercept'] = float(intercept)
    
    # Metrics
    results = {
        "model_type": "ElasticNet",
        "l1_ratio": model.l1_ratio,
        "alpha": model.alpha,
        "mean_mse": float(np.mean(mse_scores)),
        "std_mse": float(np.std(mse_scores)),
        "cv_scores": mse_scores.tolist(),
        "coefficients": coef_dict
    }
    
    # Save JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Regression results saved to {output_path}")
    
    # Save CSV
    coeffs_df = pd.DataFrame({
        'feature': list(coef_dict.keys()),
        'coefficient': list(coef_dict.values())
    })
    coeffs_df.to_csv(coeffs_path, index=False)
    logger.info(f"Coefficients saved to {coeffs_path}")

def main():
    """
    Main entry point for regression analysis.
    Checks for merged dataset; if missing, logs "N/A - Data Gap" and exits gracefully.
    """
    logger.info("Starting regression analysis (T023)")
    
    try:
        # Check for merged dataset
        if not MERGED_DATASET_PATH.exists():
            # CRITICAL: Log the exact required message for Data Gap
            logger.warning("N/A - Data Gap")
            log.warning("N/A - Data Gap")
            # Create a placeholder result file indicating the gap
            output_path = REGRESSION_OUTPUT_PATH
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump({"status": "N/A - Data Gap", "reason": "Merged dataset not found"}, f, indent=2)
            return 0
        
        # Load data
        df = load_merged_data()
        logger.info(f"Loaded {len(df)} samples")
        
        # Prepare features
        X, y, feature_names = prepare_features(df)
        logger.info(f"Prepared features: {len(X)} samples, {len(feature_names)} features")
        
        if len(X) == 0:
            logger.warning("No valid samples after filtering. Skipping regression.")
            return 0
        
        # Fit model
        logger.info("Fitting Elastic Net model...")
        model, scaler, mse_scores = fit_lasso_elasticnet(X, y)
        
        # Save results
        save_results(model, scaler, mse_scores, feature_names, REGRESSION_OUTPUT_PATH, REGRESSION_COEFFS_PATH)
        
        logger.info("Regression analysis completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        # This handles the case where load_merged_data fails (though we check exists first)
        logger.warning("N/A - Data Gap")
        log.warning("N/A - Data Gap")
        return 0
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
