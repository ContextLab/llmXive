"""
Statistical modeling module for hippocampal subfield analysis.

This module implements Linear Mixed-Effects (LMM) models,
variance inflation factor (VIF) calculations, and ratio analyses
to investigate associations between early life stress and brain volumes.
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from code.config import get_project_root, ensure_directories
from code.analysis.results import StatisticalModel, AnalysisResult

# Constants
VIF_THRESHOLD = 5.0
RANDOM_SEED = 42


def calculate_vif(df: pd.DataFrame, formula: str) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors (VIF) for covariates in a formula.

    Args:
        df: The dataframe containing the data.
        formula: The statsmodel formula string (e.g., 'y ~ x1 + x2').

    Returns:
        A dictionary mapping variable names to their VIF values.
    """
    # Parse formula to get independent variables
    # Simple parsing: split by '+' and clean up
    parts = formula.split('~')
    if len(parts) != 2:
        raise ValueError("Formula must contain exactly one '~'")

    _, rhs = parts
    # Remove random effects for VIF calculation (fixed effects only)
    rhs_clean = rhs.split(' + (1|')[0].strip()
    vars_list = [v.strip() for v in rhs_clean.split('+') if v.strip()]

    vif_data = {}
    # Create design matrix
    try:
        design = smf.ols(formula, data=df).fit()
        # statsmodels doesn't have a direct VIF function, so we calculate manually
        # using the correlation matrix of the independent variables
        # Note: This is a simplified approach; for rigorous VIF, use statsmodels.stats.outliers_influence.variance_inflation_factor
        pass
    except Exception:
        # Fallback: calculate using correlation matrix of independent variables
        pass

    # Robust VIF calculation using design matrix
    # Extract independent variables
    indep_vars = []
    for var in vars_list:
        if var in df.columns:
            indep_vars.append(var)

    if not indep_vars:
        return vif_data

    # Add intercept if not present
    if 'Intercept' not in indep_vars:
        indep_vars.insert(0, 'Intercept')

    X = df[indep_vars].values
    if X.shape[1] < 2:
        return {var: 1.0 for var in vars_list}

    # Center variables for VIF (excluding intercept)
    X_centered = X[:, 1:] - np.mean(X[:, 1:], axis=0)

    # Calculate correlation matrix
    corr_matrix = np.corrcoef(X_centered, rowvar=False)

    # Calculate VIFs
    for i, var in enumerate(vars_list):
        try:
            # VIF = 1 / (1 - R^2) where R^2 is from regressing var on others
            # Using diagonal of inverse correlation matrix
            inv_corr = np.linalg.inv(corr_matrix)
            vif = inv_corr[i, i]
            vif_data[var] = float(vif)
        except np.linalg.LinAlgError:
            vif_data[var] = float('inf')

    return vif_data


def residualize_column(df: pd.DataFrame, target_col: str, covariates: List[str]) -> pd.Series:
    """
    Residualize a target column against a list of covariates.

    Args:
        df: The dataframe containing the data.
        target_col: The name of the column to residualize.
        covariates: List of covariate column names.

    Returns:
        A pandas Series containing the residuals.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe")

    # Build formula
    covariates_str = ' + '.join(covariates)
    formula = f"{target_col} ~ {covariates_str}"

    model = smf.ols(formula, data=df).fit()
    residuals = model.resid

    return residuals


def apply_residualization_strategy(df: pd.DataFrame, target_col: str) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Apply residualization strategy if multicollinearity is detected.

    Args:
        df: The dataframe containing the data.
        target_col: The target column (e.g., ACE_score) to residualize.

    Returns:
        A tuple of (modified dataframe, dict of VIF values).
    """
    # Define covariates to check against
    covariates = ['age', 'sex', 'scanner_site']
    # Filter to existing columns
    existing_covariates = [c for c in covariates if c in df.columns]

    if not existing_covariates:
        return df, {}

    # Build formula for VIF check
    formula = f"{target_col} ~ {' + '.join(existing_covariates)}"
    vif_values = calculate_vif(df, formula)

    max_vif = max(vif_values.values()) if vif_values else 0.0

    if max_vif > VIF_THRESHOLD:
        # Find the covariate with highest VIF
        worst_covariate = max(vif_values, key=vif_values.get)
        other_covariates = [c for c in existing_covariates if c != worst_covariate]

        # Residualize target against the problematic covariate
        residuals = residualize_column(df, target_col, [worst_covariate])
        df = df.copy()
        df[f"{target_col}_resid"] = residuals

        return df, vif_values

    return df, vif_values


