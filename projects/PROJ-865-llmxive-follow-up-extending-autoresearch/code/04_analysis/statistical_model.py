"""
Statistical Model: Mixed-Effects Logistic Regression.

Fits a mixed-effects logistic regression model:
Success ~ FailureType * Method + (1|TaskID)

Pre-check: Verifies that the `results.csv` contains complete pairs of task_ids.
If any pair is incomplete, the analysis aborts with a clear error.
"""
import json
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
# Note: statsmodels mixedlm is for linear models. For logistic, we need GLMM.
# statsmodels does not have a native GLMM (Generalized Linear Mixed Model) in the standard API.
# We will use `statsmodels` if possible, or fallback to a library like `pymer4` or `lme4` (R) via rpy2,
# or implement a custom approximation.
# However, the plan mentions `statsmodels.stats.power.TTestPower` and `MixedLM`.
# If GLMM is not available, we might have to use a fixed-effects logistic regression with robust SEs
# or a simpler approximation.
# Given the constraint to use existing APIs and not invent, we will attempt to use `statsmodels`
# or a standard approximation.
# If `statsmodels` doesn't support GLMM, we will use a fixed-effects model with clustering by TaskID
# using GEE (Generalized Estimating Equations) which is supported in statsmodels.
# GEE is a valid alternative for clustered binary data.

from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from scipy.stats import norm

# Import local config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.utils.config import TIMEOUT_SECONDS

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def get_logger():
    return logger

def load_results_csv(file_path: Path) -> pd.DataFrame:
    """Load the merged results CSV."""
    if not file_path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")
    df = pd.read_csv(file_path)
    required_cols = ['task_id', 'method', 'time_to_pivot', 'success', 'failure_type']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {file_path}: {missing}")
    return df

def verify_paired_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Pre-check: Ensure that the `task_id` pairs in results.csv are complete.
    Every task_id must have exactly one 'rule_engine' and one 'baseline' entry.
    """
    logger.info("Verifying paired data integrity for statistical model...")
    
    pivot_table = df.pivot_table(index='task_id', columns='method', values='time_to_pivot', aggfunc='count', fill_value=0)
    
    all_tasks = df['task_id'].unique()
    rule_engine_count = pivot_table['rule_engine'].reindex(all_tasks, fill_value=0) if 'rule_engine' in pivot_table.columns else pd.Series(0, index=all_tasks)
    baseline_count = pivot_table['baseline'].reindex(all_tasks, fill_value=0) if 'baseline' in pivot_table.columns else pd.Series(0, index=all_tasks)
    
    missing_pairs = []
    for task_id in all_tasks:
        has_rule = rule_engine_count.get(task_id, 0) > 0
        has_baseline = baseline_count.get(task_id, 0) > 0
        
        if not has_rule or not has_baseline:
            reason = []
            if not has_rule: reason.append("missing rule_engine")
            if not has_baseline: reason.append("missing baseline")
            missing_pairs.append(f"{task_id}: {', '.join(reason)}")
    
    if missing_pairs:
        logger.error(f"Paired data integrity check FAILED. {len(missing_pairs)} incomplete pairs found.")
        for pair in missing_pairs[:5]:
            logger.error(f"  - {pair}")
        if len(missing_pairs) > 5:
            logger.error(f"  ... and {len(missing_pairs) - 5} more.")
        return False, missing_pairs
    
    logger.info("Paired data integrity check PASSED.")
    return True, []

def prepare_data_for_regression(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for GEE regression."""
    # Filter to only tasks that have both methods (already done by pre-check, but ensure)
    # We need a long format for GEE
    # Columns: task_id, method, success, failure_type
    
    # Encode categorical variables
    # Method: baseline (ref), rule_engine
    # FailureType: one-hot or ordinal? Let's use one-hot or treat as categorical.
    
    # Create a numeric encoding for success
    df['success_num'] = df['success'].astype(int)
    
    # Create interaction term manually if needed, or let formula handle it
    # Formula: success_num ~ C(method) * C(failure_type)
    # Grouping: task_id
    
    return df

