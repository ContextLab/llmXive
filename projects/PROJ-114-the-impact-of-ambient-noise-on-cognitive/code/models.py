import logging
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.anova import anova_lm
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fit_linear_mixed_effects(df: pd.DataFrame, 
                             dependent_var: str = 'reaction_time', 
                             fixed_effects: list = None,
                             random_effects: str = '1 | participant_id',
                             formula: str = None) -> mixedlm.MixedLMResults:
    """
    Fit a linear mixed-effects model to test the relationship between noise levels 
    and cognitive flexibility.
    
    Parameters
    ----------
    df : pd.DataFrame
        Preprocessed dataset containing reaction times, noise metrics, and participant IDs.
    dependent_var : str, default 'reaction_time'
        Name of the dependent variable column.
    fixed_effects : list, optional
        List of fixed effect variable names. If None, uses default formula construction.
    random_effects : str, default '1 | participant_id'
        Random effects formula string (e.g., '1 | participant_id').
    formula : str, optional
        Custom formula string. If provided, overrides fixed_effects and random_effects.
        
    Returns
    -------
    statsmodels.regression.mixed_linear_model.MixedLMResults
        Fitted model results object.
        
    Raises
    ------
    ValueError
        If required columns are missing or model fails to converge.
    """
    if formula is None:
        if fixed_effects is None:
            # Default: avg_noise, noise_squared, variability, noise_level
            formula = f"{dependent_var} ~ avg_noise + I(avg_noise**2) + noise_variability + C(noise_level)"
        else:
            # Construct formula from list
            fe_str = " + ".join(fixed_effects)
            formula = f"{dependent_var} ~ {fe_str}"
    
    logger.info(f"Fitting LMM with formula: {formula}")
    logger.info(f"Random effects: {random_effects}")
    
    try:
        # Ensure categorical variables are treated as such
        if 'noise_level' in df.columns:
            df['noise_level'] = df['noise_level'].astype('category')
        if 'participant_id' in df.columns:
            df['participant_id'] = df['participant_id'].astype('category')
        
        model = mixedlm(formula, df, groups=df['participant_id'])
        result = model.fit(reml=False)
        
        if not result.converged:
            logger.warning("Model did not converge. Trying with different optimization settings...")
            result = model.fit(reml=False, method='bfgs', maxiter=1000)
            if not result.converged:
                logger.error("Model failed to converge after retry.")
                raise ValueError("Linear mixed-effects model did not converge.")
        
        logger.info(f"Model convergence: {result.converged}")
        logger.info(f"Log-likelihood: {result.llf}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error fitting linear mixed-effects model: {e}")
        raise

def likelihood_ratio_test(model_full, model_reduced) -> dict:
    """
    Perform a likelihood ratio test to compare nested models.
    Typically used to compare a model with a quadratic term vs. one without.
    
    Parameters
    ----------
    model_full : statsmodels.regression.mixed_linear_model.MixedLMResults
        The full model (e.g., with quadratic term).
    model_reduced : statsmodels.regression.mixed_linear_model.MixedLMResults
        The reduced model (e.g., without quadratic term).
        
    Returns
    -------
    dict
        Dictionary containing:
        - 'chi2_statistic': Likelihood ratio chi-square statistic
        - 'p_value': P-value from chi-square distribution
        - 'df_diff': Difference in degrees of freedom
        - 'significant': Boolean indicating if p < 0.05
    """
    ll_full = model_full.llf
    ll_reduced = model_reduced.llf
    
    # Chi-square statistic: -2 * (logLik_reduced - logLik_full)
    chi2_stat = -2 * (ll_reduced - ll_full)
    
    # Degrees of freedom difference
    df_full = len(model_full.params)
    df_reduced = len(model_reduced.params)
    df_diff = df_full - df_reduced
    
    if df_diff <= 0:
        raise ValueError("Full model must have more parameters than reduced model.")
    
    # Calculate p-value
    p_value = 1 - stats.chi2.cdf(chi2_stat, df_diff)
    
    result = {
        'chi2_statistic': chi2_stat,
        'p_value': p_value,
        'df_diff': df_diff,
        'significant': p_value < 0.05
    }
    
    logger.info(f"LRT Chi2: {chi2_stat:.4f}, p-value: {p_value:.4f}, df: {df_diff}")
    
    return result

def post_hoc_tukey_hsd(df: pd.DataFrame, 
                       dependent_var: str = 'reaction_time',
                       grouping_var: str = 'noise_level') -> tuple:
    """
    Perform Tukey's HSD post-hoc test for pairwise comparisons of noise levels.
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataset containing the dependent variable and grouping variable.
    dependent_var : str, default 'reaction_time'
        Name of the dependent variable column.
    grouping_var : str, default 'noise_level'
        Name of the categorical grouping variable (e.g., 'noise_level').
        
    Returns
    -------
    tuple
        (tukey_results, comparison_df)
        - tukey_results: statsmodels.stats.multicomp.TukeyHSDResults object
        - comparison_df: DataFrame with pairwise comparisons and p-values
    """
    logger.info(f"Running Tukey HSD for {grouping_var} on {dependent_var}")
    
    # Ensure grouping variable is categorical
    if grouping_var in df.columns:
        df[grouping_var] = df[grouping_var].astype('category')
    
    try:
        tukey = pairwise_tukeyhsd(endog=df[dependent_var], 
                                  groups=df[grouping_var], 
                                  alpha=0.05)
        
        # Convert results to DataFrame for easier handling
        comparison_df = tukey.summary_frame()
        
        logger.info(f"Tukey HSD completed. Found {len(comparison_df)} comparisons.")
        
        return tukey, comparison_df
        
    except Exception as e:
        logger.error(f"Error running Tukey HSD: {e}")
        raise

def apply_multiple_comparison_correction(comparison_df: pd.DataFrame, 
                                         method: str = 'fdr_bh',
                                         p_value_col: str = 'p-vals') -> pd.DataFrame:
    """
    Apply multiple comparison correction to pairwise comparison p-values.
    
    Parameters
    ----------
    comparison_df : pd.DataFrame
        DataFrame containing pairwise comparison results, typically from Tukey HSD.
    method : str, default 'fdr_bh'
        Correction method: 'fdr_bh' (Benjamini-Hochberg), 'bonferroni', 'holm', etc.
    p_value_col : str, default 'p-vals'
        Name of the column containing raw p-values.
        
    Returns
    -------
    pd.DataFrame
        DataFrame with an additional column for corrected p-values.
    """
    from statsmodels.stats.multitest import multipletests
    
    if p_value_col not in comparison_df.columns:
        raise ValueError(f"Column '{p_value_col}' not found in comparison_df. "
                       f"Available columns: {list(comparison_df.columns)}")
    
    raw_pvalues = comparison_df[p_value_col].values
    
    # Apply correction
    # multipletests returns: (reject, pvals_corrected, pvals_corrected_rej, alphacSidak, alphacBonf)
    reject, corrected_pvalues, _, _ = multipletests(raw_pvalues, 
                                                    alpha=0.05, 
                                                    method=method)
    
    # Add corrected p-values to DataFrame
    corrected_col_name = f'pvals_{method}'
    comparison_df[corrected_col_name] = corrected_pvalues
    comparison_df[f'reject_{method}'] = reject
    
    logger.info(f"Applied {method} correction. {sum(reject)} comparisons remain significant.")
    
    return comparison_df