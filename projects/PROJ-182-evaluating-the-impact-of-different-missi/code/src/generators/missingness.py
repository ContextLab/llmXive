import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Optional, Tuple
from src.logging_config import get_logger
from src.generators.rd_data import generate_rd_data

logger = get_logger(__name__)

def apply_mcar_mask(df: pd.DataFrame, rate: float, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Apply Missing Completely At Random (MCAR) mask.
    Mask is independent of all variables.
    """
    if seed is not None:
        np.random.seed(seed)
    
    n = len(df)
    mask = np.random.random(n) > rate
    df_masked = df.copy()
    df_masked['Y'] = df_masked['Y'].where(mask)
    
    logger.info(f"Applied MCAR mask with rate {rate:.2f}. Missing: {n - mask.sum()}")
    return df_masked

def apply_mar_mask(df: pd.DataFrame, rate: float, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Apply Missing At Random (MAR) mask based on covariate Z.
    Uses logistic regression to generate mask probabilities.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Normalize Z to keep probabilities reasonable
    z = df['Z'].values
    z_centered = z - np.mean(z)
    
    # Logistic link: p = 1 / (1 + exp(-(a + b*z)))
    # We tune 'a' to get approximately the target rate
    # p = 1 / (1 + exp(-a)) => a = -log(1/p - 1)
    # But we want variation, so we add slope
    
    # Simple approach: shift probability to match target rate on average
    # p(z) = rate + alpha * z (clipped to [0,1])
    # Better: use logistic function
    
    # Try to find intercept such that mean(p) approx rate
    # Let p(z) = 1 / (1 + exp(-(beta0 + beta1*z)))
    # We set beta1 small to have variation, solve for beta0
    beta1 = 0.5
    # Mean of z is 0, so mean(p) ~ 1/(1+exp(-beta0))
    # We want 1/(1+exp(-beta0)) = rate => beta0 = -log(1/rate - 1)
    if rate <= 0 or rate >= 1:
        raise ValueError("Rate must be between 0 and 1")
    beta0 = -np.log(1/rate - 1)
    
    logits = beta0 + beta1 * z_centered
    probs = 1 / (1 + np.exp(-logits))
    
    # Apply mask: observed if u > prob
    u = np.random.random(len(df))
    mask = u > probs
    
    df_masked = df.copy()
    df_masked['Y'] = df_masked['Y'].where(mask)
    
    logger.info(f"Applied MAR mask (via Z) with target rate {rate:.2f}. Actual missing: {n - mask.sum()}")
    return df_masked

def apply_mnar_mask(df: pd.DataFrame, rate: float, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Apply Missing Not At Random (MNAR) mask based on outcome Y.
    Uses probit link on Y to generate mask.
    """
    if seed is not None:
        np.random.seed(seed)
    
    y = df['Y'].values
    y_centered = y - np.mean(y)
    
    # Probit link: p = Phi(beta0 + beta1 * y)
    # We want mean(p) approx rate
    # Since y is centered, mean(p) ~ Phi(beta0)
    # beta0 = Phi^{-1}(rate)
    beta1 = 0.5
    beta0 = stats.norm.ppf(rate)
    
    z_scores = beta0 + beta1 * y_centered
    probs = stats.norm.cdf(z_scores)
    
    # Apply mask
    u = np.random.random(len(df))
    mask = u > probs
    
    df_masked = df.copy()
    df_masked['Y'] = df_masked['Y'].where(mask)
    
    logger.info(f"Applied MNAR mask (via Y) with target rate {rate:.2f}. Actual missing: {n - mask.sum()}")
    return df_masked

def validate_missingness_pattern(df: pd.DataFrame, mechanism: str, rate: float, alpha: float = 0.05) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the missingness pattern matches the theoretical definition.
    
    Args:
        df: DataFrame with 'Y' column (some NaN) and 'X', 'Z' columns.
        mechanism: One of 'MCAR', 'MAR', 'MNAR'.
        rate: Target missingness rate.
        alpha: Significance level for tests.
    
    Returns:
        (success, details): success is True if validation passes, details contains p-values.
    
    Raises:
        ValueError: If validation fails (p-value threshold not met).
    """
    mask = df['Y'].notna().values
    missing = ~mask
    n = len(df)
    
    if mechanism == 'MCAR':
        # Test independence between missingness and X, Z
        # Chi-square test of independence for categorical (discretized) or correlation for continuous
        # Since X, Z are continuous, we can use point-biserial correlation or ANOVA
        # Here we use Pearson correlation for simplicity (treat missing as 0/1)
        
        r_x, p_x = stats.pearsonr(mask, df['X'].values)
        r_z, p_z = stats.pearsonr(mask, df['Z'].values)
        
        details = {'p_X': p_x, 'p_Z': p_z, 'r_X': r_x, 'r_Z': r_z}
        
        # MCAR success: p > alpha for both (no dependence)
        if p_x < alpha or p_z < alpha:
            logger.error(f"MCAR validation FAILED: p_X={p_x:.4f}, p_Z={p_z:.4f}. Expected p > {alpha}.")
            raise ValueError(f"MCAR validation failed: p_X={p_x:.4f}, p_Z={p_z:.4f}. Expected p > {alpha} for independence.")
        
        logger.info(f"MCAR validation PASSED: p_X={p_x:.4f}, p_Z={p_z:.4f} (both > {alpha}).")
        return True, details
    
    elif mechanism == 'MAR':
        # MAR: dependent on Z, independent of Y (but Y is partially missing, so we check dependence on Z)
        # We expect significant correlation between missingness and Z
        r_z, p_z = stats.pearsonr(mask, df['Z'].values)
        
        details = {'p_Z': p_z, 'r_Z': r_z}
        
        # MAR success: p < alpha (dependence on Z)
        if p_z >= alpha:
            logger.error(f"MAR validation FAILED: p_Z={p_z:.4f}. Expected p < {alpha} for dependence on Z.")
            raise ValueError(f"MAR validation failed: p_Z={p_z:.4f}. Expected p < {alpha} for dependence on Z.")
        
        logger.info(f"MAR validation PASSED: p_Z={p_z:.4f} (< {alpha}).")
        return True, details
    
    elif mechanism == 'MNAR':
        # MNAR: dependent on Y (observed part)
        # We check correlation between missingness and observed Y
        # Note: This is a bit circular, but we check if missingness correlates with Y values
        # We can use the observed Y to compute correlation
        obs_y = df['Y'].dropna().values
        obs_mask = df['Y'].notna().values[~df['Y'].isna()] # This is all True for observed
        # Actually, we need to check if the probability of missingness depends on Y.
        # A simple test: split observed Y into two groups (high/low) and check missingness rate?
        # Better: use the full Y (imputed or just observed) and check correlation with missingness indicator.
        # But Y is missing, so we can only use observed Y.
        # Alternative: check if the mean of observed Y differs from expected? 
        # Standard approach: correlation between missingness indicator and Y (using observed Y for calculation, but missingness is 0/1).
        # We compute correlation between 'Y' (with NaN) and 'missing' indicator. 
        # Pandas pearsonr ignores NaN, so it uses observed pairs.
        
        r_y, p_y = stats.pearsonr(df['Y'].values, missing.astype(float))
        
        details = {'p_Y': p_y, 'r_Y': r_y}
        
        # MNAR success: p < alpha (dependence on Y)
        if p_y >= alpha:
            logger.error(f"MNAR validation FAILED: p_Y={p_y:.4f}. Expected p < {alpha} for dependence on Y.")
            raise ValueError(f"MNAR validation failed: p_Y={p_y:.4f}. Expected p < {alpha} for dependence on Y.")
        
        logger.info(f"MNAR validation PASSED: p_Y={p_y:.4f} (< {alpha}).")
        return True, details
    
    else:
        raise ValueError(f"Unknown mechanism: {mechanism}")

def generate_missingness_pattern(
    sample_size: int,
    true_effect: float,
    seed: int,
    mechanism: str,
    rate: float,
    exclusion_restriction: float = 0.0
) -> pd.DataFrame:
    """
    Generate RD data and apply missingness pattern.
    """
    df = generate_rd_data(sample_size, true_effect, seed, exclusion_restriction=exclusion_restriction)
    
    if mechanism == 'MCAR':
        return apply_mcar_mask(df, rate, seed)
    elif mechanism == 'MAR':
        return apply_mar_mask(df, rate, seed)
    elif mechanism == 'MNAR':
        return apply_mnar_mask(df, rate, seed)
    else:
        raise ValueError(f"Unknown mechanism: {mechanism}")

def main():
    """
    CLI entry point for testing missingness generation and validation.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Test missingness generation and validation")
    parser.add_argument('--mechanism', type=str, required=True, choices=['MCAR', 'MAR', 'MNAR'])
    parser.add_argument('--rate', type=float, default=0.2)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--n', type=int, default=1000)
    parser.add_argument('--true-effect', type=float, default=1.0)
    args = parser.parse_args()
    
    try:
        df = generate_missingness_pattern(
            sample_size=args.n,
            true_effect=args.true_effect,
            seed=args.seed,
            mechanism=args.mechanism,
            rate=args.rate
        )
        success, details = validate_missingness_pattern(df, args.mechanism, args.rate)
        print(f"Validation successful for {args.mechanism}. Details: {details}")
    except ValueError as e:
        print(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
