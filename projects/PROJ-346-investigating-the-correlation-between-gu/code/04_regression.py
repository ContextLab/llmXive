"""
T023: Implement LASSO/Elastic Net regression with CLR-transformed microbial taxa.

This script fits regularized regression models to predict cognitive flexibility
scores from microbiome composition.

CRITICAL:
1. Checks for merged_dataset.parquet; if missing, exits gracefully (Data Gap).
2. All outputs are explicitly labeled 'associational only'.
3. Uses real data from the pipeline; no synthetic fallbacks.
"""
import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import scipy.stats as stats

# Import from local utils
from utils import get_data_processed_path, get_data_qc_path, get_project_root_path, setup_logger

# Setup logger
logger = setup_logger("regression_analysis")

# Constants
ALPHA_RANGE = np.logspace(-4, 1, 50)
L1_RANGES = [0.5]  # ElasticNet mix: 0.5 is a balanced default
RANDOM_STATE = 42

def load_merged_data():
    """
    Load the merged dataset from data/processed/merged_dataset.parquet.
    
    Returns:
        pd.DataFrame: The merged dataset.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    project_root = get_project_root_path()
    # Note: get_data_processed_path() is called without arguments to match
    # the call sites in 04_regression.py, 07_gap_report.py, etc.
    # The function in utils.py handles both cases (with or without args).
    data_dir = get_data_processed_path() 
    
    file_path = data_dir / "merged_dataset.parquet"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {file_path}. "
                                "Data gap detected. Exiting gracefully.")
    
    logger.info(f"Loading merged dataset from {file_path}")
    df = pd.read_parquet(file_path)
    return df

def apply_clr_transform(df, taxon_columns):
    """
    Apply Centered Log-Ratio (CLR) transform to microbial taxa.
    
    CLR(x) = ln(x / g(x)) where g(x) is the geometric mean of x.
    Handles zeros by adding a small pseudocount.
    
    Args:
        df: DataFrame containing taxa columns.
        taxon_columns: List of column names to transform.
        
    Returns:
        DataFrame with CLR-transformed values.
    """
    df_clr = df.copy()
    pseudocount = 1e-6
    
    for col in taxon_columns:
        # Add pseudocount to handle zeros
        x = df_clr[col] + pseudocount
        # Calculate geometric mean (exp of mean of logs)
        log_x = np.log(x)
        geometric_mean = np.exp(log_x.mean())
        # CLR transform
        df_clr[col] = np.log(x / geometric_mean)
        
    return df_clr

def prepare_features(df):
    """
    Prepare features (predictors) and target (outcome) for regression.
    
    Features: CLR-transformed taxa + Age, Sex, BMI (covariates).
    Target: Cognitive score (z-scored).
    
    Args:
        df: Merged dataset.
        
    Returns:
        X: Feature DataFrame.
        y: Target Series.
        feature_names: List of feature names for interpretation.
    """
    # Identify taxa columns (assuming they start with 'taxon_' or similar, 
    # or we can use a specific list if available in metadata)
    # For this implementation, we assume columns ending in '_abundance' or 
    # specific taxon names are present. 
    # Let's filter for numeric columns that are likely taxa (excluding metadata)
    metadata_cols = ['sample_id', 'participant_id', 'age', 'sex', 'bmi', 'task_type', 'z_score']
    # Also exclude non-numeric
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Heuristic: Taxa columns are numeric but not in metadata
    # We'll assume 'taxon_name' was pivoted or columns are named 'taxon_X'
    # If the schema is different, we adapt.
    # Let's look for columns that are NOT in metadata_cols
    potential_taxa = [c for c in numeric_cols if c not in metadata_cols]
    
    if not potential_taxa:
        # Fallback: try to find columns with 'abundance' or 'taxon' in name
        potential_taxa = [c for c in df.columns if ('abundance' in c.lower() or 'taxon' in c.lower()) and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not potential_taxa:
        logger.warning("No taxa columns found. Attempting to use all numeric columns except metadata.")
        potential_taxa = [c for c in numeric_cols if c not in metadata_cols]

    if not potential_taxa:
        raise ValueError("Could not identify any taxa columns for regression.")

    logger.info(f"Identified {len(potential_taxa)} taxa columns for regression.")

    # Prepare Target
    if 'z_score' not in df.columns:
        raise ValueError("Target column 'z_score' not found in merged dataset.")
    y = df['z_score']

    # Prepare Features
    # 1. CLR-transformed taxa
    df_taxa = df[potential_taxa]
    df_taxa_clr = apply_clr_transform(df_taxa, potential_taxa)
    
    # 2. Covariates (Age, Sex, BMI)
    covariates = []
    if 'age' in df.columns:
        covariates.append('age')
    if 'sex' in df.columns:
        # Encode sex if categorical
        if df['sex'].dtype == 'object':
            df['sex_encoded'] = df['sex'].map({'Male': 0, 'Female': 1, 'M': 0, 'F': 1}).fillna(0)
            covariates.append('sex_encoded')
        else:
            covariates.append('sex')
    if 'bmi' in df.columns:
        covariates.append('bmi')
        
    df_cov = df[covariates] if covariates else pd.DataFrame()

    # Combine
    X = pd.concat([df_taxa_clr, df_cov], axis=1)
    feature_names = list(X.columns)
    
    logger.info(f"Prepared {X.shape[1]} features for regression.")
    
    return X, y, feature_names

def fit_lasso_elasticnet(X, y, feature_names):
    """
    Fit Elastic Net regression with cross-validation for alpha selection.
    
    Args:
        X: Feature DataFrame.
        y: Target Series.
        feature_names: List of feature names.
        
    Returns:
        dict: Results including coefficients, alpha, R2, and metadata.
    """
    # Handle missing values in X or y
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_clean = X[mask]
    y_clean = y[mask]
    
    if len(X_clean) < 5:
        logger.warning("Insufficient samples after cleaning for regression.")
        return {
            "status": "failed",
            "reason": "Insufficient samples",
            "coefficients": {},
            "alpha": None,
            "r2": None,
            "associational_framing": "This analysis is associational only."
        }

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_clean)
    
    # Fit Elastic Net with CV
    # L1_ratio=0.5 for Elastic Net (mix of L1 and L2)
    model = ElasticNetCV(
        l1_ratio=0.5,
        alphas=ALPHA_RANGE,
        cv=5,
        random_state=RANDOM_STATE,
        max_iter=10000,
        n_jobs=-1
    )
    
    model.fit(X_scaled, y_clean)
    
    # Extract coefficients (inverse transform scaling is not needed for coefficients themselves,
    # but interpretation assumes scaled features)
    coefficients = dict(zip(feature_names, model.coef_))
    
    # Calculate R2 on the full clean set (not just CV)
    y_pred = model.predict(X_scaled)
    r2 = model.score(X_scaled, y_clean)
    
    # Significant features (non-zero coefficients)
    significant_features = {k: v for k, v in coefficients.items() if v != 0}
    
    logger.info(f"Model fit complete. Alpha: {model.alpha_:.4f}, R2: {r2:.4f}")
    logger.info(f"Non-zero coefficients: {len(significant_features)}/{len(feature_names)}")
    
    return {
        "status": "success",
        "model_type": "ElasticNet (L1_ratio=0.5)",
        "alpha": float(model.alpha_),
        "r2": float(r2),
        "coefficients": coefficients,
        "significant_features": significant_features,
        "n_samples": int(len(y_clean)),
        "n_features": int(len(feature_names)),
        "associational_framing": "These results represent associational relationships only. "
                                 "No causal inference is made regarding microbiome composition and cognitive flexibility."
    }

def save_results(results, feature_names):
    """
    Save regression results to data/processed/regression_results.json.
    
    Args:
        results: Dict of results.
        feature_names: List of feature names.
    """
    project_root = get_project_root_path()
    # Use get_data_processed_path() without args to match call sites
    processed_dir = get_data_processed_path()
    
    output_path = processed_dir / "regression_results.json"
    
    # Ensure directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    results["metadata"] = {
        "script": "code/04_regression.py",
        "task_id": "T023",
        "timestamp": str(pd.Timestamp.now()),
        "feature_count": len(feature_names)
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    logger.info(f"Results saved to {output_path}")
    return output_path

def main():
    """
    Main execution function for T023.
    
    1. Checks for merged_dataset.parquet.
    2. If missing, generates a graceful exit message and a 'N/A' report.
    3. If present, performs CLR transform, feature prep, and model fitting.
    4. Saves results.
    """
    logger.info("Starting T023: Regression Analysis (LASSO/Elastic Net)")
    
    try:
        # Step 1: Load Data
        df = load_merged_data()
        logger.info(f"Loaded {len(df)} samples.")
        
        # Step 2: Prepare Features
        X, y, feature_names = prepare_features(df)
        
        # Step 3: Fit Model
        results = fit_lasso_elasticnet(X, y, feature_names)
        
        # Step 4: Save Results
        save_results(results, feature_names)
        
        logger.info("T023 completed successfully.")
        
    except FileNotFoundError as e:
        # Data Gap Scenario: Exit gracefully, log, and create a minimal N/A report
        logger.warning(str(e))
        logger.info("Data Gap detected. Generating N/A report.")
        
        project_root = get_project_root_path()
        processed_dir = get_data_processed_path()
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = processed_dir / "regression_results.json"
        
        na_results = {
            "status": "skipped",
            "reason": "Data Gap - No merged dataset found.",
            "message": "Individual-level data linkage failed. Regression analysis not performed.",
            "associational_framing": "N/A - Analysis skipped due to data gap. "
                                     "No causal or associational claims can be made.",
            "metadata": {
                "script": "code/04_regression.py",
                "task_id": "T023",
                "timestamp": str(pd.Timestamp.now()),
                "feature_count": 0
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(na_results, f, indent=2)
            
        logger.info(f"N/A report saved to {output_path}")
        sys.exit(0) # Graceful exit
        
    except Exception as e:
        logger.error(f"Unexpected error during regression analysis: {e}")
        raise

if __name__ == "__main__":
    main()
