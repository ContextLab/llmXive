import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# Attempt to import statsmodels for panel models
# We will use a try/except block to handle environments where it might not be fully installed,
# though requirements.txt specifies it.
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from linearmodels.panel import PanelOLS, RandomEffects, HausmanTest
    HAS_LINEARMODELS = True
except ImportError:
    HAS_LINEARMODELS = False
    logging.warning("linearmodels package not found. Random Effects and Hausman tests will be unavailable.")

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def detect_time_invariant_countries(df: pd.DataFrame, country_col: str = 'country_code', time_col: str = 'year', target_col: str = 'regime_type') -> List[str]:
    """
    Detect countries where the target variable (regime_type) is constant over time.
    
    Args:
        df: Input dataframe
        country_col: Name of the country code column
        time_col: Name of the year column
        target_col: Name of the variable to check for time-invariance
        
    Returns:
        List of country codes that are time-invariant for the target variable.
    """
    if not HAS_LINEARMODELS:
        logger.error("Cannot detect time-invariant countries: linearmodels not installed.")
        return []

    logger.info(f"Detecting time-invariant countries for variable '{target_col}'...")
    
    # Group by country and check variance of the target variable
    # If variance is 0 (or NaN due to single row), it's time-invariant
    country_stats = df.groupby(country_col)[target_col].agg(['var', 'count'])
    time_invariant = country_stats[country_stats['var'] == 0.0].index.tolist()
    
    # Also handle cases where a country might have only 1 row (var is NaN)
    single_row_countries = country_stats[country_stats['count'] == 1].index.tolist()
    time_invariant = list(set(time_invariant + single_row_countries))
    
    logger.info(f"Found {len(time_invariant)} time-invariant countries: {time_invariant}")
    return time_invariant

