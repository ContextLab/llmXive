import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import Binomial
from statsmodels.stats.multitest import multipletests
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress convergence warnings for cleaner logs during fitting attempts
warnings.filterwarnings("ignore", category=ConvergenceWarning)

class GLMConvergenceError(Exception):
    """Raised when GLM fitting fails to converge."""
    pass

def load_results_data(filepath: str = "data/results.csv") -> pd.DataFrame:
    """
    Load the merged results CSV.
    Expects columns: issue_id, model_size (1B/7B), strategy (baseline/tfidf/diff/semantic), pass_status (0/1)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Results file not found: {filepath}. Run merge_results.py first.")
    df = pd.read_csv(filepath)
    # Ensure numeric types
    df['pass_status'] = pd.to_numeric(df['pass_status'], errors='coerce').fillna(0).astype(int)
    
    # Map string labels to categorical for GLM if needed, but statsmodels handles strings in formula
    # Ensure we have the specific columns expected by the analysis
    required_cols = ['issue_id', 'model_size', 'strategy', 'pass_status']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Results CSV missing required columns. Found: {df.columns.tolist()}, Expected: {required_cols}")
    
    return df

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for GLM.
    Ensures model_size and strategy are treated as categorical factors.
    """
    df = df.copy()
    df['model_size'] = df['model_size'].astype('category')
    df['strategy'] = df['strategy'].astype('category')
    return df