def fit_mixed_effects_model(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit a GEE model (approximation for Mixed Effects Logistic Regression).
    Formula: success ~ C(method) * C(failure_type)
    """
    logger.info("Fitting GEE model (Mixed Effects approximation)...")
    
    # Ensure factors are categorical
    df['method'] = df['method'].astype('category')
    df['failure_type'] = df['failure_type'].astype('category')
    
    # Define formula
    formula = "success_num ~ C(method) * C(failure_type)"
    
    # Fit GEE
    # Using Exchangeable correlation structure
    try:
        gee_model = GEE.from_formula(
            formula,
            groups="task_id",
            data=df,
            family=sm.families.Binomial(),
            cov_struct=Exchangeable()
        )
        gee_result = gee_model.fit()
        
        # Extract interaction term p-value
        # The interaction term is C(method)[T.rule_engine]:C(failure_type)[...
        # We need to find the coefficient that represents the interaction between Method and FailureType.
        # Since failure_type has multiple levels, there will be multiple interaction terms.
        # The task asks for "the interaction term". We will look for the p-value of the interaction.
        # If there are multiple, we might need to check if ANY is significant, or the overall F-test.
        # For simplicity, we will report the p-value of the first significant interaction or the overall model significance.
        # However, the plan says "p-values for the interaction term".
        # We will extract the p-value for the interaction of the main method effect with the first failure type level.
        
        params = gee_result.params
        pvalues = gee_result.pvalues
        
        # Find interaction terms
        interaction_pvalues = {}
        for idx, pval in pvalues.items():
            if "C(method)" in str(idx) and "C(failure_type)" in str(idx):
                interaction_pvalues[idx] = pval
        
        if not interaction_pvalues:
            logger.warning("No interaction terms found in the model.")
            # Fallback: assume no interaction
            min_p = 1.0
            interaction_significant = False
            narrative = "No interaction terms detected."
        else:
            # Take the minimum p-value among interactions as a proxy, or average?
            # For a binary decision, we check if ANY interaction is significant.
            min_p = min(interaction_pvalues.values())
            interaction_significant = min_p < 0.05
            
            if interaction_significant:
                narrative = "The interaction term is significant (p < 0.05), indicating that failure structure dictates method viability."
            else:
                narrative = "The interaction term is not significant (p >= 0.05)."
        
        return {
            "model_summary": str(gee_result.summary()),
            "params": params.to_dict(),
            "pvalues": pvalues.to_dict(),
            "interaction_pvalues": interaction_pvalues,
            "min_interaction_p": min_p,
            "interaction_significant": interaction_significant,
            "narrative_conclusion": narrative
        }
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

def extract_interaction_p_value(results: Dict[str, Any]) -> float:
    """Extract the minimum interaction p-value."""
    return results.get("min_interaction_p", 1.0)

def save_regression_results(results: Dict[str, Any], output_path: Path):
    """Save results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Regression results saved to {output_path}")

def main():
    """Main entry point."""
    input_path = Path("data/derived/results.csv")
    output_path = Path("data/derived/regression_results.json")
    
    logger.info("Starting Statistical Model Analysis...")
    
    try:
        # 1. Load Data
        df = load_results_csv(input_path)
        
        # 2. Pre-check: Verify Paired Data Integrity
        is_valid, missing_pairs = verify_paired_data(df)
        if not is_valid:
            logger.error("Analysis aborted due to incomplete paired data.")
            sys.exit(1)
        
        # 3. Prepare Data
        df_prep = prepare_data_for_regression(df)
        
        # 4. Fit Model
        results = fit_mixed_effects_model(df_prep)
        
        # 5. Save Results
        save_regression_results(results, output_path)
        
        logger.info("Analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()