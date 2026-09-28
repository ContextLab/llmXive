"""
Mixed-Effects Model Analysis for Robustness Check (US3).

Implements a linear mixed-effects model to verify that design effects persist
after controlling for demographic covariates (Age, Education).

Model Formula: Credibility ~ Condition + Age + Education + (1|Participant)
"""

import os
import sys
import json
import argparse
import warnings
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Suppress specific warnings during model fitting
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
except ImportError:
    logger.error("statsmodels is required. Install via: pip install statsmodels")
    sys.exit(1)

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_cleaned_data_path():
    """Return the path to the cleaned wide-format data."""
    return get_project_root() / "data" / "raw" / "participants.csv"

def get_anova_results_path():
    """Return the path to the ANOVA results file."""
    return get_project_root() / "data" / "processed" / "anova_results.json"

def get_output_path():
    """Return the path for the mixed effects results."""
    return get_project_root() / "data" / "processed" / "mixed_effects_results.json"

def load_wide_data_for_mixed(input_path):
    """
    Load the wide-format data required for mixed effects analysis.
    Validates that required columns exist.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data file not found at {input_path}. "
                                "Please run 00_preprocess.py first to generate participants.csv.")

    df = pd.read_csv(input_path)

    required_cols = ['participant_id', 'condition', 'credibility_mean', 'age', 'education']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")

    # Ensure categorical variables are treated as such
    df['condition'] = df['condition'].astype('category')
    df['participant_id'] = df['participant_id'].astype('category')

    # Drop rows with missing values in critical columns
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows with missing values.")

    return df

def check_residual_normality(residuals):
    """
    Perform a Shapiro-Wilk test for normality on residuals.
    Returns True if residuals are normally distributed (p > 0.05).
    """
    from scipy.stats import shapiro
    stat, p_value = shapiro(residuals)
    logger.info(f"Shapiro-Wilk Normality Test: W={stat:.4f}, p={p_value:.4f}")
    return p_value > 0.05

def transform_variable(data, column, method='log'):
    """
    Apply a transformation to a variable if needed.
    Currently supports 'log' for positive-only values.
    """
    if method == 'log':
        if (data[column] <= 0).any():
            raise ValueError(f"Cannot apply log transform to {column} containing non-positive values.")
        return np.log(data[column])
    return data[column]

def run_mixed_effects_model_with_convergence(df, formula, max_iter=1000):
    """
    Run the mixed effects model with convergence checks.
    Returns the fitted model and convergence status.
    """
    logger.info(f"Fitting Mixed Effects Model: {formula}")
    try:
        # Use REML for estimation
        model = smf.lme_fixed_effects(
            formula,
            data=df,
            re_formula="1 | participant_id",
            re_constraints=None,
            weights=None,
            cov_re=None,
            scale=None,
            constraints=None,
            method="ml"  # Using ML for fixed effects comparison, REML for final fit
        )
        # Note: statsmodels lme_fixed_effects is experimental.
        # We use the standard mixedlm API for robustness in this context.
        raise NotImplementedError("Using standard MixedLM API below instead.")

    except Exception:
        # Fallback to standard MixedLM API which is more stable in statsmodels
        model = smf.mixedlm(formula, df, groups=df["participant_id"])
        try:
            result = model.fit(reml=False, maxiter=max_iter)
            # Check convergence
            if not result.converged:
                logger.warning("Model did not converge within max iterations.")
                # Try again with more iterations or different method if needed
                result = model.fit(reml=True, maxiter=max_iter * 2)
            return result, result.converged
        except Exception as e:
            logger.error(f"Model fitting failed: {e}")
            raise

def bootstrap_coefficient_ci(result, n_boot=1000, seed=42):
    """
    Calculate 95% confidence intervals for fixed effects coefficients via bootstrapping.
    """
    np.seed(seed)
    df = result.model.data.frame
    formula = result.model.formula
    groups = result.model.groups

    boot_coefs = []

    for _ in range(n_boot):
        # Resample participants (cluster bootstrap)
        unique_groups = df['participant_id'].unique()
        sampled_groups = np.random.choice(unique_groups, size=len(unique_groups), replace=True)
        sampled_df = df[df['participant_id'].isin(sampled_groups)]

        if len(sampled_df) < 10:
            continue

        try:
            boot_model = smf.mixedlm(formula, sampled_df, groups=sampled_df["participant_id"])
            boot_result = boot_model.fit(reml=False, maxiter=100)
            boot_coefs.append(boot_result.params)
        except Exception:
            continue

    if len(boot_coefs) > 0:
        boot_df = pd.DataFrame(boot_coefs)
        ci_lower = boot_df.quantile(0.025)
        ci_upper = boot_df.quantile(0.975)
        return ci_lower, ci_upper
    return None, None

def compare_with_anova(anova_results, mixed_results):
    """
    Compare the Condition effect from ANOVA and Mixed Effects Model.
    """
    anova_f = anova_results.get('F_statistic', None)
    anova_p = anova_results.get('p_value', None)
    
    # Extract Condition fixed effect
    mixed_coef = mixed_results.get('fixed_effects', {}).get('C(condition)[T.high_quality]', 0)
    mixed_p = mixed_results.get('fixed_effects_p', {}).get('C(condition)[T.high_quality]', 1.0)

    comparison = {
        "anova_f_stat": anova_f,
        "anova_p_value": anova_p,
        "mixed_effect_coef": mixed_coef,
        "mixed_effect_p_value": mixed_p,
        "effect_persistence": "Yes" if (mixed_p < 0.05) else "No",
        "notes": "Comparing main effect of condition across models."
    }
    return comparison

def main():
    parser = argparse.ArgumentParser(description="Run Mixed Effects Analysis for US3")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to cleaned wide-format CSV (default: data/raw/participants.csv)")
    parser.add_argument("--output", type=str, default=None,
                        help="Path to output JSON results (default: data/processed/mixed_effects_results.json)")
    parser.add_argument("--anova-input", type=str, default=None,
                        help="Path to ANOVA results JSON for comparison")
    args = parser.parse_args()

    # Resolve paths
    input_path = args.input if args.input else str(get_cleaned_data_path())
    output_path = args.output if args.output else str(get_output_path())
    anova_input = args.anova_input if args.anova_input else str(get_anova_results_path())

    # Ensure output directory exists
    os.makedirs(os.dirname(output_path), exist_ok=True)

    logger.info(f"Loading data from {input_path}...")
    df = load_wide_data_for_mixed(input_path)

    logger.info(f"Dataset shape: {df.shape}")
    logger.info(f"Unique participants: {df['participant_id'].nunique()}")
    logger.info(f"Conditions: {df['condition'].unique()}")

    # Define the model formula
    # Credibility ~ Condition + Age + Education + (1|Participant)
    formula = "credibility_mean ~ C(condition) + age + education"

    logger.info("Running Mixed Effects Model...")
    result, converged = run_mixed_effects_model_with_convergence(df, formula)

    if not converged:
        logger.warning("Model convergence warning: Results may be approximate.")

    # Extract results
    fixed_effects = result.params.to_dict()
    fixed_effects_p = result.pvalues.to_dict()
    random_effects = result.var_to_names
    aic = result.aic
    bic = result.bic
    log_likelihood = result.llf

    # Check residual normality
    residuals = result.resid
    is_normal = check_residual_normality(residuals)

    # Bootstrap CIs
    ci_lower, ci_upper = bootstrap_coefficient_ci(result, n_boot=500)

    # Load ANOVA results for comparison if available
    comparison = None
    if os.path.exists(anova_input):
        try:
            with open(anova_input, 'r') as f:
                anova_data = json.load(f)
            comparison = compare_with_anova(anova_data, {
                "fixed_effects": fixed_effects,
                "fixed_effects_p": fixed_effects_p
            })
        except Exception as e:
            logger.warning(f"Could not load ANOVA results for comparison: {e}")

    # Prepare output dictionary
    output_data = {
        "model_formula": formula,
        "convergence_status": converged,
        "sample_size": len(df),
        "num_groups": df['participant_id'].nunique(),
        "fit_statistics": {
            "AIC": aic,
            "BIC": bic,
            "Log-Likelihood": log_likelihood
        },
        "fixed_effects": fixed_effects,
        "fixed_effects_pvalues": fixed_effects_p,
        "random_effects_structure": random_effects,
        "residual_normality": {
            "is_normal": is_normal,
            "test": "Shapiro-Wilk"
        },
        "confidence_intervals": {
            "lower": ci_lower.to_dict() if ci_lower is not None else None,
            "upper": ci_upper.to_dict() if ci_upper is not None else None
        },
        "comparison_with_anova": comparison,
        "timestamp": str(pd.Timestamp.now())
    }

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)

    logger.info(f"Results written to {output_path}")
    logger.info("Mixed Effects Analysis Complete.")

    # Print summary to stdout for quick inspection
    print("\n--- Mixed Effects Model Summary ---")
    print(f"Formula: {formula}")
    print(f"Converged: {converged}")
    print(f"AIC: {aic:.2f}, BIC: {bic:.2f}")
    print("\nFixed Effects (Condition High Quality):")
    coef = fixed_effects.get('C(condition)[T.high_quality]', 'N/A')
    p_val = fixed_effects_p.get('C(condition)[T.high_quality]', 'N/A')
    print(f"  Coefficient: {coef}")
    print(f"  p-value: {p_val}")
    print("-----------------------------------\n")

if __name__ == "__main__":
    main()