def fit_lmm_for_subfield(
    df: pd.DataFrame,
    subfield_col: str,
    formula: str,
    random_seed: int = RANDOM_SEED
) -> StatisticalModel:
    """
    Fit a Linear Mixed-Effects Model for a specific hippocampal subfield.

    Args:
        df: The dataframe containing the data.
        subfield_col: The name of the subfield volume column.
        formula: The statsmodel formula string.
        random_seed: Random seed for reproducibility.

    Returns:
        A StatisticalModel object containing the fit results.
    """
    np.random.seed(random_seed)

    if subfield_col not in df.columns:
        raise ValueError(f"Subfield column '{subfield_col}' not found in dataframe")

    try:
        model = smf.mixedlm(formula, df, groups=df["family_id"])
        result = model.fit(reml=False)  # Use ML for comparison

        # Extract parameters
        params = result.params.to_dict()
        conf_int = result.conf_int()

        # Extract specific coefficients
        beta_ace = params.get("ACE_score", np.nan)
        p_value_ace = result.pvalues.get("ACE_score", np.nan)

        # 95% CI for ACE
        ci_low = conf_int.loc["ACE_score", 0] if "ACE_score" in conf_int.index else np.nan
        ci_high = conf_int.loc["ACE_score", 1] if "ACE_score" in conf_int.index else np.nan

        return StatisticalModel(
            subfield=subfield_col,
            formula=formula,
            beta_ace=beta_ace,
            ci_95_low=ci_low,
            ci_95_high=ci_high,
            p_value=p_value_ace,
            log_likelihood=result.loglike,
            aic=result.aic,
            bic=result.bic,
            n_obs=len(df)
        )

    except Exception as e:
        logging.error(f"Failed to fit LMM for {subfield_col}: {e}")
        # Return a failed model object or raise
        raise e


def run_primary_analysis(df: pd.DataFrame) -> Dict[str, StatisticalModel]:
    """
    Run the primary LMM analysis for all three subfields.

    Args:
        df: The preprocessed dataframe.

    Returns:
        A dictionary mapping subfield names to their StatisticalModel objects.
    """
    subfields = ["CA3", "DG", "Subiculum"]
    formula = "vol ~ ACE_score + age + sex + scanner_site + (1|family_id)"

    results = {}
    for subfield in subfields:
        col_name = f"{subfield}_norm" if f"{subfield}_norm" in df.columns else subfield
        if col_name in df.columns:
            try:
                model = fit_lmm_for_subfield(df, col_name, formula)
                results[subfield] = model
            except Exception as e:
                logging.error(f"Error fitting model for {subfield}: {e}")
        else:
            logging.warning(f"Column {col_name} not found for {subfield}")

    return results


def calculate_ca3_dg_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the CA3:DG volume ratio for each participant.

    Args:
        df: The dataframe containing CA3 and DG volumes.

    Returns:
        The dataframe with a new 'CA3_DG_ratio' column.
    """
    df = df.copy()
    ca3_col = "CA3_norm" if "CA3_norm" in df.columns else "CA3"
    dg_col = "DG_norm" if "DG_norm" in df.columns else "DG"

    if ca3_col not in df.columns or dg_col not in df.columns:
        raise ValueError("Required columns CA3 and DG (or their normalized versions) not found")

    # Avoid division by zero
    df["CA3_DG_ratio"] = df[ca3_col] / (df[dg_col] + 1e-6)

    return df


def fit_ca3_dg_ratio_model(df: pd.DataFrame) -> StatisticalModel:
    """
    Fit an exploratory model for the CA3:DG ratio.

    Args:
        df: The dataframe containing the CA3_DG_ratio column.

    Returns:
        A StatisticalModel object for the ratio analysis.
    """
    formula = "CA3_DG_ratio ~ ACE_score + age + sex + scanner_site + (1|family_id)"

    if "CA3_DG_ratio" not in df.columns:
        df = calculate_ca3_dg_ratio(df)

    return fit_lmm_for_subfield(df, "CA3_DG_ratio", formula)


def main() -> None:
    """
    Main entry point for the modeling module.
    Loads data, runs primary analysis, and saves results.
    """
    project_root = get_project_root()
    ensure_directories()

    data_path = project_root / "data" / "processed" / "cleaned_dataset.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)

    logging.info(f"Loaded {len(df)} participants")

    # Run primary analysis
    results = run_primary_analysis(df)

    # Save results
    output_path = project_root / "data" / "processed" / "model_results.json"
    with open(output_path, 'w') as f:
        import json
        json_results = {k: v.to_dict() for k, v in results.items()}
        json.dump(json_results, f, indent=2)

    logging.info(f"Results saved to {output_path}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    main()
