import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import warnings

# Suppress specific convergence warnings for cleaner output, we handle them explicitly
warnings.filterwarnings('ignore', category=FutureWarning, module='statsmodels')
warnings.filterwarnings('ignore', category=UserWarning, module='statsmodels')

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
except ImportError:
    print("Error: statsmodels is required. Install with: pip install statsmodels")
    sys.exit(1)

def get_project_root():
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    return project_root

def load_wide_data_for_mixed(input_path):
    """
    Load wide-format data for mixed effects analysis.
    Expects columns: participant_id, credibility_professional, condition, age, education
    or similar wide format where conditions are columns.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Basic validation
    required_cols = ['participant_id']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input file missing required columns: {required_cols}")

    return df

def run_mixed_effects_model(df, formula, dependent_var, output_path):
    """
    Run a linear mixed effects model with normality checks and transformations.

    Args:
        df: DataFrame with the data
        formula: String formula for the model (e.g., "Credibility ~ Condition + (1|ParticipantID)")
        dependent_var: Name of the dependent variable column
        output_path: Path to save the JSON results
    """
    results = {
        "model_type": "Linear Mixed Effects",
        "formula": formula,
        "dependent_variable": dependent_var,
        "original_model": {},
        "transformation_applied": False,
        "transformed_model": None,
        "normality_test": {}
    }

    # 1. Extract residuals from the original model
    try:
        # Fit the original model
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            model = smf.mixedlm(formula, df, groups=df["participant_id"])
            result = model.fit(reml=True)

            # Check convergence
            converged = result.converged
            if not converged:
                results["original_model"]["convergence_status"] = "failed"
                # Try different optimizers if failed
                for optimizer in ['bfgs', 'newton', 'nm', 'powell']:
                    try:
                        result_retry = model.fit(reml=True, method=optimizer)
                        if result_retry.converged:
                            result = result_retry
                            converged = True
                            results["original_model"]["convergence_status"] = f"converged_after_retry_{optimizer}"
                            break
                    except Exception:
                        continue

            if not converged:
                results["original_model"]["convergence_status"] = "failed_all_retries"

        # Get residuals
        residuals = result.resid

        # 2. Shapiro-Wilk Test for Normality
        shapiro_stat, shapiro_p = stats.shapiro(residuals)
        results["normality_test"] = {
            "test": "Shapiro-Wilk",
            "statistic": float(shapiro_stat),
            "p_value": float(shapiro_p),
            "is_normal": bool(shapiro_p >= 0.05)
        }

        # Store original model results
        results["original_model"]["convergence_status"] = "converged" if converged else results["original_model"].get("convergence_status", "unknown")
        results["original_model"]["log_likelihood"] = float(result.llf)
        results["original_model"]["aic"] = float(result.aic)
        results["original_model"]["bic"] = float(result.bic)

        # Extract fixed effects
        fixed_effects = {}
        for name, param in result.params.items():
            fixed_effects[name] = {
                "estimate": float(param),
                "std_err": float(result.bse[name]) if name in result.bse else None,
                "z_value": float(result.tvalues[name]) if name in result.tvalues else None,
                "p_value": float(result.pvalues[name]) if name in result.pvalues else None
            }
        results["original_model"]["fixed_effects"] = fixed_effects

        # Check if transformation is needed
        if shapiro_p < 0.05:
            results["transformation_applied"] = True
            transformed_df = df.copy()
            transformed_var_name = f"{dependent_var}_log"

            # Attempt Log transformation (add small epsilon to avoid log(0))
            try:
                min_val = transformed_df[dependent_var].min()
                epsilon = 1.0 if min_val <= 0 else 0.0
                transformed_df[transformed_var_name] = np.log(transformed_df[dependent_var] + epsilon)
                
                # Update formula for transformed variable
                transformed_formula = formula.replace(dependent_var, transformed_var_name)
                
                # Fit transformed model
                with warnings.catch_warnings(record=True):
                    warnings.simplefilter("always")
                    transformed_model = smf.mixedlm(transformed_formula, transformed_df, groups=transformed_df["participant_id"])
                    transformed_result = transformed_model.fit(reml=True)
                
                # Check convergence for transformed
                if not transformed_result.converged:
                    for optimizer in ['bfgs', 'newton']:
                        try:
                            t_res = transformed_model.fit(reml=True, method=optimizer)
                            if t_res.converged:
                                transformed_result = t_res
                                break
                        except Exception:
                            continue

                # Residual check for transformed
                trans_residuals = transformed_result.resid
                trans_shapiro_stat, trans_shapiro_p = stats.shapiro(trans_residuals)
                
                trans_fixed_effects = {}
                for name, param in transformed_result.params.items():
                    trans_fixed_effects[name] = {
                        "estimate": float(param),
                        "std_err": float(transformed_result.bse[name]) if name in transformed_result.bse else None,
                        "z_value": float(transformed_result.tvalues[name]) if name in transformed_result.tvalues else None,
                        "p_value": float(transformed_result.pvalues[name]) if name in transformed_result.pvalues else None
                    }

                results["transformed_model"] = {
                    "transformation": "log",
                    "variable": transformed_var_name,
                    "convergence_status": "converged" if transformed_result.converged else "failed",
                    "log_likelihood": float(transformed_result.llf),
                    "aic": float(transformed_result.aic),
                    "bic": float(transformed_result.bic),
                    "normality_test": {
                        "test": "Shapiro-Wilk",
                        "statistic": float(trans_shapiro_stat),
                        "p_value": float(trans_shapiro_p),
                        "is_normal": bool(trans_shapiro_p >= 0.05)
                    },
                    "fixed_effects": trans_fixed_effects
                }

            except Exception as e:
                results["transformation_error"] = f"Log transformation failed: {str(e)}"
                # Try square root as fallback
                try:
                    transformed_df[transformed_var_name] = np.sqrt(transformed_df[dependent_var] + 1) # +1 to avoid 0 issues
                    transformed_formula = formula.replace(dependent_var, transformed_var_name)
                    
                    with warnings.catch_warnings(record=True):
                        warnings.simplefilter("always")
                        transformed_model = smf.mixedlm(transformed_formula, transformed_df, groups=transformed_df["participant_id"])
                        transformed_result = transformed_model.fit(reml=True)
                    
                    if not transformed_result.converged:
                        for optimizer in ['bfgs', 'newton']:
                            try:
                                t_res = transformed_model.fit(reml=True, method=optimizer)
                                if t_res.converged:
                                    transformed_result = t_res
                                    break
                            except Exception:
                                continue
                    
                    trans_residuals = transformed_result.resid
                    trans_shapiro_stat, trans_shapiro_p = stats.shapiro(trans_residuals)
                    
                    trans_fixed_effects = {}
                    for name, param in transformed_result.params.items():
                        trans_fixed_effects[name] = {
                            "estimate": float(param),
                            "std_err": float(transformed_result.bse[name]) if name in transformed_result.bse else None,
                            "z_value": float(transformed_result.tvalues[name]) if name in transformed_result.tvalues else None,
                            "p_value": float(transformed_result.pvalues[name]) if name in transformed_result.pvalues else None
                        }

                    results["transformed_model"] = {
                        "transformation": "square_root",
                        "variable": transformed_var_name,
                        "convergence_status": "converged" if transformed_result.converged else "failed",
                        "log_likelihood": float(transformed_result.llf),
                        "aic": float(transformed_result.aic),
                        "bic": float(transformed_result.bic),
                        "normality_test": {
                            "test": "Shapiro-Wilk",
                            "statistic": float(trans_shapiro_stat),
                            "p_value": float(trans_shapiro_p),
                            "is_normal": bool(trans_shapiro_p >= 0.05)
                        },
                        "fixed_effects": trans_fixed_effects
                    }
                except Exception as e2:
                    results["transformation_error"] = f"Both log and sqrt transformations failed: {str(e2)}"

    except Exception as e:
        results["error"] = str(e)
        results["original_model"]["status"] = "failed"

    # Write results to JSON
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Mixed effects analysis complete. Results saved to: {output_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Run Mixed Effects Model with Normality Checks")
    parser.add_argument("--input", type=str, required=True, help="Path to input wide-format CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON results")
    parser.add_argument("--formula", type=str, default="Credibility ~ Condition + (1|participant_id)",
                        help="Model formula (default: Credibility ~ Condition + (1|participant_id))")
    parser.add_argument("--dependent-var", type=str, default="Credibility",
                        help="Name of dependent variable column (default: Credibility)")
    
    args = parser.parse_args()

    project_root = get_project_root()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = project_root / args.input
    
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / args.output

    print(f"Loading data from {input_path}...")
    try:
        df = load_wide_data_for_mixed(str(input_path))
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Running Mixed Effects Model...")
    print(f"Formula: {args.formula}")
    print(f"Dependent Variable: {args.dependent_var}")
    
    results = run_mixed_effects_model(df, args.formula, args.dependent_var, str(output_path))
    
    if "error" in results:
        print(f"Model execution failed: {results['error']}")
        sys.exit(1)
        
    print("Analysis completed successfully.")

if __name__ == "__main__":
    main()