def fit_firth_glm(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Attempt to fit a Firth Penalized Likelihood GLM.
    Note: statsmodels does not have a native 'Firth' family in standard GLM.
    We attempt standard GLM first; if it fails, we try robust fitting or return None.
    For this implementation, we use standard GLM with binomial family.
    If convergence fails, we catch it and return None to signal fallback or error.
    """
    try:
        # Formula: pass_status ~ model_size * strategy
        # This tests main effects and interaction
        formula = "pass_status ~ C(model_size) * C(strategy)"
        model = GLM.from_formula(formula, data=df, family=Binomial())
        result = model.fit()
        return {
            "model": result,
            "converged": result.mle_retvals.get('converged', False),
            "params": result.params.to_dict(),
            "pvalues": result.pvalues.to_dict()
        }
    except Exception as e:
        logger.warning(f"Firth/Standard GLM fit failed: {e}")
        return None

def fit_glm_with_interaction(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Fit a standard GLM with interaction terms.
    """
    try:
        formula = "pass_status ~ C(model_size) * C(strategy)"
        model = GLM.from_formula(formula, data=df, family=Binomial())
        result = model.fit()
        return {
            "model": result,
            "converged": result.mle_retvals.get('converged', False),
            "params": result.params.to_dict(),
            "pvalues": result.pvalues.to_dict(),
            "summary": str(result.summary())
        }
    except Exception as e:
        logger.error(f"GLM with interaction failed: {e}")
        return None

def perform_post_hoc_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform post-hoc pairwise comparison.
    Requirement: Explicitly calculate the difference in Pass@1 rates ONLY between:
    1. 1B-model (high-fidelity) vs 7B-model (baseline)
    
    We filter the dataframe to these two specific groups and calculate:
    - Pass@1 for 1B-HighFidelity (mean of pass_status where model_size=1B AND strategy in [tfidf, diff, semantic])
    - Pass@1 for 7B-Baseline (mean of pass_status where model_size=7B AND strategy=baseline)
    
    Since we need a p-value for the difference between two proportions (or groups),
    and the requirement asks for a specific pair comparison with p < 0.05 and delta >= 0.05,
    we will perform a two-proportion z-test or a t-test on the means if sample sizes are large enough.
    
    However, the task asks for "post-hoc" logic typically associated with the GLM.
    Since we are comparing specific groups (1B-HF vs 7B-Baseline), we can extract the means
    and perform a statistical test (e.g., scipy.stats.ttest_ind or proportion_ztest).
    
    Let's implement a robust comparison:
    1. Identify 1B-HF group (1B + any high-fidelity strategy)
    2. Identify 7B-Baseline group (7B + baseline strategy)
    3. Calculate pass rates (proportions).
    4. Perform a two-sample z-test for proportions to get p-value.
    """
    results = {
        "comparison": "1B-HighFidelity vs 7B-Baseline",
        "condition_met": False,
        "entries": []
    }

    # Filter groups
    # High fidelity strategies are: 'tfidf', 'diff_aware', 'semantic' (based on context_processors)
    # Baseline is 'baseline' (or 'naive')
    
    hf_strategies = ['tfidf', 'diff_aware', 'semantic', 'tfidf', 'diff', 'semantic'] # Handle potential naming variations
    # Normalize strategy names to be safe
    df['strategy_clean'] = df['strategy'].astype(str).str.lower().str.replace('-', '_').str.replace(' ', '_')
    
    group_1b_hf = df[
        (df['model_size'].astype(str).str.contains('1B|1|small', case=False, na=False)) & 
        (df['strategy_clean'].isin(['tfidf', 'diff_aware', 'semantic', 'diff']))
    ]
    
    group_7b_base = df[
        (df['model_size'].astype(str).str.contains('7B|7|large', case=False, na=False)) & 
        (df['strategy_clean'].isin(['baseline', 'naive', 'first_n']))
    ]

    if len(group_1b_hf) == 0 or len(group_7b_base) == 0:
        logger.warning("One of the comparison groups is empty. Cannot compute statistics.")
        return results

    # Calculate pass rates
    n1 = len(group_1b_hf)
    x1 = group_1b_hf['pass_status'].sum()
    p1 = x1 / n1 if n1 > 0 else 0.0

    n2 = len(group_7b_base)
    x2 = group_7b_base['pass_status'].sum()
    p2 = x2 / n2 if n2 > 0 else 0.0

    delta = p1 - p2
    
    # Two-proportion z-test
    # H0: p1 = p2
    # H1: p1 != p2
    try:
        from statsmodels.stats.proportion import proportions_ztest
        count = [x1, x2]
        nobs = [n1, n2]
        stat, pval = proportions_ztest(count, nobs, alternative='two-sided')
        
        logger.info(f"Pass@1 1B-HF: {p1:.4f} ({n1} samples)")
        logger.info(f"Pass@1 7B-Baseline: {p2:.4f} ({n2} samples)")
        logger.info(f"Delta: {delta:.4f}, P-value: {pval:.6f}")

        entry = {
            "strategy_pair": "1B-HighFidelity vs 7B-Baseline",
            "pass_rate_1b_hf": float(p1),
            "pass_rate_7b_baseline": float(p2),
            "delta": float(delta),
            "p_value": float(pval),
            "n_1b_hf": int(n1),
            "n_7b_baseline": int(n2),
            "margin_met": delta >= 0.05,
            "significance_met": pval < 0.05
        }

        results["entries"].append(entry)
        
        if delta >= 0.05 and pval < 0.05:
            results["condition_met"] = True
            results["summary"] = f"Significant improvement of {delta:.2%} found with p={pval:.4f}."
        else:
            results["summary"] = f"No significant difference (delta={delta:.2%}, p={pval:.4f}) meeting criteria."

    except Exception as e:
        logger.error(f"Statistical test failed: {e}")
        results["error"] = str(e)

    return results

def run_glm_analysis(input_path: str, output_dir: str = "data/analysis") -> None:
    """
    Main entry point for GLM analysis.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "post_hoc_results.json")

    logger.info(f"Loading results from {input_path}")
    df = load_results_data(input_path)
    
    logger.info("Preparing features")
    df = prepare_features(df)

    logger.info("Performing post-hoc analysis (1B-HF vs 7B-Baseline)")
    results = perform_post_hoc_analysis(df)

    logger.info(f"Writing results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info("Analysis complete.")

def main():
    parser = argparse.ArgumentParser(description="Run GLM and Post-Hoc Analysis")
    parser.add_argument("--input", type=str, default="data/results.csv", help="Path to merged results CSV")
    parser.add_argument("--output", type=str, default="data/analysis", help="Output directory for JSON results")
    args = parser.parse_args()

    run_glm_analysis(args.input, args.output)

if __name__ == "__main__":
    main()