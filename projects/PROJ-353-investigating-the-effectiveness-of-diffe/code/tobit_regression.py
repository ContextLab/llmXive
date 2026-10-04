"""
Tobit Regression Implementation for Censored Convergence Data.

This module implements Tobit regression to analyze the relationship between
loss type, beta parameter, and steps to convergence, handling censored data
where convergence was not reached within MAX_EPOCHS.

Primary function: run_tobit_regression()
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any
import sys
import os

# Import project constants
from utils import MAX_EPOCHS

def run_tobit_regression(df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """
    Run Tobit regression on the aggregated training data.

    Args:
        df: DataFrame containing columns:
            - 'steps_to_convergence': dependent variable
            - 'loss_type': categorical independent variable (CE or InfoNCE)
            - 'beta': continuous independent variable

    Returns:
        Tuple of:
            - model: The fitted Tobit model instance
            - results: Dictionary containing:
                - 'coefficients': dict of coefficient names to values
                - 'p_values': dict of coefficient names to p-values
                - 'interaction_p_value': p-value for the interaction term
                - 'log_likelihood': model log-likelihood

    Raises:
        ImportError: If statsmodels sandbox is unavailable and custom fallback fails
        ValueError: If required columns are missing
    """
    # Validate input
    required_cols = ['steps_to_convergence', 'loss_type', 'beta']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Prepare data
    y = df['steps_to_convergence'].values.astype(np.float64)
    loss_type = df['loss_type'].values
    beta = df['beta'].values.astype(np.float64)

    # Create dummy variables for loss_type (reference: CE)
    # We'll create: intercept, loss_type_InfoNCE, beta, interaction
    n_samples = len(y)
    X = np.zeros((n_samples, 4))
    X[:, 0] = 1.0  # Intercept
    X[:, 1] = (loss_type == 'InfoNCE').astype(float)  # Loss type effect
    X[:, 2] = beta  # Beta effect
    X[:, 3] = X[:, 1] * beta  # Interaction term

    col_names = ['Intercept', 'loss_type_InfoNCE', 'beta', 'loss_type_InfoNCE:beta']

    # Try to use statsmodels sandbox Tobit first
    try:
        from statsmodels.sandbox.regression.tobit import Tobit
        
        # Initialize and fit Tobit model
        # lower=0, upper=MAX_EPOCHS to handle censored data
        tobit_model = Tobit(y, X, lower=0, upper=MAX_EPOCHS)
        tobit_results = tobit_model.fit()
        
        # Extract coefficients and p-values
        coefficients = dict(zip(col_names, tobit_results.params))
        p_values = dict(zip(col_names, tobit_results.pvalues))
        
        results = {
            'coefficients': coefficients,
            'p_values': p_values,
            'interaction_p_value': p_values.get('loss_type_InfoNCE:beta', None),
            'log_likelihood': tobit_results.llf
        }
        
        return tobit_model, results

    except ImportError:
        # Fallback: Custom Tobit implementation using scipy.optimize
        print("statsmodels.sandbox not available. Using custom Tobit implementation...")
        
        from scipy.optimize import minimize
        from scipy.stats import norm
        
        def log_likelihood_censored(params, X, y, lower, upper):
            """
            Compute log-likelihood for censored normal data.
            
            For Tobit model: y* = X*beta + epsilon, epsilon ~ N(0, sigma^2)
            Observed y = lower if y* <= lower
                       y = upper if y* >= upper
                       y = y* if lower < y* < upper
            """
            beta_params = params[:-1]  # Regression coefficients
            sigma = np.exp(params[-1])  # Log-transform to ensure positivity
            
            Xb = X @ beta_params
            sigma_vec = np.full_like(Xb, sigma)
            
            log_lik = 0.0
            
            for i in range(len(y)):
                yi = y[i]
                xbi = Xb[i]
                sigi = sigma_vec[i]
                
                if yi <= lower:
                    # Left-censored: P(Y* <= lower)
                    z = (lower - xbi) / sigi
                    prob = norm.cdf(z)
                    if prob > 0:
                        log_lik += np.log(prob)
                    else:
                        log_lik += np.log(1e-10)
                
                elif yi >= upper:
                    # Right-censored: P(Y* >= upper)
                    z = (upper - xbi) / sigi
                    prob = 1 - norm.cdf(z)
                    if prob > 0:
                        log_lik += np.log(prob)
                    else:
                        log_lik += np.log(1e-10)
                
                else:
                    # Uncensored: PDF at y
                    z = (yi - xbi) / sigi
                    log_lik += np.log(norm.pdf(z)) - np.log(sigi)
            
            return -log_lik  # Minimize negative log-likelihood

        # Initial parameter guess
        n_params = X.shape[1] + 1  # beta + sigma
        initial_params = np.zeros(n_params)
        initial_params[:-1] = np.linalg.lstsq(X, y, rcond=None)[0]
        initial_params[-1] = np.log(np.std(y) + 1e-6)
        
        # Optimize
        result = minimize(
            log_likelihood_censored,
            initial_params,
            args=(X, y, 0, MAX_EPOCHS),
            method='L-BFGS-B',
            options={'maxiter': 1000}
        )
        
        if not result.success:
            raise RuntimeError(f"Custom Tobit optimization failed: {result.message}")
        
        fitted_params = result.x
        beta_est = fitted_params[:-1]
        sigma_est = np.exp(fitted_params[-1])
        
        # Compute standard errors using Hessian approximation
        hessian = result.hess_inv if hasattr(result, 'hess_inv') else None
        if hessian is None:
            # Approximate Hessian numerically if not available
            from scipy.optimize import approx_fprime
            eps = np.sqrt(np.finfo(float).eps)
            hessian = approx_fprime(fitted_params, 
                                   lambda p: log_likelihood_censored(p, X, y, 0, MAX_EPOCHS),
                                   eps)
            # Use diagonal approximation for simplicity
            se = np.sqrt(np.abs(np.diag(1.0 / hessian)))
        else:
            se = np.sqrt(np.abs(np.diag(hessian)))
        
        # Compute z-statistics and p-values
        z_stats = beta_est / (se[:-1] + 1e-10)  # Exclude sigma
        p_vals = 2 * (1 - norm.cdf(np.abs(z_stats)))
        
        coefficients = dict(zip(col_names, beta_est))
        p_values = dict(zip(col_names, p_vals))
        
        # Compute log-likelihood at optimum
        ll = -log_likelihood_censored(fitted_params, X, y, 0, MAX_EPOCHS)
        
        results = {
            'coefficients': coefficients,
            'p_values': p_values,
            'interaction_p_value': p_values.get('loss_type_InfoNCE:beta', None),
            'log_likelihood': ll
        }
        
        # Create a simple model object for compatibility
        class CustomTobitModel:
            def __init__(self, coeffs, p_vals, ll):
                self.params = coeffs
                self.pvalues = p_vals
                self.llf = ll
                self.fitted_values = X @ np.array(list(coeffs.values()))
        
        custom_model = CustomTobitModel(coefficients, p_values, ll)
        return custom_model, results

def main():
    """
    Main entry point for Tobit regression analysis.
    
    Reads aggregated data from data/processed/convergence_logs.csv,
    runs Tobit regression, and prints results.
    """
    # Define paths
    input_path = Path("data/processed/convergence_logs.csv")
    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        print("Please run T033 (aggregate_training_runs) first.")
        sys.exit(1)
    
    # Load data
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    print(f"Loaded {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    print(f"Loss types: {df['loss_type'].unique()}")
    print(f"Beta range: [{df['beta'].min()}, {df['beta'].max()}]")
    print(f"Steps to convergence range: [{df['steps_to_convergence'].min()}, {df['steps_to_convergence'].max()}]")
    
    # Run Tobit regression
    print("\nRunning Tobit regression...")
    print(f"Formula: steps_to_convergence ~ C(loss_type) * beta")
    print(f"Censoring: lower=0, upper={MAX_EPOCHS}")
    
    try:
        model, results = run_tobit_regression(df)
        
        print("\n" + "="*60)
        print("TOBIT REGRESSION RESULTS")
        print("="*60)
        
        print("\nCoefficients:")
        for name, coef in results['coefficients'].items():
            p_val = results['p_values'].get(name, 'N/A')
            print(f"  {name:30s}: {coef:12.6f} (p={p_val:.6f})")
        
        print(f"\nInteraction term p-value: {results['interaction_p_value']:.6f}")
        print(f"Log-likelihood: {results['log_likelihood']:.4f}")
        
        # Save results
        output_file = output_dir / "tobit_results.json"
        import json
        with open(output_file, 'w') as f:
            # Convert numpy types to Python types for JSON serialization
            json_results = {
                'coefficients': {k: float(v) for k, v in results['coefficients'].items()},
                'p_values': {k: float(v) for k, v in results['p_values'].items()},
                'interaction_p_value': float(results['interaction_p_value']) if results['interaction_p_value'] is not None else None,
                'log_likelihood': float(results['log_likelihood'])
            }
            json.dump(json_results, f, indent=2)
        
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"Error during Tobit regression: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()