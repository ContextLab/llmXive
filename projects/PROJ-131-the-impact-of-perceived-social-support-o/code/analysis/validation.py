import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logger
logger = logging.getLogger(__name__)

def load_intermediate_cohort(path: Path) -> pd.DataFrame:
    """Load the intermediate cohort CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Intermediate cohort not found at {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded intermediate cohort with {len(df)} rows and {len(df.columns)} columns")
    return df

def calculate_smd(group1: pd.Series, group2: pd.Series) -> float:
    """Calculate Standardized Mean Difference (SMD) between two groups."""
    mean1 = group1.mean()
    mean2 = group2.mean()
    std_pooled = np.sqrt((group1.std()**2 + group2.std()**2) / 2)
    if std_pooled == 0:
        return 0.0
    return (mean1 - mean2) / std_pooled

def check_balance(df: pd.DataFrame, treatment_col: str = 'harassment_exposure') -> Dict[str, float]:
    """Check covariate balance between treatment and control groups."""
    if treatment_col not in df.columns:
        raise ValueError(f"Treatment column '{treatment_col}' not found in dataframe")
    
    treated = df[df[treatment_col] == 1]
    control = df[df[treatment_col] == 0]
    
    # Identify numeric covariates (excluding the treatment itself and outcomes)
    covariates = df.select_dtypes(include=[np.number]).columns.tolist()
    if treatment_col in covariates:
        covariates.remove(treatment_col)
    
    # Remove outcome variables if they exist in numeric columns to avoid checking them as covariates
    outcomes = ['depression', 'anxiety', 'ptsd']
    for outcome in outcomes:
        if outcome in covariates:
            covariates.remove(outcome)
    
    balance_stats = {}
    for col in covariates:
        s = df[col]
        smd = calculate_smd(s[treated.index], s[control.index])
        balance_stats[col] = abs(smd)
    
    return balance_stats

def check_harassment_variance(df: pd.DataFrame, threshold_sd: float = 0.2, min_exposed_n: int = 30) -> Dict[str, Any]:
    """
    Check 1: Variance of Harassment Exposure.
    - SD > threshold_sd
    - N > min_exposed_n for exposed group
    """
    if 'harassment_exposure' not in df.columns:
        raise ValueError("Column 'harassment_exposure' not found in dataframe")
    
    exposure = df['harassment_exposure']
    sd = exposure.std()
    n_exposed = exposure.sum()
    
    passed_sd = sd > threshold_sd
    passed_n = n_exposed >= min_exposed_n
    
    logger.info(f"Harassment Exposure Check: SD={sd:.4f} (>{threshold_sd}? {passed_sd}), N_exposed={n_exposed} (>={min_exposed_n}? {passed_n})")
    
    return {
        "check": "harassment_variance",
        "passed": passed_sd and passed_n,
        "details": {
            "sd": float(sd),
            "threshold_sd": threshold_sd,
            "n_exposed": int(n_exposed),
            "min_exposed_n": min_exposed_n,
            "passed_sd": passed_sd,
            "passed_n": passed_n
        }
    }

def check_social_support_variance(df: pd.DataFrame, threshold_sd: float = 0.5) -> Dict[str, Any]:
    """
    Check 2: Variance of Social Support.
    - SD > threshold_sd
    """
    if 'social_support' not in df.columns:
        raise ValueError("Column 'social_support' not found in dataframe")
    
    support = df['social_support']
    sd = support.std()
    passed = sd > threshold_sd
    
    logger.info(f"Social Support Variance Check: SD={sd:.4f} (>{threshold_sd}? {passed})")
    
    return {
        "check": "social_support_variance",
        "passed": passed,
        "details": {
            "sd": float(sd),
            "threshold_sd": threshold_sd
        }
    }

def check_vif(df: pd.DataFrame, 
              covariates: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Check 3: Multicollinearity via VIF.
    Model matrix: social_support, harassment_exposure, interaction, plus covariates.
    Ensure all VIF < 5.
    """
    required_cols = ['social_support', 'harassment_exposure']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in dataframe")
    
    # Create interaction term
    df_temp = df.copy()
    df_temp['interaction'] = df_temp['social_support'] * df_temp['harassment_exposure']
    
    # Define base predictors
    predictors = ['social_support', 'harassment_exposure', 'interaction']
    
    # Add covariates if provided (typically demographics)
    if covariates:
        # Filter to existing columns only
        available_covariates = [c for c in covariates if c in df_temp.columns]
        predictors.extend(available_covariates)
    
    # Ensure we have a numeric matrix
    X = df_temp[predictors].dropna()
    
    if len(X) < len(predictors) + 1:
        raise ValueError("Not enough samples to compute VIF for the specified predictors")
    
    # Add constant for VIF calculation
    X_with_const = sm.add_constant(X)
    
    vif_results = {}
    max_vif = 0.0
    all_passed = True
    
    for i, col in enumerate(X_with_const.columns):
        if col == 'const':
            continue
        try:
            vif_val = variance_inflation_factor(X_with_const.values, i)
            vif_results[col] = float(vif_val)
            if vif_val >= 5.0:
                all_passed = False
            if vif_val > max_vif:
                max_vif = vif_val
        except Exception as e:
            logger.warning(f"Could not compute VIF for {col}: {e}")
            vif_results[col] = float('nan')
    
    logger.info(f"VIF Check: Max VIF={max_vif:.2f} (threshold 5.0). Passed: {all_passed}")
    
    return {
        "check": "multicollinearity_vif",
        "passed": all_passed,
        "details": {
            "max_vif": float(max_vif),
            "threshold": 5.0,
            "vif_by_variable": vif_results
        }
    }