def save_time_invariant_report(flagged_countries: List[str], output_path: Path) -> None:
    """Save the list of time-invariant countries to a JSON file."""
    report = {
        "time_invariant_countries": flagged_countries,
        "count": len(flagged_countries)
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Time-invariant report saved to {output_path}")

def filter_time_invariant_countries(df: pd.DataFrame, flagged_countries: List[str], country_col: str = 'country_code') -> pd.DataFrame:
    """
    Filter the dataframe to exclude time-invariant countries.
    
    Args:
        df: Input dataframe
        flagged_countries: List of country codes to exclude
        country_col: Name of the country code column
        
    Returns:
        Filtered dataframe
    """
    if not flagged_countries:
        return df
    
    logger.info(f"Filtering out {len(flagged_countries)} time-invariant countries.")
    filtered_df = df[~df[country_col].isin(flagged_countries)]
    logger.info(f"Original rows: {len(df)}, Filtered rows: {len(filtered_df)}")
    return filtered_df

def run_fixed_effects_regression(df: pd.DataFrame, 
                                 target_col: str = 'land_use_change',
                                 main_exog: str = 'regime_type',
                                 controls: Optional[List[str]] = None,
                                 country_col: str = 'country_code',
                                 time_col: str = 'year') -> Dict[str, Any]:
    """
    Run a Fixed Effects panel regression.
    
    Model: target ~ main_exog + controls + Entity Effects
    """
    if not HAS_LINEARMODELS:
        raise ImportError("linearmodels package is required for Fixed Effects regression.")

    logger.info("Running Fixed Effects Panel Regression...")
    
    if controls is None:
        controls = []
    
    # Construct formula
    # We need to ensure all variables are present
    required_vars = [target_col, main_exog] + controls + [country_col, time_col]
    missing = [v for v in required_vars if v not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for regression: {missing}")
    
    formula = f"{target_col} ~ {main_exog}"
    if controls:
        formula += " + " + " + ".join(controls)
    
    # Prepare data for statsmodels/linearmodels
    # linearmodels expects a MultiIndex (Entity, Time)
    df_reindexed = df.set_index([country_col, time_col])
    
    # Run the model
    model = PanelOLS.from_formula(formula, df_reindexed, entity_effects=True, time_effects=False)
    result = model.fit(cov_type='robust', debiased=True)
    
    logger.info(f"Regression R-squared (Within): {result.rsquared_within:.4f}")
    logger.info(f"Main coefficient ({main_exog}): {result.params[main_exog]:.4f} (p={result.pvalues[main_exog]:.4f})")
    
    # Extract key results
    results_dict = {
        "model_type": "Fixed Effects",
        "rsquared_within": float(result.rsquared_within),
        "rsquared_overall": float(result.rsquared_overall),
        "nobs": int(result.nobs),
        "coefficients": {k: float(v) for k, v in result.params.items()},
        "p_values": {k: float(v) for k, v in result.pvalues.items()},
        "standard_errors": {k: float(v) for k, v in result.std_err.items()},
        "f_statistic": float(result.f_statistic),
        "f_p_value": float(result.f_pvalue)
    }
    
    return results_dict

def save_regression_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save regression results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Regression results saved to {output_path}")

def run_sensitivity_analysis(df: pd.DataFrame, 
                             target_col: str = 'land_use_change',
                             main_exog: str = 'regime_type',
                             primary_control: str = 'gdp_per_capita',
                             country_col: str = 'country_code',
                             time_col: str = 'year') -> Dict[str, Any]:
    """
    Run sensitivity analysis by comparing Full Model vs Model without GDP.
    """
    logger.info("Running Sensitivity Analysis...")
    
    # Full Model
    full_results = run_fixed_effects_regression(
        df, target_col, main_exog, controls=[primary_control], 
        country_col=country_col, time_col=time_col
    )
    
    # No GDP Model
    no_gdp_results = run_fixed_effects_regression(
        df, target_col, main_exog, controls=[], 
        country_col=country_col, time_col=time_col
    )
    
    coeff_full = full_results['coefficients'][main_exog]
    coeff_no_gdp = no_gdp_results['coefficients'][main_exog]
    
    pct_change = ((coeff_no_gdp - coeff_full) / abs(coeff_full)) * 100 if coeff_full != 0 else 0.0
    
    sensitivity_results = {
        "full_model": full_results,
        "no_gdp_model": no_gdp_results,
        "comparison": {
            "coeff_full": float(coeff_full),
            "coeff_no_gdp": float(coeff_no_gdp),
            "pct_change": float(pct_change)
        }
    }
    
    return sensitivity_results

def run_nonlinearity_robustness_check(df: pd.DataFrame,
                                      target_col: str = 'land_use_change',
                                      main_exog: str = 'regime_type',
                                      control: str = 'gdp_per_capita',
                                      country_col: str = 'country_code',
                                      time_col: str = 'year') -> Dict[str, Any]:
    """
    Run non-linearity check by adding a quadratic term for the main exog.
    """
    logger.info("Running Non-linearity Robustness Check...")
    
    # Create quadratic term
    df = df.copy()
    quad_col = f"{main_exog}_sq"
    df[quad_col] = df[main_exog] ** 2
    
    if not HAS_LINEARMODELS:
        raise ImportError("linearmodels package is required for non-linearity check.")
    
    formula = f"{target_col} ~ {main_exog} + {quad_col} + {control}"
    df_reindexed = df.set_index([country_col, time_col])
    
    model = PanelOLS.from_formula(formula, df_reindexed, entity_effects=True, time_effects=False)
    result = model.fit(cov_type='robust', debiased=True)
    
    results_dict = {
        "model_type": "Non-linear (Quadratic)",
        "rsquared_within": float(result.rsquared_within),
        "coefficients": {k: float(v) for k, v in result.params.items()},
        "p_values": {k: float(v) for k, v in result.pvalues.items()},
        "quad_significant": result.pvalues[quad_col] < 0.05
    }
    
    return results_dict

def run_random_effects_fallback(df: pd.DataFrame,
                                target_col: str = 'land_use_change',
                                main_exog: str = 'regime_type',
                                controls: Optional[List[str]] = None,
                                country_col: str = 'country_code',
                                time_col: str = 'year') -> Dict[str, Any]:
    """
    Implement Random Effects Fallback.
    If ALL countries are time-invariant (checked by T022), switch to Random Effects model
    and run Hausman test to compare RE vs FE.
    
    Returns:
        Dictionary containing RE results and Hausman test results.
    """
    if not HAS_LINEARMODELS:
        raise ImportError("linearmodels package is required for Random Effects fallback.")
    
    logger.info("Executing Random Effects Fallback logic...")
    
    if controls is None:
        controls = []
    
    # 1. Check if ALL countries are time-invariant
    # We re-run the detection logic here to be sure, or assume the caller passed the full list.
    # For this function, we assume the input df is the one that was flagged as ALL-invariant.
    # We check variance again to be safe.
    country_stats = df.groupby(country_col)[main_exog].agg(['var', 'count'])
    all_invariant = (country_stats['var'] == 0.0).all() or (country_stats['count'] == 1).all()
    
    if not all_invariant:
        logger.warning("Not all countries are time-invariant. Random Effects fallback may not be strictly necessary, but proceeding.")
    
    # 2. Run Random Effects Model
    logger.info("Running Random Effects Model...")
    
    required_vars = [target_col, main_exog] + controls + [country_col, time_col]
    missing = [v for v in required_vars if v not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for RE regression: {missing}")
    
    formula = f"{target_col} ~ {main_exog}"
    if controls:
        formula += " + " + " + ".join(controls)
    
    df_reindexed = df.set_index([country_col, time_col])
    
    # Run RE
    re_model = RandomEffects.from_formula(formula, df_reindexed)
    re_result = re_model.fit(cov_type='robust', debiased=True)
    
    logger.info(f"RE R-squared (Within): {re_result.rsquared_within:.4f}")
    logger.info(f"RE Coefficient ({main_exog}): {re_result.params[main_exog]:.4f}")
    
    # 3. Run Fixed Effects Model (for Hausman comparison)
    logger.info("Running Fixed Effects Model for Hausman comparison...")
    fe_model = PanelOLS.from_formula(formula, df_reindexed, entity_effects=True, time_effects=False)
    fe_result = fe_model.fit(cov_type='robust', debiased=True)
    
    # 4. Run Hausman Test
    # Hausman test compares FE and RE. Null hypothesis: RE is consistent (no correlation between effects and regressors).
    logger.info("Running Hausman Test...")
    try:
        # linearmodels has a specific Hausman test function or we can compute manually
        # Using the built-in test if available, otherwise manual
        # HausmanTest is not a standard method on result objects in all versions, 
        # so we construct the test statistic manually or use the helper if available.
        # In linearmodels, we can often just compare the models.
        
        # Manual Hausman implementation for robustness
        # H = (beta_fe - beta_re)' * (V_fe - V_re)^-1 * (beta_fe - beta_re)
        # We focus on the main exog and controls
        vars_to_test = [main_exog] + controls
        
        beta_fe = re_result.params[vars_to_test] # Note: using re_result.params keys to align
        # Actually, we need to align the indices carefully
        beta_fe = fe_result.params[vars_to_test]
        beta_re = re_result.params[vars_to_test]
        
        var_fe = fe_result.cov[vars_to_test, vars_to_test]
        var_re = re_result.cov[vars_to_test, vars_to_test]
        
        diff = beta_fe - beta_re
        diff_var = var_fe - var_re
        
        # Check if diff_var is positive definite
        if np.all(np.linalg.eigvals(diff_var) > 0):
            hausman_stat = float(diff.T @ np.linalg.inv(diff_var) @ diff)
            # Degrees of freedom = number of parameters tested
            df_hausman = len(vars_to_test)
            from scipy.stats import chi2
            p_value = float(chi2.sf(hausman_stat, df_hausman))
            hausman_result = {
                "statistic": hausman_stat,
                "df": df_hausman,
                "p_value": p_value,
                "reject_null_re_is_consistent": p_value < 0.05,
                "preferred_model": "Fixed Effects" if p_value < 0.05 else "Random Effects"
            }
            logger.info(f"Hausman Statistic: {hausman_stat:.4f}, P-value: {p_value:.4f}")
            logger.info(f"Preferred Model based on Hausman: {hausman_result['preferred_model']}")
        else:
            logger.warning("Hausman test covariance matrix not positive definite. Skipping test.")
            hausman_result = {
                "statistic": None,
                "df": None,
                "p_value": None,
                "error": "Covariance matrix not positive definite",
                "preferred_model": "Unknown"
            }
            
    except Exception as e:
        logger.error(f"Failed to run Hausman test: {e}", exc_info=True)
        hausman_result = {
            "statistic": None,
            "df": None,
            "p_value": None,
            "error": str(e)
        }

    # 5. Compile Results
    output = {
        "model_type": "Random Effects (Fallback)",
        "reason": "All countries time-invariant detected",
        "re_results": {
            "rsquared_within": float(re_result.rsquared_within),
            "rsquared_overall": float(re_result.rsquared_overall),
            "nobs": int(re_result.nobs),
            "coefficients": {k: float(v) for k, v in re_result.params.items()},
            "p_values": {k: float(v) for k, v in re_result.pvalues.items()},
            "standard_errors": {k: float(v) for k, v in re_result.std_err.items()}
        },
        "hausman_test": hausman_result
    }
    
    return output

def main():
    """
    Main entry point for regression analysis including T041 fallback logic.
    """
    config = get_config()
    data_path = Path(config['data_path'])
    processed_dir = Path(config['processed_path'])
    output_dir = Path(config['output_path'])
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    # Assuming the cleaned data from US1 is available
    data_file = data_path / "processed" / "cleaned_data.csv"
    if not data_file.exists():
        # Fallback to raw path if processed doesn't exist yet (for dev)
        data_file = data_path / "cleaned_data.csv"
    
    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}. Cannot run regression.")
        return
    
    df = pd.read_csv(data_file)
    
    # 1. Detect Time Invariant (T022)
    time_invariant_countries = detect_time_invariant_countries(df)
    
    # Save report for T022
    save_time_invariant_report(time_invariant_countries, processed_dir / "time_invariant_report.json")
    
    # 2. Check if ALL countries are time invariant
    unique_countries = df['country_code'].unique()
    if len(time_invariant_countries) == len(unique_countries) and len(unique_countries) > 0:
        logger.warning("ALL countries are time-invariant. Triggering Random Effects Fallback (T041).")
        
        # Run Fallback
        try:
            fallback_results = run_random_effects_fallback(df)
            save_regression_results(fallback_results, processed_dir / "regression_results_fallback.json")
            logger.info("Random Effects Fallback completed successfully.")
        except Exception as e:
            logger.error(f"Random Effects Fallback failed: {e}", exc_info=True)
    else:
        logger.info("Not all countries are time-invariant. Proceeding with Fixed Effects (T023).")
        # Filter out time-invariant countries
        filtered_df = filter_time_invariant_countries(df, time_invariant_countries)
        
        # Run Fixed Effects
        try:
            fe_results = run_fixed_effects_regression(filtered_df)
            save_regression_results(fe_results, processed_dir / "regression_results_primary.json")
            
            # Run Sensitivity (T024)
            sens_results = run_sensitivity_analysis(filtered_df)
            save_regression_results(sens_results, processed_dir / "sensitivity_coefficients.json")
            
            # Run Non-linearity (T025)
            nonlinear_results = run_nonlinearity_robustness_check(filtered_df)
            save_regression_results(nonlinear_results, processed_dir / "regression_results_nonlinear.json")
            
        except Exception as e:
            logger.error(f"Fixed Effects analysis failed: {e}", exc_info=True)
            return

    logger.info("Regression pipeline completed.")

if __name__ == "__main__":
    main()