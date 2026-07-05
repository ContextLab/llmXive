"""
Statistical Modeling Module for CSA Food Security Analysis.

Implements Mixed-Effects Regression, mediation analysis, and multiple hypothesis correction.
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import logging
import warnings
from scipy import stats

# Import from local project modules
from utils.config import get_processed_data_dir
from utils.logging import log_provenance_mapping

logger = logging.getLogger(__name__)


def calculate_fdr_adjusted_pvalues(p_values: List[float], method: str = 'bh') -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Parameters
    ----------
    p_values : List[float]
        List of raw p-values from hypothesis tests.
    method : str
        Correction method. Currently only 'bh' (Benjamini-Hochberg) is supported.

    Returns
    -------
    List[float]
        List of adjusted p-values (q-values) sorted by original rank.
    """
    if not p_values:
        return []

    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])

    # Benjamini-Hochberg procedure
    ranks = np.arange(1, n + 1)
    # Calculate critical values: (i/n) * alpha
    # But we return the adjusted p-values (q-values) directly
    # q_i = min( (n/i) * p_i, q_{i+1} ) ensuring monotonicity from right to left
    
    q_values = (sorted_p * n) / ranks
    
    # Enforce monotonicity: q_i <= q_{i+1} (cumulative min from the end)
    # We iterate backwards to ensure q_i is the minimum of itself and all subsequent q's
    for i in range(n - 2, -1, -1):
        if q_values[i] > q_values[i + 1]:
            q_values[i] = q_values[i + 1]
    
    # Cap at 1.0
    q_values = np.minimum(q_values, 1.0)

    # Re-order to original positions
    result = [0.0] * n
    for idx, q in zip(sorted_indices, q_values):
        result[idx] = float(q)

    return result


