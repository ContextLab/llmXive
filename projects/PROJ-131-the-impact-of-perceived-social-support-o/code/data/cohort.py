import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.config_loader import get_seed

def load_preprocessed_data(file_path: Path, logger: logging.Logger):
    """Load preprocessed data from CSV."""
    import pandas as pd
    logger.info(f"Loading preprocessed data from {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {file_path}")
    return pd.read_csv(file_path)

def filter_critical_missing(df: pd.DataFrame, logger: logging.Logger):
    """Filter rows with critical missing values."""
    initial = len(df)
    # Drop rows where harassment_severity, social_support, or outcomes are missing
    critical_cols = ['harassment_severity', 'social_support', 'depression', 'anxiety', 'ptsd']
    existing_cols = [c for c in critical_cols if c in df.columns]
    
    if not existing_cols:
        logger.warning("No critical columns found to filter on.")
        return df
    
    df = df.dropna(subset=existing_cols)
    logger.info(f"Filtered {initial - len(df)} rows with critical missing values.")
    return df

def check_harassment_variance(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """Check if harassment_severity has sufficient variance."""
    if 'harassment_severity' not in df.columns:
        logger.error("E-LOW-VAR-001: harassment_severity column missing.")
        return False
    
    sd = df['harassment_severity'].std()
    n = len(df)
    
    logger.info(f"Harassment Severity Variance Check: SD={sd:.4f}, N={n}")
    
    if sd <= 0.5 or n <= 30:
        logger.error(f"E-LOW-VAR-001: Insufficient variance (SD={sd}, N={n}). Halting.")
        return False
    
    return True

def construct_analysis_cohort(df: pd.DataFrame, logger: logging.Logger):
    """Construct the final analysis cohort."""
    logger.info("Constructing analysis cohort.")
    # Ensure required columns exist
    required = ['social_support', 'harassment_severity', 'harassment_exposure']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Select columns for analysis
    cols = ['social_support', 'harassment_severity', 'harassment_exposure', 'depression', 'anxiety']
    if 'ptsd' in df.columns:
        cols.append('ptsd')
    # Add covariates if present
    covariates = ['age', 'gender', 'education', 'income', 'platform']
    for c in covariates:
        if c in df.columns:
            cols.append(c)
    
    return df[cols].copy()

def save_cohort(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    """Save analysis cohort to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Analysis cohort saved to {output_path}")

def validate_analysis_cohort(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, Any]:
    """Validate the cohort (VIF, variance checks)."""
    # Reuse variance check
    var_ok = check_harassment_variance(df, logger)
    
    # VIF check
    vif_ok = True
    vif_results = {}
    
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        from sklearn.preprocessing import StandardScaler
        import pandas as pd
        
        # Prepare model matrix
        model_cols = ['social_support', 'harassment_exposure']
        # Add interaction
        df_temp = df.copy()
        df_temp['interaction'] = df_temp['social_support'] * df_temp['harassment_exposure']
        model_cols.append('interaction')
        
        # Add covariates
        for c in ['age', 'gender', 'education', 'income']:
            if c in df_temp.columns:
                model_cols.append(c)
        
        X = df_temp[model_cols].copy()
        
        # Center variables (StandardScaler with with_std=False)
        scaler = StandardScaler(with_mean=True, with_std=False)
        X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=model_cols, index=df_temp.index)
        
        # Compute VIF
        for i, col in enumerate(X_scaled.columns):
            vif = variance_inflation_factor(X_scaled.values, i)
            vif_results[col] = vif
            if vif >= 5:
                vif_ok = False
                logger.warning(f"High VIF for {col}: {vif:.2f}")
        
    except ImportError:
        logger.warning("statsmodels not installed. Skipping VIF check.")
    except Exception as e:
        logger.error(f"VIF check failed: {str(e)}")
        vif_ok = False
    
    report = {
        "variance_check": var_ok,
        "vif_check": vif_ok,
        "vif_results": vif_results,
        "n_rows": len(df)
    }
    
    # Save report
    report_path = project_root / "data" / "results" / "validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Entry point for cohort construction (T014-T016)."""
    logger = get_logger(__name__)
    logger.info("Starting Cohort Construction")
    
    # Load preprocessed data
    input_path = project_root / "data" / "results" / "preprocessed_data.csv"
    df = load_preprocessed_data(input_path, logger)
    
    # Filter critical missing
    df = filter_critical_missing(df, logger)
    
    # Validate
    report = validate_analysis_cohort(df, logger)
    
    if not report["variance_check"] or not report["vif_check"]:
        logger.error("Cohort validation failed. Halting pipeline.")
        raise RuntimeError("Cohort validity check failed. Aborting.")
    
    # Construct and save
    df_cohort = construct_analysis_cohort(df, logger)
    output_path = project_root / "data" / "results" / "analysis_cohort.csv"
    save_cohort(df_cohort, output_path, logger)
    
    logger.info("Cohort construction completed successfully.")
    return df_cohort

if __name__ == "__main__":
    main()