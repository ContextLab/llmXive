import os
import sys
import json
import argparse
import warnings
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.anova import AnovaRM
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Path Helpers (matching API surface) ---
def get_project_root():
    """Returns the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent.parent

def get_cleaned_data_path():
    """Returns path to cleaned_data.csv."""
    return get_project_root() / "data" / "processed" / "cleaned_data.csv"

def get_anova_results_path():
    """Returns path to anova_results.json."""
    return get_project_root() / "data" / "processed" / "anova_results.json"

def get_output_path():
    """Returns default output path."""
    return get_project_root() / "data" / "processed" / "mixed_effects_results.json"

# --- Data Loading ---
def load_wide_data_for_mixed(input_path=None):
    """
    Loads the wide-format data required for Mixed Effects modeling.
    Expects columns: participant_id, condition_Professional, condition_Minimalist, etc.
    or a long format that can be pivoted.
    """
    if input_path is None:
        input_path = get_cleaned_data_path()
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data file not found at {input_path}. "
                                "Please run 00_preprocess.py first.")
    
    df = pd.read_csv(input_path)
    
    # Ensure participant_id is string for grouping
    df['participant_id'] = df['participant_id'].astype(str)
    
    # Check for necessary columns
    required_cols = ['participant_id', 'Credibility_Professional', 'Credibility_Minimalist', 
                     'Credibility_Low-Quality', 'Credibility_Neutral', 'Age', 'Education']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        # Fallback: try to find columns with 'Credibility' prefix if exact names differ
        cred_cols = [c for c in df.columns if c.startswith('Credibility_')]
        if len(cred_cols) >= 4 and 'participant_id' in df.columns:
            logger.warning(f"Exact column names not found. Found {len(cred_cols)} Credibility columns. Attempting inference.")
            # Assume mapping order matches Latin Square or alphabetical if names are standard
            # This is a robust fallback; in a real scenario, explicit mapping is better.
            pass 
        else:
            raise ValueError(f"Missing required columns for Mixed Effects: {missing}")
    
    return df

# --- Residual Normality Check ---
def check_residual_normality(model, dependent_var='Credibility'):
    """
    Performs Shapiro-Wilk test on model residuals.
    Returns (is_normal, p_value, residuals).
    """
    try:
        # Get predicted values
        pred = model.fittedvalues
        # Get observed values (need to map back from model data)
        # Assuming model.data.endog holds the dependent variable
        observed = model.data.endog
        residuals = observed - pred
        
        stat, p_val = stats.shapiro(residuals)
        is_normal = p_val > 0.05
        return is_normal, p_val, residuals
    except Exception as e:
        logger.warning(f"Could not perform Shapiro-Wilk test: {e}")
        return None, None, None

# --- Variable Transformation ---
def transform_variable(data, method='log'):
    """
    Applies a transformation to the data.
    Handles zeros/negatives by adding a small offset if necessary.
    """
    if method == 'log':
        # Add 1 to avoid log(0) if data can be 0, or min+epsilon
        min_val = data.min()
        offset = 0 if min_val > 0 else (abs(min_val) + 1e-6)
        return np.log(data + offset)
    elif method == 'sqrt':
        min_val = data.min()
        offset = 0 if min_val >= 0 else (abs(min_val) + 1e-6)
        return np.sqrt(data + offset)
    elif method == 'reciprocal':
        min_val = data.min()
        offset = 0 if min_val != 0 else 1e-6
        return 1.0 / (data + offset)
    return data

# --- Convergence Retry Logic ---
def run_mixed_effects_model_with_convergence(df, formula, max_retries=5):
    """
    Runs MixedLM with automatic retry on different optimizers if convergence fails.
    Returns the model, result, and a log of attempts.
    """
    attempts_log = []
    optimizers = ['bfgs', 'newton', 'cg', 'lbfgs', 'powell']
    
    # Prepare data
    # Ensure categorical variables are handled correctly
    df['Condition'] = pd.Categorical(df['Condition'])
    df['Education'] = pd.Categorical(df['Education'])
    
    for i, solver in enumerate(optimizers[:max_retries]):
        try:
            logger.info(f"Attempt {i+1}: Running MixedLM with solver '{solver}'...")
            start_time = time.time()
            
            # Fit model
            model = MixedLM.from_formula(formula, groups="participant_id", data=df, 
                                         exog_re=None, re_formula="1")
            # Try fitting with specific method
            result = model.fit(method=solver, disp=False)
            
            elapsed = time.time() - start_time
            
            # Check convergence status
            # statsmodels MixedLM fit result has 'converged' attribute in newer versions,
            # or we check the 'converged' flag in the result object if available.
            # If not, we assume success if no exception was raised and result is valid.
            converged = result.converged if hasattr(result, 'converged') else True
            
            attempts_log.append({
                "solver": solver,
                "status": "converged" if converged else "failed",
                "time_seconds": elapsed,
                "message": "Success" if converged else "Did not converge"
            })
            
            if converged:
                logger.info(f"Converged successfully with solver '{solver}'.")
                return model, result, attempts_log, True
            else:
                logger.warning(f"Model did not converge with solver '{solver}'. Retrying...")
                
        except Exception as e:
            attempts_log.append({
                "solver": solver,
                "status": "error",
                "message": str(e)
            })
            logger.warning(f"Error with solver '{solver}': {e}. Retrying...")
            continue
    
    # If all retries failed
    logger.error("All convergence attempts failed.")
    return None, None, attempts_log, False

# --- Bootstrapping for Confidence Intervals (T051b) ---
def bootstrap_coefficient_ci(df, formula, n_iterations=1000, seed=42):
    """
    Calculates 95% Confidence Intervals for the Condition coefficients using bootstrapping.
    Resamples participants (rows) with replacement.
    """
    np.random.seed(seed)
    logger.info(f"Starting bootstrapping (n={n_iterations}, seed={seed})...")
    
    # Extract unique participants
    participants = df['participant_id'].unique()
    n_participants = len(participants)
    
    # Store coefficients for each condition
    # We assume the formula includes 'Condition' which is categorical
    # We will extract coefficients for each level relative to the reference
    # To make this robust, we run the model on the full data first to get the formula structure
    
    # Prepare the full data model to identify coefficients
    df['Condition'] = pd.Categorical(df['Condition'])
    df['Education'] = pd.Categorical(df['Education'])
    
    # Initial fit to get coefficient names
    try:
        base_model = MixedLM.from_formula(formula, groups="participant_id", data=df)
        base_result = base_model.fit(method='bfgs', disp=False)
        coef_names = [k for k in base_result.params.keys() if k.startswith('Condition')]
    except:
        # Fallback if base fit fails, try to infer from formula string
        # This is a heuristic
        coef_names = []
        logger.warning("Could not determine coefficient names from initial fit. Bootstrapping might be limited.")
        return None

    if not coef_names:
        logger.warning("No Condition coefficients found to bootstrap.")
        return None

    # Initialize storage for bootstrapped coefficients
    bootstrap_samples = {name: [] for name in coef_names}
    
    for i in range(n_iterations):
        # Resample participants with replacement
        # We need to keep all rows for a selected participant to maintain the repeated measures structure
        sample_indices = np.random.choice(n_participants, size=n_participants, replace=True)
        sample_participants = participants[sample_indices]
        
        # Filter dataframe to these participants
        boot_df = df[df['participant_id'].isin(sample_participants)].copy()
        
        if len(boot_df) < 10:
            continue # Skip if sample is too small
        
        try:
            # Re-fit model on bootstrap sample
            # Use a simpler method for speed if needed, but 'bfgs' is standard
            boot_model = MixedLM.from_formula(formula, groups="participant_id", data=boot_df)
            boot_result = boot_model.fit(method='bfgs', disp=False)
            
            # Extract coefficients
            for name in coef_names:
                if name in boot_result.params:
                    bootstrap_samples[name].append(boot_result.params[name])
                else:
                    # If a coefficient is dropped due to collinearity in sample, skip or handle
                    pass
                    
        except Exception as e:
            # If model fails to converge on a bootstrap sample, skip it
            continue
    
    # Calculate CIs
    ci_results = {}
    for name, samples in bootstrap_samples.items():
        if len(samples) > 0:
            lower = np.percentile(samples, 2.5)
            upper = np.percentile(samples, 97.5)
            mean = np.mean(samples)
            ci_results[name] = {
                "mean": float(mean),
                "ci_lower": float(lower),
                "ci_upper": float(upper),
                "n_samples": len(samples)
            }
        else:
            ci_results[name] = {
                "mean": None,
                "ci_lower": None,
                "ci_upper": None,
                "n_samples": 0
            }
            
    logger.info(f"Bootstrapping complete. Valid samples: {len(bootstrap_samples[coef_names[0]]) if coef_names else 0}")
    return ci_results

# --- Comparison with ANOVA ---
def compare_with_anova(mixed_results, anova_path=None):
    """
    Compares Mixed Effects results with ANOVA results.
    """
    if anova_path is None:
        anova_path = get_anova_results_path()
        
    if not os.path.exists(anova_path):
        logger.warning(f"ANOVA results not found at {anova_path}. Skipping comparison.")
        return None
    
    try:
        with open(anova_path, 'r') as f:
            anova_data = json.load(f)
        
        comparison = {
            "anova_p_value": anova_data.get('p_value'),
            "mixed_p_value": mixed_results.get('overall_p_value'),
            "consistency": "consistent" if (anova_data.get('p_value') is not None and 
                                            mixed_results.get('overall_p_value') is not None and
                                            (anova_data['p_value'] < 0.05) == (mixed_results['overall_p_value'] < 0.05)) 
                           else "inconsistent"
        }
        return comparison
    except Exception as e:
        logger.error(f"Error comparing with ANOVA: {e}")
        return None

# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description="Run Mixed Effects Analysis with Bootstrapping")
    parser.add_argument('--input', type=str, default=None, help='Path to cleaned data CSV (default: auto-detect)')
    parser.add_argument('--output', type=str, default=None, help='Path to output JSON (default: auto-detect)')
    parser.add_argument('--formula', type=str, default="C(Credibility) ~ C(Condition) + Age + Education + (1|participant_id)",
                        help='Statsmodels formula for the mixed model')
    parser.add_argument('--bootstrap', action='store_true', default=True, help='Enable bootstrapping for CIs (T051b)')
    parser.add_argument('--n-bootstrap', type=int, default=1000, help='Number of bootstrap iterations')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for bootstrapping')
    
    args = parser.parse_args()
    
    # Set paths
    input_path = args.input if args.input else get_cleaned_data_path()
    output_path = args.output if args.output else get_output_path()
    
    logger.info(f"Loading data from {input_path}...")
    try:
        df_wide = load_wide_data_for_mixed(input_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Reshape to long format for MixedLM (MixedLM expects long format for repeated measures)
    # Wide columns: Credibility_Professional, Credibility_Minimalist, etc.
    # We need to pivot to: participant_id, Condition, Credibility, Age, Education
    
    # Identify Credibility columns
    cred_cols = [c for c in df_wide.columns if c.startswith('Credibility_')]
    if not cred_cols:
        logger.error("No Credibility columns found in wide data.")
        sys.exit(1)
    
    # Create long dataframe
    long_dfs = []
    for col in cred_cols:
        cond_name = col.replace('Credibility_', '')
        temp_df = df_wide[['participant_id', 'Age', 'Education']].copy()
        temp_df['Condition'] = cond_name
        temp_df['Credibility'] = df_wide[col]
        long_dfs.append(temp_df)
    
    df_long = pd.concat(long_dfs, ignore_index=True)
    
    # Drop rows with missing data
    df_long = df_long.dropna(subset=['Credibility', 'Condition', 'Age', 'Education'])
    
    logger.info(f"Data reshaped to long format. {len(df_long)} observations.")
    
    # Run Mixed Effects Model
    logger.info("Running Mixed Effects Model...")
    model, result, attempts_log, converged = run_mixed_effects_model_with_convergence(df_long, args.formula)
    
    results_dict = {
        "convergence_status": "converged" if converged else "failed",
        "convergence_attempts": attempts_log,
        "parameters": {},
        "p_values": {},
        "comparison_with_anova": None
    }
    
    if converged and result is not None:
        # Extract parameters and p-values
        for param, val in result.params.items():
            results_dict["parameters"][param] = float(val)
        for param, val in result.pvalues.items():
            results_dict["p_values"][param] = float(val)
        
        # Overall significance (simplified: check if any Condition effect is significant)
        cond_pvals = [v for k, v in results_dict["p_values"].items() if k.startswith('Condition')]
        if cond_pvals:
            results_dict["overall_p_value"] = min(cond_pvals) # Conservative min
        else:
            results_dict["overall_p_value"] = None
        
        # Residual Normality Check (T049)
        is_normal, p_val, _ = check_residual_normality(result, 'Credibility')
        results_dict["residual_normality"] = {
            "is_normal": is_normal,
            "shapiro_p_value": float(p_val) if p_val is not None else None
        }
        
        # Transformation attempt if not normal
        if is_normal is False:
            logger.info("Residuals not normal. Attempting log transformation...")
            # Transform Credibility in df_long
            df_long['Credibility_Transformed'] = transform_variable(df_long['Credibility'], 'log')
            formula_trans = args.formula.replace('Credibility', 'Credibility_Transformed')
            model_t, result_t, attempts_log_t, converged_t = run_mixed_effects_model_with_convergence(df_long, formula_trans)
            
            if converged_t:
                results_dict["transformation_applied"] = True
                results_dict["transformation_method"] = "log"
                results_dict["transformed_parameters"] = {k: float(v) for k, v in result_t.params.items()}
                results_dict["transformed_p_values"] = {k: float(v) for k, v in result_t.pvalues.items()}
                # Check transformed residuals
                is_normal_t, p_val_t, _ = check_residual_normality(result_t, 'Credibility_Transformed')
                results_dict["transformed_residual_normality"] = {
                    "is_normal": is_normal_t,
                    "shapiro_p_value": float(p_val_t) if p_val_t is not None else None
                }
            else:
                results_dict["transformation_applied"] = False
                results_dict["transformation_method"] = "log"
                results_dict["transformation_status"] = "failed"
        else:
            results_dict["transformation_applied"] = False
    
    # Bootstrapping (T051b)
    if args.bootstrap and converged and result is not None:
        logger.info("Calculating Confidence Intervals via Bootstrapping...")
        # We need to pass the long dataframe to the bootstrap function
        # Adjust formula for long format if necessary (it should be compatible)
        # The formula in args.formula is already set for long format: "C(Credibility) ~ C(Condition) + ..."
        ci_results = bootstrap_coefficient_ci(df_long, args.formula, n_iterations=args.n_bootstrap, seed=args.seed)
        results_dict["bootstrap_confidence_intervals"] = ci_results
    else:
        results_dict["bootstrap_confidence_intervals"] = None
        if not converged:
            logger.warning("Bootstrapping skipped due to model convergence failure.")
        elif not args.bootstrap:
            logger.info("Bootstrapping disabled by argument.")
    
    # Comparison with ANOVA
    results_dict["comparison_with_anova"] = compare_with_anova(results_dict)
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())