def validate_synthetic_cohort(input_path: Path, output_path: Path) -> bool:
    """
    Main validation function for T015.
    Loads intermediate cohort, runs checks, saves JSON report.
    Raises Exception with E-VALIDATION-001 if any check fails.
    """
    logger.info(f"Starting validation of cohort at {input_path}")
    df = load_intermediate_cohort(input_path)
    
    results = {
        "input_file": str(input_path),
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "checks": []
    }
    
    # Check 1: Harassment Variance
    try:
        res1 = check_harassment_variance(df)
        results["checks"].append(res1)
    except Exception as e:
        logger.error(f"Harassment variance check failed: {e}")
        results["checks"].append({"check": "harassment_variance", "passed": False, "error": str(e)})
    
    # Check 2: Social Support Variance
    try:
        res2 = check_social_support_variance(df)
        results["checks"].append(res2)
    except Exception as e:
        logger.error(f"Social support variance check failed: {e}")
        results["checks"].append({"check": "social_support_variance", "passed": False, "error": str(e)})
    
    # Check 3: VIF
    # Standard covariates based on data model: age, gender, education, income
    covariates = ['age', 'gender', 'education', 'income']
    try:
        res3 = check_vif(df, covariates=covariates)
        results["checks"].append(res3)
    except Exception as e:
        logger.error(f"VIF check failed: {e}")
        results["checks"].append({"check": "multicollinearity_vif", "passed": False, "error": str(e)})
    
    # Determine overall pass
    all_passed = all(check["passed"] for check in results["checks"] if "passed" in check)
    results["overall_passed"] = all_passed
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")
    
    if not all_passed:
        error_details = [c for c in results["checks"] if not c.get("passed", True)]
        raise Exception(f"E-VALIDATION-001: Cohort validation failed. Failing checks: {[c['check'] for c in error_details]}")
    
    return True

def main():
    """Entry point for T015 validation."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Paths relative to project root
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / "data" / "results" / "intermediate_cohort.csv"
    output_path = base_dir / "data" / "results" / "validation_report.json"
    
    try:
        validate_synthetic_cohort(input_path, output_path)
        logger.info("Validation completed successfully.")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        # Re-raise to ensure pipeline stops if this is run directly
        raise

if __name__ == "__main__":
    main()
