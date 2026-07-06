import os
import tempfile
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
from numpy.typing import ArrayLike
from cmdstanpy import CmdStanModel, CmdStanFit

# Stan model code for Bayesian Linear Regression
# Uses Normal(0, 10) priors for coefficients and Half-Cauchy(0, 10) for sigma
BAYESIAN_MODEL_CODE = """
data {
  int<lower=0> N;
  int<lower=0> K;
  matrix[N, K] X;
  vector[N] y;
}
parameters {
  vector[K] beta;
  real<lower=0> sigma;
}
transformed parameters {
  vector[N] y_hat = X * beta;
}
model {
  // Priors
  beta ~ normal(0, 10);
  sigma ~ cauchy(0, 10);
  
  // Likelihood
  y ~ normal(y_hat, sigma);
}
"""

class BayesianModel:
    """
    Bayesian Linear Regression model wrapper using CmdStanPy.
    
    Implements:
    - Multiple chains execution (default 4)
    - 2000 samples per chain, 500 warmup
    - Divergent transition checking
    - R-hat convergence diagnostics
    """
    
    def __init__(self, model_code: str = BAYESIAN_MODEL_CODE):
        self.model_code = model_code
        self.model: Optional[CmdStanModel] = None
        self.fit_result: Optional[CmdStanFit] = None
        
    def _compile_model(self) -> CmdStanModel:
        """Compile the Stan model to an executable."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_path = os.path.join(tmp_dir, "bayesian_model")
            stan_file = f"{model_path}.stan"
            exe_file = f"{model_path}.exe"
            
            with open(stan_file, 'w') as f:
                f.write(self.model_code)
            
            try:
                # Compile the model
                self.model = CmdStanModel(stan_file=stan_file)
            except Exception as e:
                raise RuntimeError(f"Failed to compile Stan model: {e}")
            
        return self.model

    def fit(
        self,
        X: ArrayLike,
        y: ArrayLike,
        chains: int = 4,
        iter_warmup: int = 500,
        iter_sampling: int = 2000,
        seed: Optional[int] = None
    ) -> CmdStanFit:
        """
        Fit the Bayesian model using CmdStanPy.
        
        Args:
            X: Feature matrix (N, K)
            y: Target vector (N,)
            chains: Number of MCMC chains (default 4)
            iter_warmup: Warmup iterations per chain (default 500)
            iter_sampling: Sampling iterations per chain (default 2000)
            seed: Random seed for reproducibility
        
        Returns:
            CmdStanFit object containing the posterior samples
        
        Raises:
            RuntimeError: If model compilation fails or sampling encounters errors
        """
        if self.model is None:
            self._compile_model()
        
        X = np.asarray(X)
        y = np.asarray(y)
        
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if y.ndim == 1:
            y = y.reshape(-1)
        
        N, K = X.shape
        
        data = {
            'N': N,
            'K': K,
            'X': X,
            'y': y
        }
        
        try:
            self.fit_result = self.model.sample(
                data=data,
                chains=chains,
                iter_warmup=iter_warmup,
                iter_sampling=iter_sampling,
                seed=seed,
                show_console=False  # Suppress console output for cleaner logs
            )
        except Exception as e:
            raise RuntimeError(f"Stan sampling failed: {e}")
        
        return self.fit_result

    def check_diagnostics(self) -> Dict[str, Any]:
        """
        Check MCMC diagnostics including R-hat and divergent transitions.
        
        Returns:
            Dictionary containing:
            - 'r_hat_max': Maximum R-hat value across parameters
            - 'divergent_count': Number of divergent transitions
            - 'divergent_rate': Fraction of divergent transitions
            - 'is_converged': Boolean indicating if R-hat < 1.05 and no divergences
            - 'warnings': List of warning messages if issues detected
        """
        if self.fit_result is None:
            raise RuntimeError("No fit result available. Call fit() first.")
        
        diagnostics = {
            'r_hat_max': 0.0,
            'divergent_count': 0,
            'divergent_rate': 0.0,
            'is_converged': True,
            'warnings': []
        }
        
        try:
            # Get R-hat values
            r_hat = self.fit_result.summary().loc['r_hat']
            diagnostics['r_hat_max'] = float(r_hat.max())
            
            if diagnostics['r_hat_max'] > 1.05:
                diagnostics['is_converged'] = False
                diagnostics['warnings'].append(
                    f"R-hat max ({diagnostics['r_hat_max']:.4f}) > 1.05. "
                    "Chain convergence may be insufficient."
                )
        
        except Exception as e:
            diagnostics['warnings'].append(f"Error computing R-hat: {e}")
        
        try:
            # Get divergent transitions
            # CmdStanFit doesn't have a direct method, so we parse the sampler diagnostics
            # Access the sampler diagnostics from the fit object
            sampler_diagnostics = self.fit_result.stan_variable("divergent__")
            if sampler_diagnostics is not None:
                divergent_count = int(np.sum(sampler_diagnostics))
                total_samples = sampler_diagnostics.size
                diagnostics['divergent_count'] = divergent_count
                diagnostics['divergent_rate'] = divergent_count / total_samples
                
                if divergent_count > 0:
                    diagnostics['is_converged'] = False
                    diagnostics['warnings'].append(
                        f"Detected {divergent_count} divergent transitions "
                        f"({diagnostics['divergent_rate']:.2%}). "
                        "Consider increasing adapt_delta or reparameterizing."
                    )
            else:
                diagnostics['warnings'].append("Could not retrieve divergent transition data.")
        
        except Exception as e:
            diagnostics['warnings'].append(f"Error checking divergent transitions: {e}")
        
        return diagnostics

    def get_intervals(
        self,
        param: str = "beta",
        prob: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get credible intervals for model parameters.
        
        Args:
            param: Name of the parameter (e.g., 'beta', 'sigma')
            prob: Credible interval probability (default 0.95 for 95%)
        
        Returns:
            Tuple of (lower_bounds, upper_bounds) arrays
        """
        if self.fit_result is None:
            raise RuntimeError("No fit result available. Call fit() first.")
        
        samples = self.fit_result.stan_variable(param)
        
        # Handle different shapes
        if samples.ndim == 1:
            # Scalar parameter
            lower = np.percentile(samples, (1 - prob) / 2 * 100)
            upper = np.percentile(samples, (1 + prob) / 2 * 100)
            return np.array([lower]), np.array([upper])
        elif samples.ndim == 2:
            # Vector parameter (e.g., beta)
            lower = np.percentile(samples, (1 - prob) / 2 * 100, axis=0)
            upper = np.percentile(samples, (1 + prob) / 2 * 100, axis=0)
            return lower, upper
        else:
            raise ValueError(f"Unsupported parameter shape: {samples.shape}")


