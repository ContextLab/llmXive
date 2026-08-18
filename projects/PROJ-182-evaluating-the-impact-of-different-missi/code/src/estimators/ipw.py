"""
Inverse-Probability Weighting (IPW) estimator for Regression Discontinuity.

Implements IPW using logistic regression on observed data only (X, Z, D).
The estimator weights complete cases by the inverse of their propensity score
(probability of being observed) to correct for missingness bias.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import Binomial
from src.logging_config import get_logger

logger = get_logger(__name__)


def estimate_ipw(
    data: pd.DataFrame,
    true_effect: float,
    bandwidth: Optional[float] = None,
    kernel: str = "triangular"
) -> Dict[str, Any]:
    """
    Estimate the RD treatment effect using Inverse-Probability Weighting.

    This method:
    1. Filters data to the local bandwidth around the cutoff (X=0).
    2. Fits a logistic regression model (Propensity Score) on observed data:
       R ~ X + Z + D (where R is the missingness indicator, 1=observed).
    3. Calculates weights w = 1 / P(R=1 | X, Z, D).
    4. Performs a weighted local-linear regression of Y on X and D using weights w.

    Args:
        data: DataFrame with columns ['X', 'Y', 'Z', 'D', 'R'] where R is 1 if observed.
        true_effect: Ground truth effect (used for metric calculation).
        bandwidth: Optional bandwidth for local regression. If None, uses a default.
        kernel: Kernel function name (not used in weighted OLS directly but kept for API consistency).

    Returns:
        Dict containing 'estimate', 'se', 'n_obs', 'n_effective', 'converged', 'method'.
    """
    # Validate inputs
    required_cols = {'X', 'Y', 'Z', 'D', 'R'}
    if not required_cols.issubset(data.columns):
        missing = required_cols - set(data.columns)
        raise ValueError(f"IPW estimator requires columns: {missing}")

    # Filter to local bandwidth
    # Default bandwidth: 0.5 * (max(X) - min(X)) if not provided, similar to naive
    if bandwidth is None:
        x_range = data['X'].max() - data['X'].min()
        bandwidth = 0.5 * x_range
        if bandwidth < 0.05 * x_range:
            bandwidth = 0.05 * x_range  # Floor per plan

    local_data = data[np.abs(data['X']) <= bandwidth].copy()

    if len(local_data) < 10:
        logger.warning(f"IPW: Insufficient observations in bandwidth ({len(local_data)}). Returning NaN.")
        return {
            'estimate': np.nan,
            'se': np.nan,
            'n_obs': len(local_data),
            'n_effective': 0,
            'converged': False,
            'method': 'IPW',
            'error': 'Insufficient data in bandwidth'
        }

    # Separate observed and missing
    observed = local_data[local_data['R'] == 1]

    if len(observed) < 5:
        logger.warning(f"IPW: Insufficient observed data ({len(observed)}) to fit propensity model.")
        return {
            'estimate': np.nan,
            'se': np.nan,
            'n_obs': len(local_data),
            'n_effective': len(observed),
            'converged': False,
            'method': 'IPW',
            'error': 'Insufficient observed data'
        }

    # 1. Fit Propensity Score Model: P(R=1 | X, Z, D)
    # Features: X, Z, D (and optionally interaction X*D if needed, but plan says X, Z, D)
    X_features = observed[['X', 'Z', 'D']]
    y_features = observed['R']

    # Add constant for intercept
    X_design = sm.add_constant(X_features)

    try:
        # Use GLM with Binomial family for logistic regression
        model = GLM(y_features, X_design, family=Binomial())
        result = model.fit()
        
        if not result.converged:
            logger.warning("IPW: Propensity score model did not converge.")
            return {
                'estimate': np.nan,
                'se': np.nan,
                'n_obs': len(local_data),
                'n_effective': len(observed),
                'converged': False,
                'method': 'IPW',
                'error': 'Propensity model did not converge'
            }
        
        # Predict probabilities for the FULL local dataset (observed + missing)
        # We need to predict P(R=1) for everyone in the local bandwidth
        full_design = sm.add_constant(local_data[['X', 'Z', 'D']])
        
        # Handle potential singularities or out-of-bounds predictions
        try:
            prop_scores = result.predict(full_design)
            # Clip to avoid division by zero
            prop_scores = np.clip(prop_scores, 1e-6, 1.0 - 1e-6)
        except Exception as e:
            logger.warning(f"IPW: Failed to predict propensity scores: {e}")
            return {
                'estimate': np.nan,
                'se': np.nan,
                'n_obs': len(local_data),
                'n_effective': len(observed),
                'converged': False,
                'method': 'IPW',
                'error': str(e)
            }

    except Exception as e:
        logger.error(f"IPW: Propensity score model fitting failed: {e}")
        return {
            'estimate': np.nan,
            'se': np.nan,
            'n_obs': len(local_data),
            'n_effective': 0,
            'converged': False,
            'method': 'IPW',
            'error': str(e)
        }

    # 2. Calculate Weights
    # Weight = 1 / P(R=1)
    weights = 1.0 / prop_scores

    # 3. Weighted Local Linear Regression
    # Model: Y = beta0 + beta1*X + tau*D + error
    # We use the full local dataset, but weights for missing cases will be high (if they were observed)
    # effectively correcting the distribution.
    
    # Prepare design matrix for the outcome model
    # Y ~ X + D (Interaction X*D is often used in RD, but standard local linear is Y ~ X + D)
    # The standard RD estimator is the coefficient on D.
    # We use X and D as regressors.
    outcome_X = local_data[['X', 'D']]
    outcome_y = local_data['Y']
    outcome_design = sm.add_constant(outcome_X)

    # Fit weighted GLM (OLS with weights)
    try:
        weighted_model = GLM(outcome_y, outcome_design, weights=weights)
        weighted_result = weighted_model.fit()
        
        if not weighted_result.converged:
             logger.warning("IPW: Weighted outcome model did not converge.")
             return {
                'estimate': np.nan,
                'se': np.nan,
                'n_obs': len(local_data),
                'n_effective': len(observed),
                'converged': False,
                'method': 'IPW',
                'error': 'Outcome model did not converge'
             }

        # The treatment effect is the coefficient on D (index 2: const, X, D)
        # Check if D is in the model
        if 'D' not in outcome_design.columns:
             # Fallback if D was dropped due to collinearity
             tau_idx = None
             for i, col in enumerate(outcome_design.columns):
                 if col == 'D':
                     tau_idx = i
                     break
             if tau_idx is None:
                 # Try to find it by name if columns are not aligned
                 # In sm.add_constant, order is const, then columns of input
                 # Input was ['X', 'D'], so D is index 2
                 tau_idx = 2
        else:
             tau_idx = list(outcome_design.columns).index('D')

        estimate = weighted_result.params.iloc[tau_idx]
        se = weighted_result.bse.iloc[tau_idx]
        
        # Calculate effective sample size: (sum(w))^2 / sum(w^2)
        w_sum = weights.sum()
        w_sq_sum = (weights ** 2).sum()
        n_effective = (w_sum ** 2) / w_sq_sum if w_sq_sum > 0 else 0

        return {
            'estimate': float(estimate),
            'se': float(se),
            'n_obs': len(local_data),
            'n_effective': float(n_effective),
            'converged': True,
            'method': 'IPW',
            'true_effect': true_effect,
            'bias': float(estimate - true_effect)
        }

    except Exception as e:
        logger.error(f"IPW: Weighted outcome model fitting failed: {e}")
        return {
            'estimate': np.nan,
            'se': np.nan,
            'n_obs': len(local_data),
            'n_effective': 0,
            'converged': False,
            'method': 'IPW',
            'error': str(e)
        }


def main():
    """
    CLI entry point for testing the IPW estimator.
    Generates synthetic data, applies missingness, and runs IPW.
    """
    import sys
    import os
    from pathlib import Path
    import argparse

    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

    from src.generators.rd_data import generate_rd_data
    from src.generators.missingness import apply_mcar_mask
    from src.config_loader import load_simulation_config, load_missingness_config

    parser = argparse.ArgumentParser(description="Test IPW Estimator")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--n", type=int, default=1000, help="Sample size")
    parser.add_argument("--missing_rate", type=float, default=0.3, help="Missingness rate")
    args = parser.parse_args()

    logger.info(f"Starting IPW Estimator Test with seed={args.seed}, n={args.n}")

    # 1. Generate Data
    try:
        sim_config = load_simulation_config()
        sim_config.sample_size = args.n
        sim_config.seed = args.seed
        
        data = generate_rd_data(sim_config)
        logger.info(f"Generated {len(data)} rows of RD data.")
    except Exception as e:
        logger.error(f"Failed to generate data: {e}")
        sys.exit(1)

    # 2. Apply Missingness (MCAR for this test)
    try:
        miss_config = load_missingness_config()
        miss_config.rate = args.missing_rate
        miss_config.mechanism = "MCAR"
        
        # We need to apply the mask manually here for the test script
        # The apply_mcar_mask expects a DataFrame and a rate
        data_with_mask = apply_mcar_mask(data, rate=args.missing_rate)
        logger.info(f"Applied MCAR missingness (rate={args.missing_rate}). Observed: {data_with_mask['R'].sum()}")
    except Exception as e:
        logger.error(f"Failed to apply missingness: {e}")
        sys.exit(1)

    # 3. Run IPW
    try:
        result = estimate_ipw(data_with_mask, true_effect=sim_config.true_effect)
        
        logger.info("IPW Estimation Results:")
        logger.info(f"  Estimate: {result['estimate']:.4f}")
        logger.info(f"  SE: {result['se']:.4f}")
        logger.info(f"  True Effect: {result.get('true_effect', 'N/A')}")
        logger.info(f"  Bias: {result.get('bias', 'N/A'):.4f}")
        logger.info(f"  Converged: {result['converged']}")
        if 'error' in result:
            logger.error(f"  Error: {result['error']}")
            
        return result
    except Exception as e:
        logger.error(f"IPW Estimation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
