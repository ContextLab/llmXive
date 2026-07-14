import logging
import warnings
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def calculate_min_max_regret(df: pd.DataFrame, option_col: str = 'option_id', value_col: str = 'utility') -> pd.DataFrame:
    """
    Calculate Min-Max Regret (Opportunity Cost) proxy.
    
    For each decision context (group), regret is defined as the difference
    between the maximum possible utility in that context and the utility of the chosen option.
    
    Args:
        df: DataFrame containing decision context data.
        option_col: Column name for option identifier.
        value_col: Column name for utility/value of the option.
        
    Returns:
        DataFrame with added 'regret_proxy' column.
    """
    if df.empty:
        return df
        
    # Group by decision context (assumed to be the index or a specific context ID if present)
    # If no context ID, we assume rows are already grouped or we group by a 'context_id' if it exists.
    # For this implementation, we assume the input df has a 'context_id' column or we treat the whole df as one batch if not.
    # However, standard practice for regret is per-decision-event.
    # Let's assume 'context_id' exists. If not, we group by an index level or a synthetic ID.
    
    if 'context_id' not in df.columns:
        # Fallback: If no context_id, we cannot calculate regret across options within a choice set.
        # We assume the input is already filtered to choice sets or we raise an error.
        # For robustness, we'll create a synthetic context if missing, but log a warning.
        logger.warning("No 'context_id' found. Assuming each row is its own context (Regret=0).")
        df['regret_proxy'] = 0.0
        return df

    def calc_regret(group: pd.DataFrame) -> pd.Series:
        if len(group) <= 1:
            # Single option: Regret is 0 (per FR-002 and T011)
            return pd.Series([0.0] * len(group), index=group.index)
        
        max_util = group[value_col].max()
        # Regret = Max Utility - Chosen Utility
        regret = max_util - group[value_col]
        return regret

    df['regret_proxy'] = df.groupby('context_id').apply(calc_regret).reset_index(level=0, drop=True)
    return df


def calculate_sd_normalized_eu(df: pd.DataFrame, option_col: str = 'option_id', value_col: str = 'utility') -> pd.DataFrame:
    """
    Calculate Standard Deviation of Normalized EU (Spec-mandated alternative).
    This is for comparison purposes only, not the primary proxy.
    """
    if df.empty:
        return df
        
    if 'context_id' not in df.columns:
        df['sd_eu_proxy'] = 0.0
        return df

    def calc_sd(group: pd.DataFrame) -> pd.Series:
        if len(group) <= 1:
            return pd.Series([0.0] * len(group), index=group.index)
        
        # Normalize EU within context (0 to 1)
        utils = group[value_col].values
        utils_min, utils_max = utils.min(), utils.max()
        
        if utils_max == utils_min:
            normalized = np.zeros_like(utils)
        else:
            normalized = (utils - utils_min) / (utils_max - utils_min)
        
        sd_val = np.std(normalized)
        return pd.Series([sd_val] * len(group), index=group.index)

    df['sd_eu_proxy'] = df.groupby('context_id').apply(calc_sd).reset_index(level=0, drop=True)
    return df


def calculate_potential_loss_magnitude(df: pd.DataFrame, value_col: str = 'utility') -> pd.DataFrame:
    """
    Calculate Potential Loss Magnitude (Max possible loss) independent of regret.
    This is used to control for loss aversion.
    """
    if df.empty:
        return df
        
    if 'context_id' not in df.columns:
        df['potential_loss_magnitude'] = 0.0
        return df

    def calc_loss(group: pd.DataFrame) -> pd.Series:
        if len(group) <= 1:
            return pd.Series([0.0] * len(group), index=group.index)
        
        # Max possible loss is the range of utilities in the context
        # (Best case - Worst case)
        loss = group[value_col].max() - group[value_col].min()
        return pd.Series([loss] * len(group), index=group.index)

    df['potential_loss_magnitude'] = df.groupby('context_id').apply(calc_loss).reset_index(level=0, drop=True)
    return df


def add_regret_and_loss_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add both regret_proxy and potential_loss_magnitude to the dataframe.
    """
    df = calculate_min_max_regret(df)
    df = calculate_potential_loss_magnitude(df)
    return df


def compute_regret_loss_correlation(df: pd.DataFrame) -> float:
    """
    Compute correlation between regret_proxy and potential_loss_magnitude.
    Returns 0.0 if either column is missing or variance is zero.
    """
    if 'regret_proxy' not in df.columns or 'potential_loss_magnitude' not in df.columns:
        logger.warning("Missing regret_proxy or potential_loss_magnitude columns for correlation check.")
        return 0.0
        
    corr, _ = stats.pearsonr(df['regret_proxy'], df['potential_loss_magnitude'])
    return float(corr)


def calculate_price_variance_proxy(df: pd.DataFrame, price_col: str = 'price') -> pd.DataFrame:
    """
    Calculate price variance as a proxy for perceived risk.
    This is used as a fallback when 'perceived_risk' scores are missing.
    """
    if df.empty:
        return df
        
    if 'context_id' not in df.columns:
        df['price_variance'] = 0.0
        return df

    def calc_var(group: pd.DataFrame) -> pd.Series:
        if len(group) <= 1:
            return pd.Series([0.0] * len(group), index=group.index)
        
        var_val = group[price_col].var()
        return pd.Series([var_val] * len(group), index=group.index)

    df['price_variance'] = df.groupby('context_id').apply(calc_var).reset_index(level=0, drop=True)
    return df


def validate_regret_proxy_single_option(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure regret_proxy is 0 when only one option exists (per FR-002).
    This is a validation step that enforces the logic already in calculate_min_max_regret,
    but explicitly checks and corrects if necessary.
    """
    if 'context_id' not in df.columns:
        return df
        
    # Count options per context
    option_counts = df.groupby('context_id').size()
    single_option_contexts = option_counts[option_counts == 1].index
    
    if len(single_option_contexts) > 0:
        logger.info(f"Enforcing regret=0 for {len(single_option_contexts)} contexts with single option.")
        df.loc[df['context_id'].isin(single_option_contexts), 'regret_proxy'] = 0.0
        
    return df


def add_perceived_risk_covariate(df: pd.DataFrame, price_col: str = 'price') -> pd.DataFrame:
    """
    T018 Implementation: Fallback logic for 'perceived_risk' covariate.
    
    If 'perceived_risk' column is missing, calculate 'price_variance' and 
    use it as the 'perceived_risk' covariate in the model formula.
    
    Args:
        df: Input DataFrame.
        price_col: Column name for price data.
        
    Returns:
        DataFrame with 'perceived_risk' column populated (either from existing or calculated).
    """
    if 'perceived_risk' not in df.columns:
        logger.info("Column 'perceived_risk' missing. Calculating fallback 'price_variance' as covariate.")
        df = calculate_price_variance_proxy(df, price_col=price_col)
        # Rename the calculated variance to the expected covariate name
        df['perceived_risk'] = df['price_variance']
        logger.info("Fallback 'perceived_risk' assigned from price_variance.")
    else:
        logger.info("Column 'perceived_risk' already present. Using existing values.")
        
    return df
