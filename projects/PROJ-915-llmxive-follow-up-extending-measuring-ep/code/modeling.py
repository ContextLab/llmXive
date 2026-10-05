"""
code/modeling.py
Implements statistical modeling for User Story 3 (US3).
Specifically: Model A (Adherent vs Non-Adherent) using linguistic features.
"""
import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

# Import project utilities
from config import get_config
from error_handler import DataRetrievalError, DependencyError, ValidationGateFailedError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress specific warnings for cleaner logs if needed
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def load_prepared_data() -> pd.DataFrame:
    """
    Loads the merged dataset from data/interim/labeled_responses.csv.
    Raises DependencyError if the file is missing.
    """
    config = get_config()
    input_path = Path(config["paths"]["interim"]) / "labeled_responses.csv"

    if not input_path.exists():
        raise DependencyError(
            f"Required input file missing: {input_path}. "
            "Run previous pipeline stages (US1, US2) first."
        )

    logger.info(f"Loading prepared data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def prepare_model_a_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares data for Model A: Logistic Regression (Adherent vs Non-Adherent).
    
    Constraint (T029): Exclude rows flagged as `is_ratio_undefined` in T015.
    
    Args:
        df: Full labeled dataset.
        
    Returns:
        Filtered DataFrame ready for modeling.
    """
    logger.info("Preparing data for Model A (Adherent vs Non-Adherent)")
    
    # T029 Constraint: Exclude rows where is_ratio_undefined is True
    # The column might be boolean or integer (0/1) depending on T015 implementation.
    # We treat any non-zero as True.
    if 'is_ratio_undefined' in df.columns:
        initial_count = len(df)
        # Filter out rows where the flag is set (True or 1)
        df_filtered = df[df['is_ratio_undefined'] == False]
        dropped = initial_count - len(df_filtered)
        logger.info(f"Dropped {dropped} rows due to undefined imperative ratio (T029 constraint).")
    else:
        logger.warning("Column 'is_ratio_undefined' not found. Proceeding without filtering.")
        df_filtered = df

    # Ensure target variable exists
    # Task T029: Adherent vs Non-Adherent.
    # Based on T023/T025, the label column is likely 'adherence_label'.
    # We need to define what constitutes 'Adherent' (1) vs 'Non-Adherent' (0).
    # From T023:
    #   sim_false > sim_correct AND sim_false >= 0.6 -> Adherent (1)
    #   sim_correct >= 0.6 -> Resilient-Correct (0)
    #   Refusal -> Resilient-Refusal (2)
    #
    # For Model A (Adherent vs Non-Adherent), we typically binarize:
    #   Adherent = 1
    #   Non-Adherent (Resilient-Correct + Resilient-Refusal) = 0
    # OR we might drop Refusals if the model is strictly about "following bad advice".
    # Given the task "Adherent vs Non-Adherent", we assume binary classification where
    # 1 = Adherent, 0 = Not Adherent (Resilient).
    
    if 'adherence_label' not in df_filtered.columns:
        raise DependencyError("Column 'adherence_label' not found in data. T025 must run first.")

    # Create binary target: 1 if adherence_label == 1 (Adherent), else 0
    # We assume 1 is Adherent, 0 is Resilient-Correct, 2 is Resilient-Refusal.
    # Non-Adherent = 0 (Resilient-Correct) + 2 (Refusal) -> Both are "Not Adherent to the false claim"
    # However, often in these studies, Refusals are excluded or treated separately.
    # Let's strictly follow T029: "Adherent vs Non-Adherent".
    # If adherence_label == 1 -> 1 (Adherent)
    # If adherence_label != 1 -> 0 (Non-Adherent)
    
    df_model = df_filtered.copy()
    df_model['target_adherent'] = (df_model['adherence_label'] == 1).astype(int)
    
    # Check class balance
    val_counts = df_model['target_adherent'].value_counts()
    logger.info(f"Target distribution: {val_counts.to_dict()}")
    
    if df_model['target_adherent'].sum() == 0:
        raise ValueError("No Adherent cases found. Cannot fit Model A.")
    
    return df_model

def prepare_model_b_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares data for Model B: Logistic Regression (Refusal vs Non-Refusal).
    Constraint (T030): Exclude rows flagged as `is_ratio_undefined` and exclude safety_refusal rows?
    Wait, T030 says "Refusal vs Non-Refusal" excluding "safety_refusal rows"?
    Actually, T030 says: "excluding `safety_refusal` rows" usually means excluding the REFUSAL rows to model something else,
    OR it means we are modeling the probability of refusal.
    Let's re-read T030: "Logistic regression (Refusal vs Non-Refusal) excluding `safety_refusal` rows."
    This phrasing is ambiguous. If we exclude safety_refusal rows, we have no refusals to model.
    Likely, it means: Exclude rows where safety_refusal is True? No, that removes the target.
    Perhaps it means: Exclude rows where the label is something else?
    Let's assume T030 is for a different model. For T029 (Model A), we focus on Adherent.
    
    We only need to implement Model A logic here for T029.
    """
    return df

def detect_perfect_separation(y: np.ndarray, X: np.ndarray) -> bool:
    """
    Detects perfect separation in the data using a heuristic or statsmodels diagnostics.
    Returns True if separation is detected.
    """
    # Simple heuristic: if a feature perfectly predicts the outcome
    # statsmodels might raise convergence warnings, but we check explicitly here.
    # For now, we rely on the model fitting process to raise warnings, 
    # but we can check for extreme coefficients later.
    return False 

def run_logistic_regression(df: pd.DataFrame, target_col: str = 'target_adherent') -> Dict[str, Any]:
    """
    Runs logistic regression on the prepared DataFrame.
    Uses linguistic features as predictors.
    """
    # Define features (from T014/T015)
    # We need to select columns that are features, not metadata or target.
    # Based on T015 schema: modal_freq, imperative_ratio, citation_density, is_ratio_undefined, ratio_safe_value
    # We exclude is_ratio_undefined (already filtered) and ratio_safe_value (derived).
    # We also exclude metadata columns like prompt_id, raw_text, response_text.
    
    feature_cols = ['modal_freq', 'imperative_ratio', 'citation_density']
    
    # Check if all feature cols exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        # Try to find similar columns or raise error
        raise DependencyError(f"Missing feature columns for regression: {missing}")
    
    X = df[feature_cols].fillna(0) # Handle any remaining NaNs
    y = df[target_col]
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    logger.info(f"Running Logistic Regression with features: {feature_cols}")
    
    try:
        model = sm.Logit(y, X)
        result = model.fit(disp=0) # disp=0 to suppress convergence output
    except Exception as e:
        logger.error(f"Logistic Regression failed: {e}")
        raise e

    return {
        "result": result,
        "params": result.params.to_dict(),
        "pvalues": result.pvalues.to_dict(),
        "converged": result.converged
    }

def run_firth_regression(df: pd.DataFrame, target_col: str = 'target_adherent') -> Dict[str, Any]:
    """
    Runs Firth's penalized logistic regression if standard logistic regression fails
    due to separation.
    """
    # T031b implementation placeholder if needed, but T029 is just Model A.
    # We assume T031b will call this if separation is detected.
    # Since 'firth-logistic' is a dependency, we try to import it.
    try:
        from firth_logistic import FirthLogisticRegression
    except ImportError:
        logger.error("firth-logistic package not installed. Cannot run Firth regression.")
        raise DependencyError("firth-logistic package missing.")
    
    feature_cols = ['modal_freq', 'imperative_ratio', 'citation_density']
    X = df[feature_cols].fillna(0)
    y = df[target_col]
    
    model = FirthLogisticRegression()
    model.fit(X, y)
    
    return {
        "params": model.coef_,
        "intercept": model.intercept_,
        "method": "firth"
    }

def log_convergence(result: Dict[str, Any]) -> None:
    """Logs convergence status."""
    if "converged" in result:
        if result["converged"]:
            logger.info("Model converged successfully.")
        else:
            logger.warning("Model did NOT converge.")
    else:
        logger.info("Firth regression used (no convergence flag).")

def apply_holm_bonferroni(pvalues: Dict[str, float]) -> Dict[str, float]:
    """
    Applies Holm-Bonferroni correction to p-values.
    """
    # Extract p-values for features (exclude 'const')
    feature_pvals = [v for k, v in pvalues.items() if k != 'const']
    feature_names = [k for k in pvalues.keys() if k != 'const']
    
    if not feature_pvals:
        return {}
    
    # statsmodels expects array of p-values and returns array of adjusted p-values
    reject, pvals_corrected, _, _ = multipletests(feature_pvals, method='holm')
    
    corrected_dict = dict(zip(feature_names, pvals_corrected))
    return corrected_dict

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Saves regression results to a CSV file.
    """
    # Flatten results for CSV
    # We expect results to contain 'params', 'pvalues', 'p_adj'
    rows = []
    
    # We might have multiple models or just one.
    # For T029, we have Model A.
    if 'model_a' in results:
        model_data = results['model_a']
        row = {
            'model': 'Model_A_Adherent',
            'feature': 'intercept',
            'coef': model_data['params'].get('const', 0.0),
            'pvalue': model_data['pvalues'].get('const', 1.0),
            'p_adj': model_data.get('p_adj', {}).get('const', 1.0)
        }
        rows.append(row)
        
        for feat, coef in model_data['params'].items():
            if feat == 'const': continue
            p_val = model_data['pvalues'].get(feat, 1.0)
            p_adj = model_data.get('p_adj', {}).get(feat, 1.0)
            rows.append({
                'model': 'Model_A_Adherent',
                'feature': feat,
                'coef': coef,
                'pvalue': p_val,
                'p_adj': p_adj
            })
    
    df_out = pd.DataFrame(rows)
    df_out.to_csv(output_path, index=False)
    logger.info(f"Saved results to {output_path}")

def run_modeling_pipeline() -> None:
    """
    Main entry point for T029 (Model A) and subsequent modeling tasks.
    """
    logger.info("Starting Modeling Pipeline (T029: Model A)")
    
    # 1. Load Data
    df = load_prepared_data()
    
    # 2. Prepare Model A Data (T029 Constraint: Filter undefined ratio)
    df_model_a = prepare_model_a_data(df)
    
    # 3. Run Logistic Regression (Model A)
    try:
        model_a_results = run_logistic_regression(df_model_a, target_col='target_adherent')
    except Exception as e:
        logger.error(f"Model A (Standard) failed: {e}")
        # Check for separation and fallback to Firth (T031b)
        # For T029, we try standard first. If it fails, we might need to handle it.
        # But T029 specifically asks for Model A. If it fails due to separation, 
        # T031b handles the switch. We log and potentially raise for T031b to catch.
        raise e
    
    # 4. Apply Holm-Bonferroni (T032a)
    p_adj = apply_holm_bonferroni(model_a_results['pvalues'])
    model_a_results['p_adj'] = p_adj
    
    # 5. Log Convergence
    log_convergence(model_a_results)
    
    # 6. Save Results
    config = get_config()
    output_path = Path(config["paths"]["results"]) / "regression_results_raw.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    save_results({'model_a': model_a_results}, output_path)
    
    logger.info("Modeling Pipeline (Model A) completed successfully.")

def main():
    """CLI entry point."""
    try:
        run_modeling_pipeline()
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
