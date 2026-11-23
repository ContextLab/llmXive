import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

from config import get_path, ensure_directories
from utils.logging import get_logger, AnalysisError, LlmXiveError
from utils.hygiene import compute_file_checksum, generate_data_manifest

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper Functions for Confounder Handling
# ----------------------------------------------------------------------

def get_confounder_formula(
    outcome_col: str,
    confounders: Optional[List[str]] = None,
    include_intercept: bool = True
) -> str:
    """
    Constructs the R-style formula string for OLS regression.

    Args:
        outcome_col: Name of the dependent variable column.
        confounders: List of independent variable column names to control for.
        include_intercept: Whether to include the intercept (default True).

    Returns:
        Formula string suitable for statsmodels.
    """
    if confounders is None:
        confounders = []

    predictors = " + ".join(confounders)
    if include_intercept:
        # statsmodels adds intercept by default unless -1 is specified
        # We explicitly list it for clarity or rely on default behavior
        formula = f"{outcome_col} ~ {predictors}" if predictors else f"{outcome_col} ~ 1"
    else:
        formula = f"{outcome_col} ~ {predictors} - 1" if predictors else f"{outcome_col} ~ 0"
    
    return formula


def validate_confounders_present(df: pd.DataFrame, confounders: List[str]) -> bool:
    """
    Checks if all required confounder columns exist in the dataframe.

    Args:
        df: Input dataframe.
        confounders: List of required column names.

    Returns:
        True if all confounders are present, raises AnalysisError otherwise.
    """
    missing = [col for col in confounders if col not in df.columns]
    if missing:
        raise AnalysisError(f"Missing required confounder columns: {missing}")
    return True


# ----------------------------------------------------------------------
# Core Statistical Analysis Functions
# ----------------------------------------------------------------------

def fit_ols_model(
    df: pd.DataFrame,
    outcome_col: str,
    predictor_col: str,
    confounders: List[str]
) -> Dict[str, Any]:
    """
    Fits a standard OLS linear model: outcome ~ predictor + confounders.

    Args:
        df: DataFrame containing the data.
        outcome_col: Column name for the dependent variable (e.g., cognitive score).
        predictor_col: Column name for the independent variable (e.g., ILR coordinate).
        confounders: List of column names for covariates.

    Returns:
        Dictionary containing:
            - 'beta': Coefficient for the predictor.
            - 'pvalue': P-value for the predictor.
            - 'std_err': Standard error of the predictor.
            - 'model': The fitted statsmodels OLSResults object.
    """
    # Ensure all columns exist
    required_cols = [outcome_col, predictor_col] + confounders
    validate_confounders_present(df, required_cols)

    # Drop rows with missing values in any of the required columns
    model_data = df[required_cols].dropna()
    
    if len(model_data) == 0:
        raise AnalysisError(f"No valid rows remaining after dropping NaNs for {predictor_col}")

    # Construct formula
    formula = get_confounder_formula(outcome_col, [predictor_col] + confounders)

    try:
        model = sm.OLS.from_formula(formula, data=model_data)
        results = model.fit()
    except Exception as e:
        raise AnalysisError(f"OLS fitting failed for {predictor_col}: {str(e)}")

    # Extract results for the specific predictor
    # The params index will match the predictor name exactly if using from_formula
    params = results.params
    pvalues = results.pvalues
    std_errs = results.bse

    if predictor_col not in params.index:
        # Fallback for edge cases, though from_formula usually handles it
        raise AnalysisError(f"Predictor '{predictor_col}' not found in model results")

    return {
        'beta': float(params[predictor_col]),
        'pvalue': float(pvalues[predictor_col]),
        'std_err': float(std_errs[predictor_col]),
        'tvalue': float(results.tvalues[predictor_col]),
        'r_squared': float(results.rsquared),
        'adj_r_squared': float(results.rsquared_adj),
        'n_obs': int(results.nobs),
        'model': results  # Keep the full object if needed for diagnostics
    }


