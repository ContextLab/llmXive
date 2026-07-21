import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Optional, Tuple
from src.logging_config import get_logger
from src.generators.rd_data import generate_rd_data

logger = get_logger(__name__)

def apply_mcar_mask(df: pd.DataFrame, rate: float, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Apply MCAR (Missing Completely At Random) mask.
    Mask generation is independent of all variables.
    """
    if seed is not None:
        np.random.seed(seed)
    
    n = len(df)
    # Bernoulli trial: 1 = missing, 0 = observed
    # We want 'rate' to be the probability of missingness
    mask = np.random.binomial(1, rate, size=n) == 1
    
    df = df.copy()
    df['Y_missing'] = mask
    return df

def apply_mar_mask(df: pd.DataFrame, rate: float, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Apply MAR (Missing At Random) mask.
    Mask generation depends on covariate Z via logistic regression.
    """
    if seed is not None:
        np.random.seed(seed)
    
    n = len(df)
    Z = df['Z'].values
    
    # Logistic regression: P(missing) = 1 / (1 + exp(-(beta0 + beta1*Z)))
    # We want to target a specific rate. We'll adjust beta0 to hit the rate.
    # First, generate logits with some slope
    beta1 = 1.0
    logits = beta1 * Z
    
    # Find beta0 such that the mean probability is close to rate
    # We can use a simple numerical search or approximation
    # For simplicity, we'll use a linear approximation of the logit function around 0
    # logit(rate) ~ beta0 + beta1 * mean(Z)
    # Since mean(Z) ~ 0, beta0 ~ logit(rate)
    from math import log
    if 0 < rate < 1:
        beta0 = log(rate / (1 - rate))
    else:
        beta0 = 0.0
        
    logits = beta0 + beta1 * Z
    probs = 1 / (1 + np.exp(-logits))
    
    # Generate mask based on probabilities
    mask = np.random.binomial(1, probs, size=n) == 1
    
    df = df.copy()
    df['Y_missing'] = mask
    return df

def apply_mnar_mask(df: pd.DataFrame, rate: float, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Apply MNAR (Missing Not At Random) mask.
    Mask generation depends on outcome Y via probit link.
    """
    if seed is not None:
        np.random.seed(seed)
    
    n = len(df)
    Y = df['Y'].values
    
    # Probit link: P(missing) = Phi(beta0 + beta1*Y)
    # We want to target a specific rate.
    beta1 = 0.5
    linear_comb = beta1 * Y
    
    # Find beta0 such that mean(Phi(linear_comb + beta0)) ~ rate
    # Use numerical approximation: Phi(beta0) ~ rate if Y is standardized
    # Since Y is not necessarily standardized, we'll use a simple search
    # Or approximate: if Y is roughly normal, then beta0 ~ Phi^{-1}(rate)
    from scipy.stats import norm
    if 0 < rate < 1:
        beta0 = norm.ppf(rate)
    else:
        beta0 = 0.0
        
    linear_comb = beta0 + beta1 * Y
    probs = norm.cdf(linear_comb)
    
    # Generate mask based on probabilities
    mask = np.random.binomial(1, probs, size=n) == 1
    
    df = df.copy()
    df['Y_missing'] = mask
    return df

def generate_missingness_pattern(df: pd.DataFrame, mechanism: str, rate: float, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Generate missingness pattern based on mechanism.
    """
    if mechanism == 'MCAR':
        return apply_mcar_mask(df, rate, seed)
    elif mechanism == 'MAR':
        return apply_mar_mask(df, rate, seed)
    elif mechanism == 'MNAR':
        return apply_mnar_mask(df, rate, seed)
    else:
        raise ValueError(f"Unknown mechanism: {mechanism}")

def validate_missingness_pattern(df: pd.DataFrame, mechanism: str) -> Tuple[bool, float, str]:
    """
    Validate that the missingness pattern matches the theoretical definition.
    
    Returns:
        Tuple of (is_valid, p_value, message)
        
    Validation logic:
        - MCAR: Chi-square test for independence between missingness and (X, Z, D, Y).
          Expect p > 0.05 (no dependence).
        - MAR: Correlation between missingness and Z (covariate).
          Expect p < 0.05 (dependence on Z).
        - MNAR: Correlation between missingness and Y (outcome).
          Expect p < 0.05 (dependence on Y).
    """
    if 'Y_missing' not in df.columns:
        return False, 0.0, "No missingness mask found in dataframe"
    
    mask = df['Y_missing'].values.astype(int)
    
    if mechanism == 'MCAR':
        # Test independence between mask and all other variables
        # We'll use Chi-square for categorical or correlation for continuous
        # Since X, Z, D, Y are continuous/binary, we'll use point-biserial correlation
        # and check if all are insignificant (p > 0.05)
        
        variables_to_check = ['X', 'Z', 'D', 'Y']
        all_independent = True
        min_p = 1.0
        
        for var in variables_to_check:
            if var not in df.columns:
                continue
            
            # Point-biserial correlation (equivalent to Pearson for binary vs continuous)
            corr, p_val = stats.pointbiserialr(mask, df[var].values)
            
            if p_val < 0.05:
                all_independent = False
            min_p = min(min_p, p_val)
        
        if all_independent:
            return True, min_p, f"MCAR validation passed: all p-values >= 0.05 (min p={min_p:.4f})"
        else:
            return False, min_p, f"MCAR validation FAILED: some variables show dependence (min p={min_p:.4f})"
            
    elif mechanism == 'MAR':
        # MAR: Missingness should depend on Z (covariate)
        # We expect a significant correlation (p < 0.05)
        if 'Z' not in df.columns:
            return False, 0.0, "Z variable not found for MAR validation"
        
        corr, p_val = stats.pointbiserialr(mask, df['Z'].values)
        
        if p_val < 0.05:
            return True, p_val, f"MAR validation passed: significant correlation with Z (p={p_val:.4f})"
        else:
            return False, p_val, f"MAR validation FAILED: no significant correlation with Z (p={p_val:.4f})"
            
    elif mechanism == 'MNAR':
        # MNAR: Missingness should depend on Y (outcome)
        # We expect a significant correlation (p < 0.05)
        if 'Y' not in df.columns:
            return False, 0.0, "Y variable not found for MNAR validation"
        
        corr, p_val = stats.pointbiserialr(mask, df['Y'].values)
        
        if p_val < 0.05:
            return True, p_val, f"MNAR validation passed: significant correlation with Y (p={p_val:.4f})"
        else:
            return False, p_val, f"MNAR validation FAILED: no significant correlation with Y (p={p_val:.4f})"
    else:
        return False, 0.0, f"Unknown mechanism: {mechanism}"

def main():
    """
    Main function to demonstrate missingness pattern generation and validation.
    This script generates RD data, applies missingness, and validates the pattern.
    """
    import sys
    from src.config_loader import load_simulation_config, load_missingness_config
    from src.generators.rd_data import generate_rd_data
    
    # Load configurations
    sim_config = load_simulation_config()
    miss_config = load_missingness_config()
    
    logger.info(f"Starting missingness pattern generation and validation")
    logger.info(f"Simulation config: {sim_config}")
    logger.info(f"Missingness config: {miss_config}")
    
    # Generate RD data
    df = generate_rd_data(sim_config)
    logger.info(f"Generated RD data with {len(df)} rows")
    
    # Get parameters from config
    mechanism = miss_config.get('mechanism', 'MCAR')
    rate = miss_config.get('rate', 0.2)
    seed = miss_config.get('seed', 42)
    
    logger.info(f"Applying {mechanism} missingness at rate {rate}")
    
    # Apply missingness
    df_with_mask = generate_missingness_pattern(df, mechanism, rate, seed)
    
    # Validate the pattern
    is_valid, p_val, message = validate_missingness_pattern(df_with_mask, mechanism)
    
    logger.info(message)
    
    if not is_valid:
        logger.error(f"Validation failed for {mechanism} mechanism. Failing simulation.")
        # Save the data for inspection
        output_path = "data/simulated_raw_with_validation.csv"
        df_with_mask.to_csv(output_path, index=False)
        logger.info(f"Saved data with failed validation to {output_path}")
        sys.exit(1)
    else:
        logger.info(f"Validation successful for {mechanism} mechanism.")
        # Save the data
        output_path = "data/simulated_raw_with_validation.csv"
        df_with_mask.to_csv(output_path, index=False)
        logger.info(f"Saved validated data to {output_path}")
    
    return is_valid

if __name__ == "__main__":
    main()
