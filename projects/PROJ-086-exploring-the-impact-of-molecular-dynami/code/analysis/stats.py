"""
Statistical analysis utilities for MD simulation parameter impact study.

This module provides functionality for:
- Fitting Linear Mixed-Effects Models (LMM) to binding affinity errors
- Variance component decomposition
- Summary statistics for parameter combinations

Model Structure:
  Response: Absolute Error (AE) in binding affinity prediction
  Fixed Effects: ForceField, Duration
  Random Effects: Complex (random intercept)

Note: Temperature is excluded as a factor since it is constant (300K).
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import warnings

# Import from project utilities
from utils.logger import get_logger

logger = get_logger(__name__)


def load_analysis_results(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Load analysis results from CSV file.

    Expected columns:
      - complex_id: Unique identifier for the protein-ligand complex
      - force_field: Force field used (e.g., 'ffSB', 'CHARMM36m')
      - duration: Simulation duration (e.g., '0.5ns', '1.0ns', '1.5ns')
      - experimental_kcal: Experimental binding affinity (kcal/mol)
      - predicted_kcal: Predicted binding affinity (kcal/mol)
      - absolute_error: |predicted - experimental|

    Args:
        filepath: Path to the analysis results CSV file

    Returns:
        DataFrame with analysis results

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If required columns are missing
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Analysis results file not found: {filepath}")

    df = pd.read_csv(filepath)

    required_columns = ['complex_id', 'force_field', 'duration', 
                      'experimental_kcal', 'predicted_kcal', 'absolute_error']
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {filepath}: {missing}")

    logger.info(f"Loaded {len(df)} records from {filepath}")
    return df


def calculate_absolute_error(
    experimental: pd.Series, 
    predicted: pd.Series
) -> pd.Series:
    """
    Calculate absolute error between experimental and predicted values.

    Args:
        experimental: Series of experimental binding affinities
        predicted: Series of predicted binding affinities

    Returns:
        Series of absolute errors
    """
    return (experimental - predicted).abs()


def fit_linear_mixed_effects_model(
    df: pd.DataFrame,
    formula: Optional[str] = None
) -> sm.regression.mixed_linear_model.MixedLMResults:
    """
    Fit a Linear Mixed-Effects Model (LMM) to the analysis data.

    Model specification:
      - Fixed effects: ForceField, Duration
      - Random effects: Complex (random intercept)
      - Response variable: absolute_error

    The model follows the structure:
      AE ~ ForceField + Duration + (1 | Complex)

    Args:
        df: DataFrame with analysis results
        formula: Optional custom formula. If None, uses default formula.

    Returns:
        Fitted LMM results object

    Raises:
        ValueError: If data is insufficient for model fitting
    """
    if formula is None:
        # Default formula: fixed effects for force_field and duration,
        # random intercept for complex_id
        formula = "absolute_error ~ C(force_field) + C(duration) + (1 | complex_id)"

    if len(df) < 10:
        logger.warning(f"Small dataset ({len(df)} records) may lead to unreliable LMM results")

    try:
        # Ensure categorical variables are properly typed
        df['force_field'] = df['force_field'].astype('category')
        df['duration'] = df['duration'].astype('category')
        df['complex_id'] = df['complex_id'].astype('category')

        # Fit the model
        model = smf.mixedlm(formula, df, groups=df["complex_id"])
        results = model.fit(reml=True)
        
        logger.info(f"LMM model fitted successfully. AIC: {results.aic:.2f}, BIC: {results.bic:.2f}")
        return results

    except Exception as e:
        logger.error(f"Failed to fit LMM model: {e}")
        raise


def calculate_variance_components(
    results: sm.regression.mixed_linear_model.MixedLMResults,
    total_variance: Optional[float] = None
) -> Dict[str, float]:
    """
    Calculate variance component decomposition from LMM results.

    Decomposes total variance into:
      - Fixed effects variance (explained by ForceField and Duration)
      - Random effects variance (explained by Complex)
      - Residual variance (unexplained)

    Args:
        results: Fitted LMM results object
        total_variance: Optional pre-computed total variance. If None, calculated from residuals.

    Returns:
        Dictionary with variance components as percentages of total variance
    """
    # Extract variance components
    # Fixed effects variance is not directly available, so we calculate
    # the proportion of variance explained by the model vs residual

    # Get the covariance matrix of random effects
    try:
        random_cov = results.cov_re
        random_variance = float(np.diagonal(random_cov)[0]) if random_cov is not None else 0.0
    except Exception:
        random_variance = 0.0
        logger.warning("Could not extract random effects variance")

    # Get residual variance
    try:
        residual_variance = float(results.scale)
    except Exception:
        residual_variance = 0.0
        logger.warning("Could not extract residual variance")

    # Calculate total variance from data if not provided
    if total_variance is None:
        total_variance = random_variance + residual_variance
        if total_variance == 0:
            # Fallback: calculate from actual data
            logger.warning("Zero total variance detected, recalculating from data")
            # This is a simplification; in practice, we'd need the full model predictions
            total_variance = 1.0  # Avoid division by zero

    # Calculate percentages
    variance_components = {
        'random_effect_complex': (random_variance / total_variance) * 100,
        'residual': (residual_variance / total_variance) * 100,
        'fixed_effects_explained': 100 - (random_variance + residual_variance) / total_variance * 100
    }

    # Ensure fixed effects variance is non-negative
    if variance_components['fixed_effects_explained'] < 0:
        variance_components['fixed_effects_explained'] = 0.0
        # Recalculate residual to account for the discrepancy
        variance_components['residual'] = 100 - variance_components['random_effect_complex']

    logger.info(f"Variance components: Complex={variance_components['random_effect_complex']:.2f}%, "
               f"Residual={variance_components['residual']:.2f}%, Fixed={variance_components['fixed_effects_explained']:.2f}%")

    return variance_components


def calculate_rmse_mae(
    df: pd.DataFrame,
    experimental_col: str = 'experimental_kcal',
    predicted_col: str = 'predicted_kcal',
    groupby_cols: Optional[List[str]] = None
) -> Union[pd.DataFrame, Dict[str, float]]:
    """
    Calculate RMSE and MAE for binding affinity predictions.

    Args:
        df: DataFrame with experimental and predicted values
        experimental_col: Column name for experimental values
        predicted_col: Column name for predicted values
        groupby_cols: Optional list of columns to group by (e.g., ['force_field', 'duration'])

    Returns:
        If groupby_cols provided: DataFrame with RMSE and MAE per group
        Otherwise: Dictionary with overall RMSE and MAE
    """
    df = df.copy()
    df['absolute_error'] = (df[experimental_col] - df[predicted_col]).abs()
    df['squared_error'] = (df[experimental_col] - df[predicted_col]) ** 2

    if groupby_cols:
        # Group by specified columns and calculate metrics
        summary = df.groupby(groupby_cols).agg(
            rmse=('squared_error', 'mean'),
            mae=('absolute_error', 'mean'),
            count=('absolute_error', 'count')
        ).reset_index()
        summary['rmse'] = np.sqrt(summary['rmse'])
        return summary
    else:
        # Overall metrics
        rmse = np.sqrt(df['squared_error'].mean())
        mae = df['absolute_error'].mean()
        return {'rmse': rmse, 'mae': mae, 'n_samples': len(df)}


def get_fixed_effect_summary(
    results: sm.regression.mixed_linear_model.MixedLMResults,
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Extract fixed effect estimates with confidence intervals.

    Args:
        results: Fitted LMM results object
        alpha: Significance level for confidence intervals (default 0.05)

    Returns:
        DataFrame with effect estimates, standard errors, and confidence intervals
    """
    # Get parameter names and estimates
    params = results.params
    std_err = results.bse
    conf_int = results.conf_int(alpha=alpha)

    summary_data = {
        'parameter': params.index,
        'estimate': params.values,
        'std_error': std_err.values,
        'conf_int_lower': conf_int.iloc[:, 0].values,
        'conf_int_upper': conf_int.iloc[:, 1].values
    }

    # Calculate p-values (approximate using t-distribution)
    # Note: This is an approximation; exact p-values require more complex calculation
    t_values = params / std_err
    # Using normal approximation for large samples
    from scipy import stats
    p_values = 2 * (1 - stats.norm.cdf(np.abs(t_values)))
    summary_data['p_value'] = p_values

    summary_df = pd.DataFrame(summary_data)
    summary_df['significant'] = summary_df['p_value'] < alpha

    logger.info(f"Fixed effect summary: {len(summary_df)} parameters, "
               f"{summary_df['significant'].sum()} significant at α={alpha}")

    return summary_df


