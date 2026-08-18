"""
Multiple Imputation (MICE) implementation for Regression Discontinuity designs.

Uses statsmodels.imputation.mice with Rubin's rules for pooling.
Predictors: X (running variable), Z (covariate), D (treatment indicator).
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
import statsmodels.api as sm
from statsmodels.imputation.mice import MICEData, MICE
from src.logging_config import get_logger

logger = get_logger(__name__)

def estimate_multiple_imputation(
    data: pd.DataFrame,
    true_effect: float,
    m: int = 5,
    max_iter: int = 20,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Estimate RD treatment effect using Multiple Imputation (MICE).
    
    Args:
        data: DataFrame with columns ['Y', 'X', 'Z', 'D']. Y may contain NaN.
        true_effect: Ground truth treatment effect for bias calculation.
        m: Number of imputations (default 5).
        max_iter: Maximum iterations for MICE convergence (default 20).
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary with keys:
            - 'estimate': Pooled treatment effect estimate
            - 'se': Standard error of the pooled estimate
            - 'bias': Estimate - true_effect
            - 'n_obs': Number of observations used
            - 'n_imputed': Number of imputations performed
            - 'converged': Boolean indicating if MICE converged
            - 'method': 'MICE'
    """
    logger.info(f"Starting MICE estimation with m={m} imputations")
    
    # Ensure required columns exist
    required_cols = ['Y', 'X', 'Z', 'D']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")
    
    # Handle case where Y is completely missing
    if data['Y'].isna().all():
        logger.warning("Y is completely missing; cannot perform estimation")
        return {
            'estimate': np.nan,
            'se': np.nan,
            'bias': np.nan,
            'n_obs': len(data),
            'n_imputed': 0,
            'converged': False,
            'method': 'MICE'
        }
    
    # Set seed for reproducibility
    if seed is not None:
        np.random.seed(seed)
    
    try:
        # Prepare data for MICE
        # MICE requires a DataFrame with at least one column to impute
        df_mice = data.copy()
        
        # Initialize MICEData
        mice_data = MICEData(df_mice, seed=seed if seed else 42)
        
        # Run MICE with default settings
        # The formula for Y is automatically determined based on other columns
        # We specify the model for the outcome Y
        model = MICE(
            "Y ~ X + Z + D",
            data=mice_data,
            missing_data="Y"
        )
        
        # Fit the model with multiple imputations
        result = model.fit(maxiter=max_iter)
        
        # Extract pooled estimates using Rubin's rules (handled internally by MICE)
        # The fitted result contains the pooled estimates
        pooled_params = result.params
        pooled_se = result.bse
        
        # The treatment effect is the coefficient for D
        if 'D' in pooled_params.index:
            estimate = pooled_params['D']
            se = pooled_se['D']
        else:
            # Fallback if D is not in the model (should not happen)
            logger.warning("Treatment indicator D not found in pooled parameters")
            estimate = np.nan
            se = np.nan
        
        # Check convergence
        # MICE result has a 'converged' attribute if available, otherwise check iteration count
        converged = result.niter < max_iter or hasattr(result, 'converged') and result.converged
        
        bias = estimate - true_effect if not np.isnan(estimate) else np.nan
        
        logger.info(f"MICE completed: estimate={estimate:.4f}, se={se:.4f}, bias={bias:.4f}, converged={converged}")
        
        return {
            'estimate': estimate,
            'se': se,
            'bias': bias,
            'n_obs': len(data),
            'n_imputed': m,
            'converged': converged,
            'method': 'MICE'
        }
        
    except Exception as e:
        logger.error(f"MICE estimation failed: {str(e)}")
        return {
            'estimate': np.nan,
            'se': np.nan,
            'bias': np.nan,
            'n_obs': len(data),
            'n_imputed': 0,
            'converged': False,
            'method': 'MICE',
            'error': str(e)
        }

def main():
    """
    Standalone runner for testing MICE implementation.
    Generates sample data, applies missingness, and runs MICE.
    """
    import sys
    import os
    from pathlib import Path
    
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from src.generators.rd_data import generate_rd_data
    from src.generators.missingness import apply_mcar_mask
    from src.config_loader import load_simulation_config, load_missingness_config
    
    # Load configurations
    sim_config = load_simulation_config()
    missing_config = load_missingness_config()
    
    print("Generating synthetic RD data...")
    data = generate_rd_data(sim_config)
    
    print(f"Generated {len(data)} observations")
    print(f"True effect: {sim_config.true_effect}")
    
    # Apply MCAR missingness for demonstration
    print("Applying MCAR missingness...")
    missingness_rate = missing_config.get('mcar', {}).get('rate', 0.2)
    data_with_missing = apply_mcar_mask(data, rate=missingness_rate)
    
    print(f"Missingness rate: {data_with_missing['Y'].isna().mean():.2%}")
    
    # Run MICE
    print("Running MICE estimation...")
    result = estimate_multiple_imputation(
        data_with_missing,
        true_effect=sim_config.true_effect,
        m=5,
        max_iter=20,
        seed=42
    )
    
    print("\nMICE Results:")
    print(f"  Estimate: {result['estimate']:.4f}")
    print(f"  Std Error: {result['se']:.4f}")
    print(f"  Bias: {result['bias']:.4f}")
    print(f"  Converged: {result['converged']}")
    
    return result

if __name__ == "__main__":
    main()
