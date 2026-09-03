import os
import tempfile
import logging
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
from numpy.typing import ArrayLike
from cmdstanpy import CmdStanModel, CmdStanFit

# Configure logging for the module
logger = logging.getLogger(__name__)

STAN_MODEL_CODE = """
data {
  int<lower=1> N;
  int<lower=1> P;
  matrix[N, P] X;
  vector[N] y;
}
parameters {
  vector[P] beta;
  real<lower=0> sigma;
}
model {
  // Priors
  beta ~ normal(0, 10);
  sigma ~ cauchy(0, 5); // Half-Cauchy for scale

  // Likelihood
  y ~ normal(X * beta, sigma);
}
generated quantities {
  vector[N] y_rep;
  for (n in 1:N) {
    y_rep[n] = normal_rng(X[n] * beta, sigma);
  }
}
"""

class BayesianModel:
    """
    Bayesian Linear Regression wrapper using CmdStanPy.
    Implements Normal(0, 10) priors for coefficients and Half-Cauchy(0, 5) for sigma.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.model: Optional[CmdStanModel] = None
        self.fit: Optional[CmdStanFit] = None
        self._stan_code_path: Optional[str] = None

    def _compile_model(self) -> CmdStanModel:
        """Compiles the Stan model if not already compiled."""
        if self.model is not None:
            return self.model

        logger.info("Compiling Stan model...")
        # Write Stan code to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.stan', delete=False) as f:
            f.write(STAN_MODEL_CODE)
            self._stan_code_path = f.name

        try:
            self.model = CmdStanModel(stan_file=self._stan_code_path)
            logger.info("Stan model compiled successfully.")
        except Exception as e:
            logger.error(f"Failed to compile Stan model: {e}")
            raise
        
        return self.model

    def fit(self, X: ArrayLike, y: ArrayLike, 
            chains: int = 4, 
            samples_per_chain: int = 1000, 
            warmup: int = 500,
            check_divergences: bool = True) -> Dict[str, Any]:
        """
        Fits the Bayesian model using CmdStanPy.
        
        Args:
            X: Feature matrix (N, P)
            y: Target vector (N,)
            chains: Number of MCMC chains (default 4)
            samples_per_chain: Number of post-warmup samples per chain
            warmup: Number of warmup iterations per chain
            check_divergences: If True, raises an error if divergent transitions are found.
        
        Returns:
            Dict containing fit results and diagnostics.
        
        Raises:
            RuntimeError: If the model fails to converge (R-hat > 1.05) or 
                          if divergent transitions are detected and check_divergences is True.
        """
        X = np.asarray(X)
        y = np.asarray(y).flatten()
        
        if X.ndim != 2:
            raise ValueError("X must be a 2D array")
        if y.ndim != 1:
            raise ValueError("y must be a 1D array")
        
        N, P = X.shape
        if N <= P:
            raise ValueError(f"Sample size N={N} must be greater than number of predictors P={P} for Bayesian regression.")

        model = self._compile_model()
        
        data = {
            'N': N,
            'P': P,
            'X': X,
            'y': y
        }

        logger.info(f"Fitting Bayesian model with {chains} chains, {samples_per_chain} samples, {warmup} warmup.")
        
        try:
            self.fit = model.sample(
                data=data,
                chains=chains,
                iter_warmup=warmup,
                iter_sampling=samples_per_chain,
                seed=self.seed,
                show_console=False,
                refresh=0 # Suppress console output for cleaner logs
            )
        except Exception as e:
            logger.error(f"Stan sampling failed: {e}")
            raise RuntimeError(f"Stan sampling failed: {e}")

        # Diagnostics
        diagnostics = {
            'r_hat': {},
            'divergent_count': 0,
            'divergent': False,
            'max_r_hat': 0.0
        }

        # Check R-hat
        try:
            summary = self.fit.summary()
            # R-hat is usually in the 'r_hat' column of the summary
            # We need to check beta and sigma specifically
            for param in ['beta', 'sigma']:
                if param in summary.columns:
                    # summary is a DataFrame, columns are parameters
                    # We need to handle the case where beta is a vector
                    # summary usually flattens beta into beta[1], beta[2], etc.
                    r_hat_vals = summary[summary.index.str.contains(param)]['r_hat'].values
                    if len(r_hat_vals) > 0:
                        max_r = np.max(r_hat_vals)
                        diagnostics['r_hat'][param] = float(max_r)
                        if max_r > diagnostics['max_r_hat']:
                            diagnostics['max_r_hat'] = float(max_r)
        except Exception as e:
            logger.warning(f"Could not compute R-hat summary: {e}")
            diagnostics['max_r_hat'] = 999.0 # Force failure if we can't check

        if diagnostics['max_r_hat'] > 1.05:
            msg = f"Model failed convergence check: Max R-hat = {diagnostics['max_r_hat']:.4f} (> 1.05)"
            logger.error(msg)
            raise RuntimeError(msg)

        # Check Divergent Transitions
        if check_divergences:
            try:
                # access the sampler diagnostics
                # fit.sampler_diagnostics() returns a dictionary of arrays
                # 'divergent__' is usually a boolean array or count
                sampler_diag = self.fit.sampler_diagnostics()
                if 'divergent__' in sampler_diag:
                    # sum across all chains and samples
                    divergent_count = int(np.sum(sampler_diag['divergent__']))
                    diagnostics['divergent_count'] = divergent_count
                    if divergent_count > 0:
                        diagnostics['divergent'] = True
                        msg = f"Model detected {divergent_count} divergent transitions."
                        logger.error(msg)
                        raise RuntimeError(msg)
            except Exception as e:
                logger.warning(f"Could not check divergent transitions: {e}")

        logger.info("Bayesian model fit successful.")
        return diagnostics

    def get_intervals(self, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extracts posterior intervals for coefficients.
        
        Args:
            alpha: Significance level (default 0.05 for 95% CI)
        
        Returns:
            Tuple of (lower_bound, point_estimate, upper_bound) for each coefficient.
        """
        if self.fit is None:
            raise RuntimeError("Model must be fitted before getting intervals.")
        
        # Extract beta samples
        # fit.stan_variable returns a dict of numpy arrays
        # beta shape: (chains * samples, P)
        beta_samples = self.fit.stan_variable("beta")
        
        # Calculate statistics
        # Point estimate: Mean
        point_estimate = np.mean(beta_samples, axis=0)
        
        # Intervals: Quantile based
        lower = np.quantile(beta_samples, alpha / 2, axis=0)
        upper = np.quantile(beta_samples, 1 - alpha / 2, axis=0)
        
        return lower, point_estimate, upper