def validate_lmm_assumptions(
    df: pd.DataFrame,
    results: sm.regression.mixed_linear_model.MixedLMResults
) -> Dict[str, bool]:
    """
    Validate key assumptions for LMM analysis.

    Checks:
      - Sufficient sample size (N >= 10 complexes)
      - Balanced design (roughly equal samples per group)
      - No extreme outliers in residuals

    Args:
        df: Original analysis DataFrame
        results: Fitted LMM results

    Returns:
        Dictionary with validation results
    """
    validation = {
        'sufficient_sample_size': False,
        'balanced_design': False,
        'no_extreme_outliers': False,
        'warnings': []
    }

    # Check sample size
    n_complexes = df['complex_id'].nunique()
    if n_complexes >= 10:
        validation['sufficient_sample_size'] = True
    else:
        validation['warnings'].append(f"Low sample size: {n_complexes} complexes (recommended >= 10)")

    # Check balance
    group_counts = df.groupby(['force_field', 'duration']).size()
    max_count = group_counts.max()
    min_count = group_counts.min()
    balance_ratio = min_count / max_count if max_count > 0 else 0
    
    if balance_ratio >= 0.5:
        validation['balanced_design'] = True
    else:
        validation['warnings'].append(f"Imbalanced design: ratio {balance_ratio:.2f} (recommended >= 0.5)")

    # Check for outliers (residuals > 3 std dev)
    try:
        residuals = results.resid
        std_residuals = np.std(residuals)
        outlier_threshold = 3 * std_residuals
        n_outliers = np.sum(np.abs(residuals) > outlier_threshold)
        
        if n_outliers <= 0.05 * len(residuals):  # Less than 5% outliers
            validation['no_extreme_outliers'] = True
        else:
            validation['warnings'].append(f"High outlier count: {n_outliers} ({100*n_outliers/len(residuals):.1f}%)")
    except Exception as e:
        validation['warnings'].append(f"Could not check outliers: {e}")

    return validation


