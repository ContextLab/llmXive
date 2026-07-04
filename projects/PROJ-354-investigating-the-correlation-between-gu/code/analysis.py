"""
Statistical Analysis Module for Gut Microbiome-Cognitive Correlation Study.

Implements OLS linear models, Benjamini-Hochberg correction, and interaction analysis.
Enforces citation validity from config.py (T024b).
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

# Local Imports (ensuring API surface matches)
from code.config import (
    ARTIFACT_PATHS,
    VALIDATED_CITATIONS,
    get_validated_citation,
    validate_citation_id,
    FDR_THRESHOLD,
    SIGNIFICANCE_THRESHOLD,
)
from code.utils.logging import get_logger, AnalysisError

logger = get_logger(__name__)

def _validate_citations_for_analysis() -> None:
    """
    Enforce citation validity before running analysis.
    Checks that all required cognitive instrument citations are validated.
    """
    required_citations = [
        "fluid_intelligence_score",
        "reaction_time",
        "pairs_matching",
    ]
    
    missing = []
    for key in required_citations:
        if not validate_citation_id(key):
            missing.append(key)
    
    if missing:
        error_msg = f"Citation validation failed for analysis. Missing validated IDs: {missing}. " \
                    f"Please run T024a (Instrument Validator) first."
        logger.error(error_msg)
        raise AnalysisError(error_msg)
    
    logger.info("All required cognitive instrument citations validated successfully.")

def fit_ols_model(
    df: pd.DataFrame,
    outcome_col: str,
    predictor_col: str,
    covariate_cols: List[str],
    interaction_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fit a Standard OLS linear model.

    Args:
        df: DataFrame containing the data
        outcome_col: Name of the outcome variable (cognitive score)
        predictor_col: Name of the predictor variable (ILR coordinate)
        covariate_cols: List of covariate column names
        interaction_col: Optional column name for interaction term

    Returns:
        Dictionary with model statistics (beta, p-value, adj_p, r_squared)
    """
    _validate_citations_for_analysis()

    # Prepare data
    cols = [outcome_col, predictor_col] + covariate_cols
    if interaction_col:
        cols.append(interaction_col)
    
    # Drop rows with missing values
    clean_df = df[cols].dropna()
    
    if len(clean_df) < 10:
        logger.warning(f"Insufficient data points for model fitting ({len(clean_df)} < 10).")
        return {
            "beta": np.nan,
            "p_value": np.nan,
            "adj_p_value": np.nan,
            "r_squared": np.nan,
            "n_obs": len(clean_df),
            "status": "insufficient_data"
        }

    # Define design matrix
    y = clean_df[outcome_col].values
    X = clean_df[[predictor_col] + covariate_cols]
    
    if interaction_col:
        X = pd.concat([X, clean_df[[interaction_col]]], axis=1)
    
    X = sm.add_constant(X)
    
    try:
        model = sm.OLS(y, X).fit()
        # Get the coefficient for the predictor
        pred_idx = list(X.columns).index(predictor_col)
        beta = model.params[pred_idx]
        p_val = model.pvalues[pred_idx]
        r_sq = model.rsquared
        
        return {
            "beta": beta,
            "p_value": p_val,
            "adj_p_value": np.nan, # Calculated later in batch
            "r_squared": r_sq,
            "n_obs": len(clean_df),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"OLS model fitting failed: {e}")
        return {
            "beta": np.nan,
            "p_value": np.nan,
            "adj_p_value": np.nan,
            "r_squared": np.nan,
            "n_obs": len(clean_df),
            "status": "error",
            "error": str(e)
        }

