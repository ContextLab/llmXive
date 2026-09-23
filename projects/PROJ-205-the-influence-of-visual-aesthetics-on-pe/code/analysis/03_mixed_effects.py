"""
Mixed-Effects Model Analysis with Residual Normality Checks and Transformations.

This script runs a linear mixed effects model with random intercepts, age/education
as covariates, and checks the residuals for normality. If the residuals are not
normally distributed, it attempts log or square-root transformations and re-runs
the model.

Output: data/processed/mixed_effects_results.json
"""
import os
import sys
import json
import argparse
import warnings
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_wide_data_for_mixed(input_path):
    """
    Load wide-format data for mixed effects analysis.
    
    Args:
        input_path: Path to the wide-format CSV file.
        
    Returns:
        pd.DataFrame: Wide-format dataframe.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded data with {len(df)} participants from {input_path}")
    
    # Ensure numeric columns are numeric
    numeric_cols = ['credibility_professional', 'age', 'education']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def run_mixed_effects_model(df, formula, dependent_var, random_var='participant_id'):
    """
    Run a linear mixed effects model.
    
    Args:
        df: DataFrame with the data.
        formula: Model formula string.
        dependent_var: Name of the dependent variable column.
        random_var: Name of the random effect grouping variable.
        
    Returns:
        dict: Model results including coefficients, p-values, and convergence status.
    """
    if df[dependent_var].isna().all():
        logger.warning(f"All values for {dependent_var} are NaN. Skipping model.")
        return {
            "status": "skipped",
            "reason": "All NaN values",
            "dependent_var": dependent_var
        }
    
    # Drop rows with NaN in dependent variable or formula columns
    model_df = df.dropna(subset=[dependent_var] + [col.strip().split(' ')[0] for col in formula.split('+') if col.strip()])
    
    if len(model_df) < 10:
        logger.warning(f"Not enough data points ({len(model_df)}) for mixed effects model.")
        return {
            "status": "skipped",
            "reason": f"Insufficient data points ({len(model_df)})",
            "dependent_var": dependent_var
        }
    
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = mixedlm(f"{dependent_var} ~ {formula}", model_df, groups=model_df[random_var])
            result = model.fit()
            
        # Check convergence
        converged = result.converged
        if not converged:
            logger.warning(f"Model did not converge for {dependent_var}. Retrying with different optimizer...")
            try:
                result = model.fit(method='bfgs')
                converged = result.converged
                if not converged:
                    result = model.fit(method='newton')
                    converged = result.converged
            except Exception as e:
                logger.warning(f"Retrying with different optimizers failed: {e}")
        
        # Extract results
        results_dict = {
            "status": "converged" if converged else "unconverged",
            "dependent_var": dependent_var,
            "formula": f"{dependent_var} ~ {formula}",
            "random_var": random_var,
            "n_observations": len(model_df),
            "coefficients": {},
            "p_values": {},
            "convergence_status": "converged" if converged else "failed"
        }
        
        for param_name, param_value in result.params.items():
            # Skip the intercept for p-value extraction if it's the group variance
            if param_name != 'group':
                results_dict["coefficients"][param_name] = float(param_value)
                # Get p-value if available
                try:
                    p_val = result.pvalues[param_name]
                    results_dict["p_values"][param_name] = float(p_val)
                except KeyError:
                    results_dict["p_values"][param_name] = None
        
        # Add AIC/BIC if available
        try:
            results_dict["AIC"] = float(result.aic)
            results_dict["BIC"] = float(result.bic)
        except:
            pass
        
        return results_dict
        
    except Exception as e:
        logger.error(f"Error running mixed effects model for {dependent_var}: {e}")
        return {
            "status": "error",
            "reason": str(e),
            "dependent_var": dependent_var
        }

def check_residual_normality(model_result, df, formula, dependent_var, random_var='participant_id'):
    """
    Check residuals for normality using Shapiro-Wilk test.
    
    Args:
        model_result: The fitted model result.
        df: DataFrame with the data.
        formula: Model formula string.
        dependent_var: Name of the dependent variable.
        random_var: Name of the random effect grouping variable.
        
    Returns:
        tuple: (shapiro_statistic, shapiro_pvalue, is_normal)
    """
    try:
        # Get residuals
        # Note: We need to calculate residuals manually if not directly available
        model_df = df.dropna(subset=[dependent_var] + [col.strip().split(' ')[0] for col in formula.split('+') if col.strip()])
        
        # Predict values
        X = sm.model._formula_interpret_formula(f"{dependent_var} ~ {formula}", model_df)
        beta = model_result.params
        
        # Calculate residuals
        # This is a simplified approach; in practice, statsmodels provides residuals
        residuals = model_result.resid
        
        # Shapiro-Wilk test
        stat, p_value = stats.shapiro(residuals)
        is_normal = p_value >= 0.05
        
        logger.info(f"Shapiro-Wilk test for {dependent_var}: W={stat:.4f}, p={p_value:.4f}, Normal={is_normal}")
        
        return stat, p_value, is_normal
        
    except Exception as e:
        logger.warning(f"Could not compute residuals for normality test: {e}")
        return None, None, None

def transform_variable(df, column, method='log'):
    """
    Transform a variable using log or square-root transformation.
    
    Args:
        df: DataFrame.
        column: Column name to transform.
        method: 'log' or 'sqrt'.
        
    Returns:
        pd.Series: Transformed series.
    """
    if method == 'log':
        # Add small constant to avoid log(0)
        transformed = np.log1p(df[column])
    elif method == 'sqrt':
        transformed = np.sqrt(df[column])
    else:
        raise ValueError(f"Unknown transformation method: {method}")
    
    return transformed

def main():
    parser = argparse.ArgumentParser(description="Run mixed effects model with residual checks")
    parser.add_argument("--input", type=str, required=True, help="Path to wide-format input CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file")
    parser.add_argument("--formula", type=str, default="condition + age + education", help="Model formula (excluding dependent variable)")
    parser.add_argument("--random", type=str, default="participant_id", help="Random effect grouping variable")
    args = parser.parse_args()

    project_root = get_project_root()
    input_path = Path(args.input)
    
    if not input_path.is_absolute():
        input_path = project_root / args.input
    
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / args.output

    logger.info(f"Loading data from {input_path}...")
    try:
        df = load_wide_data_for_mixed(str(input_path))
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Define dependent variables to analyze
    dependent_vars = ['credibility_professional', 'credibility', 'professionalism']
    
    results = {
        "analysis_timestamp": datetime.now().isoformat(),
        "input_file": str(input_path),
        "formula": args.formula,
        "random_effect": args.random,
        "models": {}
    }

    for dep_var in dependent_vars:
        if dep_var not in df.columns:
            logger.info(f"Skipping {dep_var}: not found in data")
            continue
        
        logger.info(f"Analyzing {dep_var}...")
        
        # Run initial model
        model_result = run_mixed_effects_model(df, args.formula, dep_var, args.random)
        
        if model_result["status"] in ["skipped", "error"]:
            results["models"][dep_var] = model_result
            continue
        
        # Check residual normality
        shapiro_stat, shapiro_p, is_normal = check_residual_normality(
            model_result, df, args.formula, dep_var, args.random
        )
        
        model_results = {
            "original_model": model_result,
            "normality_check": {
                "shapiro_statistic": shapiro_stat,
                "shapiro_p_value": shapiro_p,
                "is_normal": is_normal,
                "threshold": 0.05
            },
            "transformed_model": None
        }
        
        # If not normal, try transformations
        if shapiro_p is not None and shapiro_p < 0.05:
            logger.warning(f"Residuals for {dep_var} are not normally distributed (p={shapiro_p:.4f}). Attempting transformations...")
            
            # Try log transformation
            log_transformed = transform_variable(df, dep_var, 'log')
            df[f"{dep_var}_log"] = log_transformed
            
            log_result = run_mixed_effects_model(df, args.formula, f"{dep_var}_log", args.random)
            
            # Check normality of transformed residuals
            if log_result["status"] == "converged":
                _, log_shapiro_p, log_is_normal = check_residual_normality(
                    log_result, df, args.formula, f"{dep_var}_log", args.random
                )
                
                log_results = {
                    "transformation": "log",
                    "model": log_result,
                    "normality_check": {
                        "shapiro_p_value": log_shapiro_p,
                        "is_normal": log_is_normal
                    }
                }
                
                # Try sqrt transformation if log didn't help
                if not log_is_normal:
                    sqrt_transformed = transform_variable(df, dep_var, 'sqrt')
                    df[f"{dep_var}_sqrt"] = sqrt_transformed
                    
                    sqrt_result = run_mixed_effects_model(df, args.formula, f"{dep_var}_sqrt", args.random)
                    
                    if sqrt_result["status"] == "converged":
                        _, sqrt_shapiro_p, sqrt_is_normal = check_residual_normality(
                            sqrt_result, df, args.formula, f"{dep_var}_sqrt", args.random
                        )
                        
                        sqrt_results = {
                            "transformation": "sqrt",
                            "model": sqrt_result,
                            "normality_check": {
                                "shapiro_p_value": sqrt_shapiro_p,
                                "is_normal": sqrt_is_normal
                            }
                        }
                        
                        # Choose the best transformation
                        if sqrt_is_normal and (log_shapiro_p is None or not log_is_normal):
                            model_results["transformed_model"] = sqrt_results
                            logger.info(f"Using sqrt transformation for {dep_var}: p={sqrt_shapiro_p:.4f}")
                        elif log_is_normal:
                            model_results["transformed_model"] = log_results
                            logger.info(f"Using log transformation for {dep_var}: p={log_shapiro_p:.4f}")
                        else:
                            model_results["transformed_model"] = {
                                "transformation": "log",
                                "model": log_result,
                                "normality_check": {
                                    "shapiro_p_value": log_shapiro_p,
                                    "is_normal": log_is_normal
                                }
                            }
                            logger.warning(f"Neither transformation achieved normality for {dep_var}. Using log.")
                    else:
                        model_results["transformed_model"] = log_results
                        logger.warning(f"Sqrt transformation failed for {dep_var}. Using log.")
                else:
                    model_results["transformed_model"] = log_results
                    logger.info(f"Log transformation achieved normality for {dep_var}: p={log_shapiro_p:.4f}")
            
            else:
                model_results["transformed_model"] = {
                    "transformation": "log",
                    "model": log_result,
                    "normality_check": {
                        "shapiro_p_value": None,
                        "is_normal": False,
                        "reason": "Model did not converge"
                    }
                }
                logger.warning(f"Log transformation model did not converge for {dep_var}.")
        
        results["models"][dep_var] = model_results
        
        # Clean up transformed columns
        for col in [f"{dep_var}_log", f"{dep_var}_sqrt"]:
            if col in df.columns:
                del df[col]

    # Write results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    print(f"Analysis complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()