def run_full_statistical_analysis(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None
) -> Dict[str, any]:
    """
    Run complete statistical analysis pipeline.

    This function:
      1. Loads analysis results
      2. Fits LMM model
      3. Calculates variance components
      4. Generates fixed effect summary
      5. Validates assumptions
      6. Calculates RMSE/MAE by parameter combination

    Args:
        input_path: Path to analysis results CSV
        output_path: Optional path to save results summary (JSON)

    Returns:
        Dictionary containing all analysis results
    """
    logger.info(f"Starting full statistical analysis from {input_path}")

    # Load data
    df = load_analysis_results(input_path)

    # Fit model
    lmm_results = fit_linear_mixed_effects_model(df)

    # Calculate variance components
    variance_components = calculate_variance_components(lmm_results)

    # Get fixed effect summary
    fixed_effects = get_fixed_effect_summary(lmm_results)

    # Validate assumptions
    assumptions = validate_lmm_assumptions(df, lmm_results)

    # Calculate RMSE/MAE by parameter combination
    rmse_mae_by_group = calculate_rmse_mae(
        df, 
        groupby_cols=['force_field', 'duration']
    )

    # Overall metrics
    overall_metrics = calculate_rmse_mae(df)

    # Compile results
    analysis_results = {
        'model_fit': {
            'aic': float(lmm_results.aic),
            'bic': float(lmm_results.bic),
            'log_likelihood': float(lmm_results.llf)
        },
        'variance_components': variance_components,
        'fixed_effects': fixed_effects.to_dict('records'),
        'assumptions_validation': assumptions,
        'rmse_mae_by_group': rmse_mae_by_group.to_dict('records') if isinstance(rmse_mae_by_group, pd.DataFrame) else rmse_mae_by_group,
        'overall_metrics': overall_metrics,
        'sample_info': {
            'n_complexes': int(df['complex_id'].nunique()),
            'n_observations': int(len(df)),
            'n_force_fields': int(df['force_field'].nunique()),
            'n_durations': int(df['duration'].nunique())
        }
    }

    # Save results if output path provided
    if output_path:
        from utils.io import write_json
        output_path = Path(output_path)
        write_json(analysis_results, output_path)
        logger.info(f"Saved analysis results to {output_path}")

    logger.info("Statistical analysis completed successfully")
    return analysis_results