def apply_benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.

    Args:
        p_values: Array of raw p-values

    Returns:
        Array of adjusted p-values
    """
    if len(p_values) == 0:
        return np.array([])
    
    # Use statsmodels implementation
    reject, pvals_corrected, _, _ = multipletests(
        p_values, 
        alpha=FDR_THRESHOLD, 
        method='fdr_bh'
    )
    return pvals_corrected

def run_main_effects_analysis(
    ilr_df: pd.DataFrame,
    cognitive_scores: pd.DataFrame,
    covariates: List[str],
    output_path: Path
) -> pd.DataFrame:
    """
    Run main effects analysis for all taxon-cognitive associations.

    Args:
        ilr_df: DataFrame with ILR coordinates
        cognitive_scores: DataFrame with cognitive scores
        covariates: List of covariate column names
        output_path: Path to save results

    Returns:
        DataFrame with association statistics
    """
    _validate_citations_for_analysis()
    
    logger.info("Starting Main Effects Analysis...")
    
    # Merge data
    merged_df = ilr_df.merge(cognitive_scores, on="eid")
    
    results = []
    cognitive_vars = [col for col in cognitive_scores.columns if col != "eid"]
    ilr_vars = [col for col in ilr_df.columns if col != "eid"]
    
    total_tests = len(ilr_vars) * len(cognitive_vars)
    logger.info(f"Running {total_tests} tests.")
    
    for cov in cognitive_vars:
        for ilr in ilr_vars:
            res = fit_ols_model(
                merged_df,
                outcome_col=cov,
                predictor_col=ilr,
                covariate_cols=covariates
            )
            res["outcome"] = cov
            res["predictor"] = ilr
            results.append(res)
    
    results_df = pd.DataFrame(results)
    
    # Apply FDR correction per outcome
    for outcome in cognitive_vars:
        mask = results_df["outcome"] == outcome
        p_vals = results_df.loc[mask, "p_value"].values
        adj_p = apply_benjamini_hochberg(p_vals)
        results_df.loc[mask, "adj_p_value"] = adj_p
    
    # Add metadata
    results_df["causality_claim"] = False
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_parquet(output_path, index=False)
    logger.info(f"Main effects results saved to {output_path}")
    
    return results_df

def run_interaction_analysis(
    ilr_df: pd.DataFrame,
    cognitive_scores: pd.DataFrame,
    age_group_col: str,
    covariates: List[str],
    output_path: Path
) -> pd.DataFrame:
    """
    Run interaction analysis (Age_Group * Taxon).

    Args:
        ilr_df: DataFrame with ILR coordinates
        cognitive_scores: DataFrame with cognitive scores (includes age_group_col)
        age_group_col: Column name for age groups
        covariates: List of covariate column names
        output_path: Path to save results

    Returns:
        DataFrame with interaction statistics
    """
    _validate_citations_for_analysis()
    
    logger.info("Starting Interaction Analysis...")
    
    merged_df = ilr_df.merge(cognitive_scores, on="eid")
    
    results = []
    cognitive_vars = [col for col in cognitive_scores.columns if col != "eid" and col != age_group_col]
    ilr_vars = [col for col in ilr_df.columns if col != "eid"]
    
    total_tests = len(ilr_vars) * len(cognitive_vars)
    logger.info(f"Running {total_tests} interaction tests.")
    
    for cov in cognitive_vars:
        for ilr in ilr_vars:
            # Construct interaction term manually if not in df
            # Assuming age_group_col is categorical or we create dummy
            interaction_name = f"{ilr}_x_{age_group_col}"
            
            # For simplicity in this module, we assume the interaction term 
            # is pre-computed or we fit a model with the interaction column
            # In a real pipeline, this might be more complex.
            # Here we assume the interaction term is passed or constructed.
            # To be robust, we construct the term if it exists as a column or create it.
            
            # Let's assume the interaction term is provided in the df or constructed here
            # For this implementation, we will fit the model with the interaction term
            # if it exists in the dataframe, otherwise skip or warn.
            
            # Simplified approach: Fit model with interaction term explicitly
            # We need the interaction term column to exist.
            # In a real scenario, we would generate this in preprocess.
            # Here we assume 'interaction_term' is not a single column but we model:
            # Y ~ Taxon + AgeGroup + Taxon*AgeGroup + Covariates
            
            # We will use statsmodels formula for clarity if possible, 
            # but to stick to the API, we use the matrix approach.
            # We need to create the interaction column in a temp df.
            
            temp_df = merged_df.copy()
            # Assuming age_group_col is numeric or we map it to 0/1 for interaction
            # If it's categorical, we need dummies. For this specific task, 
            # let's assume we have a binary 'Age_Group' or we use the column directly.
            # If the column is categorical, we need to handle it.
            # Let's assume the column is numeric (0, 1) for interaction.
            
            if temp_df[age_group_col].dtype == 'object':
                # Map to numeric for interaction
                temp_df[age_group_col] = temp_df[age_group_col].astype('category').cat.codes
            
            temp_df[interaction_name] = temp_df[ilr] * temp_df[age_group_col]
            
            res = fit_ols_model(
                temp_df,
                outcome_col=cov,
                predictor_col=interaction_name,
                covariate_cols=covariates + [ilr, age_group_col]
            )
            res["outcome"] = cov
            res["predictor"] = interaction_name
            results.append(res)
    
    results_df = pd.DataFrame(results)
    
    # Apply FDR
    for outcome in cognitive_vars:
        mask = results_df["outcome"] == outcome
        p_vals = results_df.loc[mask, "p_value"].values
        adj_p = apply_benjamini_hochberg(p_vals)
        results_df.loc[mask, "adj_p_value"] = adj_p
    
    results_df["causality_claim"] = False
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_parquet(output_path, index=False)
    logger.info(f"Interaction results saved to {output_path}")
    
    return results_df

def main():
    """Main entry point for analysis."""
    logger.info("Analysis module loaded. Citation validation active.")
    # This would typically be called by a pipeline script
    pass

if __name__ == "__main__":
    main()