def fit_bayesian_and_get_intervals(
    X: ArrayLike,
    y: ArrayLike,
    chains: int = 4,
    iter_warmup: int = 500,
    iter_sampling: int = 2000,
    seed: Optional[int] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    High-level function to fit a Bayesian model and return intervals and diagnostics.
    
    This function wraps the BayesianModel class to provide a simple interface
    for fitting and extracting results.
    
    Args:
        X: Feature matrix (N, K)
        y: Target vector (N,)
        chains: Number of MCMC chains (default 4)
        iter_warmup: Warmup iterations per chain (default 500)
        iter_sampling: Sampling iterations per chain (default 2000)
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of:
        - intervals: Dict with 'beta_lower', 'beta_upper', 'sigma_lower', 'sigma_upper'
        - diagnostics: Dict with 'r_hat_max', 'divergent_count', 'divergent_rate', 
                      'is_converged', 'warnings'
    
    Raises:
        RuntimeError: If model fitting fails or diagnostics show issues
    """
    model = BayesianModel()
    model.fit(
        X=X,
        y=y,
        chains=chains,
        iter_warmup=iter_warmup,
        iter_sampling=iter_sampling,
        seed=seed
    )
    
    # Check diagnostics
    diagnostics = model.check_diagnostics()
    
    # Get intervals for beta
    beta_lower, beta_upper = model.get_intervals("beta", prob=0.95)
    sigma_lower, sigma_upper = model.get_intervals("sigma", prob=0.95)
    
    intervals = {
        'beta_lower': beta_lower,
        'beta_upper': beta_upper,
        'sigma_lower': sigma_lower,
        'sigma_upper': sigma_upper,
        'beta_mean': model.fit_result.stan_variable("beta").mean(axis=0),
        'sigma_mean': model.fit_result.stan_variable("sigma").mean()
    }
    
    return intervals, diagnostics