def apply_benjamini_hochberg(
    pvalues: np.ndarray,
    alpha: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Applies the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).

    Args:
        pvalues: Array of raw p-values.
        alpha: Significance level for FDR (default 0.05).

    Returns:
        Tuple of (reject_hypothesis, adjusted_pvalues).
        - reject_hypothesis: Boolean array indicating if the null hypothesis is rejected.
        - adjusted_pvalues: The FDR-adjusted p-values (q-values).
    """
    if len(pvalues) == 0:
        return np.array([]), np.array([])

    # Use statsmodels implementation which handles sorting and monotonicity correction
    # method='fdr_bh' implements the Benjamini-Hochberg linear step-up procedure
    reject, adj_pvals, _, _ = multipletests(pvalues, alpha=alpha, method='fdr_bh')

    return reject, adj_pvals


# ----------------------------------------------------------------------
# Main Execution Logic for Task T021
# ----------------------------------------------------------------------

def run_main_effects_analysis(
    ilr_data_path: str,
    cognitive_data_path: str,
    confounder_cols: List[str],
    output_path: str,
    age_group_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Runs the main effects analysis:
    1. Loads ILR coordinates and cognitive scores.
    2. Merges on participant ID.
    3. Fits OLS models for each ILR coordinate against cognitive score + confounders.
    4. Applies Benjamini-Hochberg correction.
    5. Saves results to Parquet.

    Args:
        ilr_data_path: Path to the ILR-transformed parquet file.
        cognitive_data_path: Path to the cognitive scores parquet file.
        confounder_cols: List of confounder column names.
        output_path: Path to save the results parquet file.
        age_group_col: Optional column name for age groups (for potential future interaction checks).

    Returns:
        DataFrame containing the analysis results.
    """
    logger.info(f"Loading ILR data from {ilr_data_path}")
    ilr_df = pd.read_parquet(ilr_data_path)
    
    logger.info(f"Loading cognitive data from {cognitive_data_path}")
    cog_df = pd.read_parquet(cognitive_data_path)

    # Determine the merge key (usually 'participant_id' or similar)
    # Assuming standard naming convention based on project context
    merge_key = 'participant_id'
    if merge_key not in ilr_df.columns or merge_key not in cog_df.columns:
        # Fallback to common variations
        candidates = ['eid', 'f20400', 'id']
        found = False
        for c in candidates:
            if c in ilr_df.columns and c in cog_df.columns:
                merge_key = c
                found = True
                break
        if not found:
            raise AnalysisError("Could not find a common merge key between ILR and Cognitive data.")

    logger.info(f"Merging on key: {merge_key}")
    merged_df = pd.merge(ilr_df, cog_df, on=merge_key, how='inner')
    
    if len(merged_df) == 0:
        raise AnalysisError("No overlapping participants found between ILR and Cognitive datasets.")

    logger.info(f"Merged dataset size: {len(merged_df)} participants")

    # Identify ILR columns (typically prefixed with 'ilr_' or ending in '_ilr')
    # Based on T015 output, we assume columns are named appropriately.
    # We will look for columns that are numeric and not the merge key, outcome, or confounders.
    outcome_col = 'cognitive_score' # Assumed column name from T012/T020
    if outcome_col not in merged_df.columns:
        # Try to find a column that looks like a cognitive score
        possible_outcomes = [c for c in merged_df.columns if 'cog' in c.lower() or 'score' in c.lower()]
        if possible_outcomes:
            outcome_col = possible_outcomes[0]
            logger.warning(f"Assumed cognitive score column: {outcome_col}")
        else:
            raise AnalysisError(f"Could not identify cognitive score column. Available: {merged_df.columns.tolist()}")

    # Filter out non-ILR columns
    exclude_cols = [merge_key, outcome_col] + confounder_cols
    ilr_cols = [c for c in merged_df.columns if c not in exclude_cols and np.issubdtype(merged_df[c].dtype, np.number)]

    if not ilr_cols:
        raise AnalysisError("No ILR coordinate columns found in the merged dataset.")

    logger.info(f"Found {len(ilr_cols)} ILR coordinates to test.")

    results = []

    for coord in ilr_cols:
        try:
            stats = fit_ols_model(
                merged_df,
                outcome_col=outcome_col,
                predictor_col=coord,
                confounders=confounder_cols
            )
            results.append({
                'taxon_coordinate': coord,
                'outcome': outcome_col,
                'beta': stats['beta'],
                'pvalue': stats['pvalue'],
                'std_err': stats['std_err'],
                'tvalue': stats['tvalue'],
                'r_squared': stats['r_squared'],
                'n_obs': stats['n_obs']
            })
        except Exception as e:
            logger.error(f"Failed to fit model for {coord}: {e}")
            # Log error but continue with other taxa
            results.append({
                'taxon_coordinate': coord,
                'outcome': outcome_col,
                'beta': np.nan,
                'pvalue': np.nan,
                'std_err': np.nan,
                'tvalue': np.nan,
                'r_squared': np.nan,
                'n_obs': 0,
                'error': str(e)
            })

    results_df = pd.DataFrame(results)

    # Apply Benjamini-Hochberg correction
    if 'pvalue' in results_df.columns:
        valid_pvals = results_df['pvalue'].dropna().values
        if len(valid_pvals) > 0:
            _, adj_pvals = apply_benjamini_hochberg(valid_pvals)
            # Map back to the dataframe
            # We need to align the sorted indices or just map by value if unique?
            # Better: re-run on the full series, handling NaNs
            
            # statsmodels multipletests handles NaNs by returning NaN for them? 
            # Let's do it manually to be safe with the index alignment
            pvals_series = results_df['pvalue']
            non_nan_idx = pvals_series.notna()
            if non_nan_idx.any():
                _, adj_pvals_arr, _, _ = multipletests(pvals_series[non_nan_idx].values, alpha=0.05, method='fdr_bh')
                results_df.loc[non_nan_idx, 'adj_pvalue'] = adj_pvals_arr
            else:
                results_df['adj_pvalue'] = np.nan
        else:
            results_df['adj_pvalue'] = np.nan
    else:
        results_df['adj_pvalue'] = np.nan

    # Add metadata
    results_df['analysis_type'] = 'main_effects'
    results_df['causality_claim'] = False
    results_df['correction_method'] = 'benjamini_hochberg'

    # Ensure output directory exists
    ensure_directories([output_path])

    # Save to Parquet
    results_df.to_parquet(output_path, index=False)
    logger.info(f"Saved main effects results to {output_path}")

    # Generate manifest/checksum
    checksum = compute_file_checksum(output_path)
    manifest = {
        'file': output_path,
        'checksum': checksum,
        'n_rows': len(results_df),
        'n_columns': len(results_df.columns),
        'timestamp': str(pd.Timestamp.now())
    }
    manifest_path = str(Path(output_path).with_suffix('.manifest.json'))
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Generated manifest at {manifest_path}")

    return results_df