def run_mixed_effects_model(
    data: pd.DataFrame,
    dependent_var: str,
    independent_vars: List[str],
    random_effect_formula: str = '0 + 1 | country/region',
    interaction_terms: Optional[List[str]] = None,
    mediation_vars: Optional[List[str]] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Fit a Mixed-Effects Regression model with optional interaction and mediation terms.
    
    Applies Benjamini-Hochberg FDR correction for multiple hypothesis testing.

    Parameters
    ----------
    data : pd.DataFrame
        The analysis-ready dataset.
    dependent_var : str
        Name of the dependent variable (e.g., 'food_security_index').
    independent_vars : List[str]
        List of independent variables (e.g., CSA index, controls).
    random_effect_formula : str
        Formula for random effects (default: '0 + 1 | country/region').
    interaction_terms : List[str], optional
        List of interaction term strings (e.g., ['CSA_Index * digital_access']).
    mediation_vars : List[str], optional
        List of variables to test for mediation effects.
    alpha : float
        Significance level for initial testing.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing model summary, coefficients, p-values, 
        FDR-adjusted p-values, and random effect estimates.
    """
    logger.info(f"Fitting Mixed-Effects Model: {dependent_var} ~ {independent_vars}")

    # Construct formula
    base_formula = f"{dependent_var} ~ {' + '.join(independent_vars)}"
    
    if interaction_terms:
        base_formula += f" + {' + '.join(interaction_terms)}"

    if mediation_vars:
        # Mediation analysis is typically a separate set of models, 
        # but we include them as predictors here for the main associational model
        base_formula += f" + {' + '.join(mediation_vars)}"

    logger.info(f"Model Formula: {base_formula}")

    try:
        # Fit the model
        model = smf.mixedlm(base_formula, data, groups=data["region"])
        result = model.fit()
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "coefficients": None,
            "p_values": None,
            "fdr_adjusted_p_values": None
        }

    # Extract results
    coef_df = result.summary2().tables[1]
    coefficients = coef_df['Coef.']
    std_errors = coef_df['Std.Err.']
    t_values = coef_df['t']
    p_values = coef_df['P>|t|']

    # Prepare lists for FDR correction
    # Exclude the intercept from multiple testing correction if desired, 
    # but typically we correct all tested coefficients.
    # We filter out non-numeric or NaN p-values
    valid_indices = []
    raw_p_vals = []
    var_names = []

    for idx, row in coef_df.iterrows():
        if idx == 'Const': continue # Often excluded from FDR in this context, but can include
        p_val = row['P>|t|']
        if pd.notna(p_val) and p_val < 1.0: # Avoid infinite p-values if any
            raw_p_vals.append(p_val)
            var_names.append(idx)
            valid_indices.append(idx)

    # Apply Benjamini-Hochberg FDR
    if len(raw_p_vals) > 1:
        adjusted_p_vals = calculate_fdr_adjusted_pvalues(raw_p_vals, method='bh')
    else:
        # If 0 or 1 hypothesis, FDR is trivial
        adjusted_p_vals = raw_p_vals

    # Map back to dictionary
    fdr_results = dict(zip(var_names, adjusted_p_vals))

    # Log provenance
    log_provenance_mapping(
        {
            "model_type": "Mixed-Effects",
            "formula": base_formula,
            "correction_method": "Benjamini-Hochberg",
            "num_hypotheses": len(raw_p_vals)
        }
    )

    logger.info(f"Model fitting complete. FDR correction applied to {len(raw_p_vals)} hypotheses.")

    return {
        "success": True,
        "formula": base_formula,
        "coefficients": coefficients.to_dict(),
        "std_errors": std_errors.to_dict(),
        "p_values": p_values.to_dict(),
        "fdr_adjusted_p_values": fdr_results,
        "random_effects": result.random_effects,
        "log_likelihood": result.llf,
        "aic": result.aic,
        "bic": result.bic
    }


def run_mediation_analysis(
    data: pd.DataFrame,
    outcome: str,
    treatment: str,
    mediator: str,
    covariates: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform a simple mediation analysis (Baron & Kenny approach) using OLS.
    Note: This is an associational analysis as per project constraints.

    Parameters
    ----------
    data : pd.DataFrame
        The dataset.
    outcome : str
        Dependent variable.
    treatment : str
        Independent variable (CSA Index).
    mediator : str
        Mediating variable (e.g., digital access).
    covariates : List[str], optional
        Control variables.

    Returns
    -------
    Dict[str, Any]
        Direct effect, indirect effect, and total effect estimates.
    """
    logger.info(f"Running Mediation Analysis: {treatment} -> {mediator} -> {outcome}")

    # Model 1: Outcome ~ Treatment + Covariates (Total Effect of Treatment)
    # Model 2: Mediator ~ Treatment + Covariates
    # Model 3: Outcome ~ Treatment + Mediator + Covariates (Direct Effect)

    cov_str = f" + {' + '.join(covariates)}" if covariates else ""
    
    formula_1 = f"{outcome} ~ {treatment} {cov_str}"
    formula_2 = f"{mediator} ~ {treatment} {cov_str}"
    formula_3 = f"{outcome} ~ {treatment} + {mediator} {cov_str}"

    try:
        m1 = smf.ols(formula_1, data).fit()
        m2 = smf.ols(formula_2, data).fit()
        m3 = smf.ols(formula_3, data).fit()
    except Exception as e:
        logger.error(f"Mediation analysis failed: {e}")
        return {"success": False, "error": str(e)}

    # Coefficients
    # Total effect (c)
    c = m1.params.get(treatment, 0)
    # Effect of treatment on mediator (a)
    a = m2.params.get(treatment, 0)
    # Effect of mediator on outcome (b)
    b = m3.params.get(mediator, 0)
    # Direct effect (c')
    c_prime = m3.params.get(treatment, 0)

    # Indirect effect (a * b)
    indirect = a * b
    total_effect = c_prime + indirect

    return {
        "success": True,
        "total_effect": float(total_effect),
        "direct_effect": float(c_prime),
        "indirect_effect": float(indirect),
        "effect_a": float(a),
        "effect_b": float(b),
        "model_1_r2": float(m1.rsquared),
        "model_2_r2": float(m2.rsquared),
        "model_3_r2": float(m3.rsquared)
    }


def main():
    """
    Entry point to run the modeling pipeline on the processed dataset.
    """
    logger.info("Starting Model Pipeline")
    
    # Load data
    data_path = get_processed_data_dir() / "merged_sample.parquet"
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return

    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} records for modeling.")

    # Define variables (example based on typical CSA analysis)
    # Ensure these columns exist in the data; otherwise, the model will fail gracefully
    dep_var = "food_security_index"
    indep_vars = ["csa_index", "farm_size", "household_size", "education_level"]
    interactions = ["csa_index * digital_access_score"]
    mediators = ["digital_access_score"]
    random_effect = "0 + 1 | country/region"

    # Check for necessary columns
    required_cols = [dep_var] + indep_vars + [i.split('*')[0].strip() for i in interactions] + [i.split('*')[1].strip() for i in interactions] + mediators
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        logger.warning(f"Missing columns for full model: {missing_cols}. Attempting with available subset.")
        # Filter vars to those present
        indep_vars = [v for v in indep_vars if v in df.columns]
        interactions = [i for i in interactions if all(v.strip() in df.columns for v in i.split('*'))]
        mediators = [m for m in mediators if m in df.columns]

    # Run Mixed Effects Model
    results = run_mixed_effects_model(
        data=df,
        dependent_var=dep_var,
        independent_vars=indep_vars,
        random_effect_formula=random_effect,
        interaction_terms=interactions,
        mediation_vars=mediators
    )

    if results.get("success"):
        # Save results
        output_dir = get_processed_data_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert coefficients to DataFrame for saving
        coef_df = pd.DataFrame([
            {"variable": k, "coefficient": v, "p_value": results["p_values"].get(k, np.nan), "fdr_p_value": results["fdr_adjusted_p_values"].get(k, np.nan)}
            for k, v in results["coefficients"].items()
        ])
        
        output_path = output_dir / "model_results.csv"
        coef_df.to_csv(output_path, index=False)
        logger.info(f"Model results saved to {output_path}")
        
        # Save full stats dict as JSON if needed (omitted here for brevity, but standard practice)
    else:
        logger.error("Model execution failed.")
        print(f"Error: {results.get('error')}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()