def fit_bayesian_and_get_intervals(
    X: ArrayLike, 
    y: ArrayLike, 
    seed: int = 42,
    chains: int = 4,
    samples_per_chain: int = 1000,
    warmup: int = 500,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    High-level wrapper to fit a Bayesian model and return intervals and diagnostics.
    
    This function handles the full pipeline: instantiation, fitting with 
    convergence checks, and interval extraction.
    
    Args:
        X: Feature matrix (N, P)
        y: Target vector (N,)
        seed: Random seed for reproducibility
        chains: Number of MCMC chains
        samples_per_chain: Samples per chain
        warmup: Warmup iterations per chain
        alpha: Significance level for intervals
        
    Returns:
        Dictionary with keys:
            - 'lower': np.ndarray, lower bounds of 95% CI
            - 'upper': np.ndarray, upper bounds of 95% CI
            - 'estimate': np.ndarray, point estimates (posterior mean)
            - 'diagnostics': dict with r_hat, divergent info
            - 'success': bool, True if fit succeeded
            - 'error': str or None, error message if failed
    """
    model = BayesianModel(seed=seed)
    result = {
        'success': False,
        'error': None,
        'lower': None,
        'upper': None,
        'estimate': None,
        'diagnostics': {}
    }
    
    try:
        diagnostics = model.fit(
            X, y, 
            chains=chains, 
            samples_per_chain=samples_per_chain, 
            warmup=warmup,
            check_divergences=True
        )
        
        lower, estimate, upper = model.get_intervals(alpha=alpha)
        
        result['lower'] = lower
        result['upper'] = upper
        result['estimate'] = estimate
        result['diagnostics'] = diagnostics
        result['success'] = True
        
    except RuntimeError as e:
        result['error'] = str(e)
        result['success'] = False
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        result['success'] = False
        
    return result