def run_interaction_analysis(
    df: pd.DataFrame,
    outcome_col: str,
    predictor_col: str,
    interaction_col: str,
    confounders: List[str]
) -> Dict[str, Any]:
    """
    Fits an interaction model: outcome ~ predictor * interaction + confounders.
    This is a placeholder for T027 implementation, but included for API completeness.
    """
    # Implementation would go here
    raise NotImplementedError("Interaction analysis is scheduled for T027.")


def main():
    """
    Main entry point for running the analysis pipeline.
    Reads configuration from config.py and executes T021 logic.
    """
    logger.info("Starting Main Effects Analysis (T021)")

    try:
        # Load paths from config
        ilr_path = get_path('data', 'processed', 'ilr_coordinates.parquet')
        cog_path = get_path('data', 'processed', 'cohort_with_age_groups.parquet') # Or similar source
        output_path = get_path('results', 'associations', 'main_effects.parquet')
        
        # Define confounders based on T004 and FR-004
        # Assuming these are standard names; if T004 defines specific IDs, map them here
        confounders = ['age', 'sex', 'bmi', 'diet_score', 'activity_score', 'medication_count']
        
        # Validate inputs exist
        if not os.path.exists(ilr_path):
            raise FileNotFoundError(f"ILR data not found at {ilr_path}. Run preprocessing first.")
        if not os.path.exists(cog_path):
            raise FileNotFoundError(f"Cognitive data not found at {cog_path}. Run preprocessing first.")

        # Run analysis
        results = run_main_effects_analysis(
            ilr_data_path=ilr_path,
            cognitive_data_path=cog_path,
            confounder_cols=confounders,
            output_path=output_path
        )

        logger.info(f"Analysis complete. {len(results)} associations tested.")
        logger.info(f"Output saved to {output_path}")
        
        # Print summary
        significant = results[results['adj_pvalue'] < 0.05]
        logger.info(f"Significant associations (adj-p < 0.05): {len(significant)}")

    except Exception as e:
        logger.critical(f"Analysis failed: {e}")
        raise LlmXiveError(f"Analysis execution failed: {e}") from e


if __name__ == "__main__":
    main()
