"""
Bayesian Online Change Point Detection (BOCPD) implementation.
Supports configurable run-length priors via config.yaml.
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Generator

from main import load_config
from exceptions import E_NO_DATA

logger = logging.getLogger(__name__)

class GaussianBOCPD:
    """
    Gaussian BOCPD with configurable run-length prior.
    """
    def __init__(self, run_length_prior: str = "geometric", 
                 geometric_lambda: float = 0.1, 
                 uniform_max: int = 100,
                 delta: float = 0.001,
                 mu_0: float = 0.0,
                 kappa_0: float = 1.0,
                 alpha_0: float = 1.0,
                 beta_0: float = 1.0):
        """
        Initialize BOCPD with specified prior.
        
        Args:
            run_length_prior: "geometric" or "uniform"
            geometric_lambda: Lambda parameter for geometric distribution
            uniform_max: Max run length for uniform distribution
            delta: Regularization parameter for precision
            mu_0, kappa_0, alpha_0, beta_0: Hyperparameters for Normal-Inverse-Gamma
        """
        self.run_length_prior = run_length_prior
        self.geometric_lambda = geometric_lambda
        self.uniform_max = uniform_max
        self.delta = delta
        self.mu_0 = mu_0
        self.kappa_0 = kappa_0
        self.alpha_0 = alpha_0
        self.beta_0 = beta_0
        
        logger.info(f"BOCPD initialized with prior: {run_length_prior}")
        if run_length_prior == "geometric":
            logger.info(f"Geometric prior lambda: {geometric_lambda}")
        elif run_length_prior == "uniform":
            logger.info(f"Uniform prior max: {uniform_max}")

    def _survival_prob(self, run_length: int) -> float:
        """Calculate survival probability P(r_t = r_{t-1} + 1 | r_{t-1})"""
        if self.run_length_prior == "geometric":
            return (1 - self.geometric_lambda) ** run_length
        elif self.run_length_prior == "uniform":
            if run_length < self.uniform_max:
                return 1.0
            else:
                return 0.0
        else:
            raise ValueError(f"Unknown prior: {self.run_length_prior}")

    def _predictive_prob(self, x: float, run_length: int, 
                         params: Dict) -> float:
        """
        Calculate predictive probability P(x_t | x_{t-run_length:t-1})
        Using Normal-Inverse-Gamma posterior predictive (Student-t).
        """
        # Get posterior parameters for current run length
        mu, kappa, alpha, beta = params[run_length]
        
        # Update with new observation
        kappa_new = kappa + 1
        mu_new = (kappa * mu + x) / kappa_new
        alpha_new = alpha + 0.5
        beta_new = beta + 0.5 * kappa * (x - mu) ** 2 / kappa_new
        
        # Predictive variance (Student-t)
        # t-distribution with 2*alpha degrees of freedom
        # Location: mu, Scale: sqrt(beta * (kappa+1) / (kappa * alpha))
        
        # Log predictive probability to avoid underflow
        # Using Student-t PDF: 
        # f(x) = Gamma((nu+1)/2) / (Gamma(nu/2) * sqrt(nu*pi*sigma^2)) * (1 + (x-mu)^2/(nu*sigma^2))^(-(nu+1)/2)
        
        nu = 2 * alpha
        scale_sq = beta * (kappa + 1) / (kappa * alpha)
        
        # Log PDF
        from scipy.special import gammaln, loggamma
        log_pdf = (gammaln((nu + 1) / 2) - gammaln(nu / 2) 
                  - 0.5 * np.log(nu * np.pi * scale_sq) 
                  - (nu + 1) / 2 * np.log(1 + (x - mu) ** 2 / (nu * scale_sq)))
        
        return np.exp(log_pdf)

    def update(self, x: float, params: Dict, 
               max_run_length: int) -> Tuple[Dict, np.ndarray]:
        """
        Update BOCPD with new observation.
        
        Args:
            x: New observation
            params: Current parameters {run_length: (mu, kappa, alpha, beta)}
            max_run_length: Maximum run length to track
            
        Returns:
            Updated params and run-length distribution
        """
        # Initialize new params dict
        new_params = {}
        run_length_probs = np.zeros(max_run_length + 1)
        
        # For each possible previous run length
        for r in range(max_run_length + 1):
            if r not in params:
                # Initialize with prior
                mu, kappa, alpha, beta = self.mu_0, self.kappa_0, self.alpha_0, self.beta_0
            else:
                mu, kappa, alpha, beta = params[r]
            
            # Predictive probability
            try:
                pred_prob = self._predictive_prob(x, r, {r: (mu, kappa, alpha, beta)})
            except:
                pred_prob = 1e-300  # Avoid zero probabilities
            
            # Survival probability
            surv_prob = self._survival_prob(r)
            
            # New run length
            new_r = r + 1
            if new_r <= max_run_length:
                # Update parameters for new run length
                kappa_new = kappa + 1
                mu_new = (kappa * mu + x) / kappa_new
                alpha_new = alpha + 0.5
                beta_new = beta + 0.5 * kappa * (x - mu) ** 2 / kappa_new
                
                new_params[new_r] = (mu_new, kappa_new, alpha_new, beta_new)
                run_length_probs[new_r] += pred_prob * surv_prob
            
            # Change point probability (r=0)
            # This happens when a change point is detected
            # Use prior parameters
            new_params[0] = (self.mu_0, self.kappa_0, self.alpha_0, self.beta_0)
            # Probability of change point is 1 - survival_prob
            change_prob = 1 - surv_prob
            # Predictive with prior
            try:
                pred_prob_prior = self._predictive_prob(x, 0, {0: (self.mu_0, self.kappa_0, self.alpha_0, self.beta_0)})
            except:
                pred_prob_prior = 1e-300
            
            run_length_probs[0] += pred_prob_prior * (1 - surv_prob)
        
        # Normalize
        total = np.sum(run_length_probs)
        if total > 0:
            run_length_probs /= total
        else:
            run_length_probs = np.ones_like(run_length_probs) / len(run_length_probs)
        
        return new_params, run_length_probs

def run_bocpd_rolling_window(data: pd.Series, window_size: int = 12, 
                             stride: int = 1, prior_config: Optional[Dict] = None) -> List[Dict]:
    """
    Run BOCPD on rolling windows of the data.
    
    Args:
        data: Input time series
        window_size: Size of rolling window
        stride: Stride for rolling window
        prior_config: Dictionary with prior configuration
        
    Returns:
        List of detected change points with statistics
    """
    if prior_config is None:
        prior_config = {}
    
    prior_type = prior_config.get("run_length_prior", "geometric")
    geom_lambda = prior_config.get("geometric_lambda", 0.1)
    uniform_max = prior_config.get("bocpd_uniform_max", 100)
    
    logger.info(f"Running BOCPD with prior: {prior_type}")
    logger.info(f"Prior params: lambda={geom_lambda}, uniform_max={uniform_max}")
    
    bocpd = GaussianBOCPD(
        run_length_prior=prior_type,
        geometric_lambda=geom_lambda,
        uniform_max=uniform_max
    )
    
    change_points = []
    max_run_length = 50  # Maximum run length to track
    
    # Process data in rolling windows
    for start in range(0, len(data) - window_size + 1, stride):
        window_data = data.iloc[start:start + window_size].values
        
        # Initialize parameters
        params = {0: (bocpd.mu_0, bocpd.kappa_0, bocpd.alpha_0, bocpd.beta_0)}
        run_length_dist = np.zeros(max_run_length + 1)
        run_length_dist[0] = 1.0
        
        # Run BOCPD on window
        window_change_points = []
        for t, x in enumerate(window_data):
            params, run_length_dist = bocpd.update(x, params, max_run_length)
            
            # Detect change point if probability of r=0 is high
            if run_length_dist[0] > 0.5:  # Threshold for change point
                window_change_points.append({
                    "window_start": start,
                    "relative_pos": t,
                    "global_pos": start + t,
                    "change_prob": run_length_dist[0],
                    "run_length_dist": run_length_dist.copy()
                })
        
        # Record change points for this window
        if window_change_points:
            # Take the most confident change point
            best_cp = max(window_change_points, key=lambda x: x["change_prob"])
            change_points.append({
                "method": "BOCPD",
                "window_start": best_cp["window_start"],
                "week_id": best_cp["global_pos"],
                "statistic": best_cp["change_prob"],
                "run_length": int(np.argmax(run_length_dist)),
                "prior_used": prior_type,
                "prior_params": {
                    "lambda": geom_lambda,
                    "uniform_max": uniform_max
                }
            })
    
    logger.info(f"BOCPD detected {len(change_points)} change points")
    return change_points

def main():
    """Main entry point for BOCPD analysis."""
    # Load config
    config = load_config()
    
    # Setup logging
    import logging_setup
    logger = logging_setup.setup_logging("bocpd")
    
    try:
        # Load preprocessed data
        processed_path = "data/processed/ili_processed.csv"
        if not os.path.exists(processed_path):
            raise E_NO_DATA(f"Processed data not found: {processed_path}")
        
        data = pd.read_csv(processed_path)
        if 'ili_standardized' not in data.columns:
            raise E_NO_DATA("Column 'ili_standardized' not found in processed data")
        
        series = data['ili_standardized']
        
        # Run BOCPD
        prior_config = {
            "run_length_prior": config.get("run_length_prior", "geometric"),
            "geometric_lambda": config.get("geometric_lambda", 0.1),
            "bocpd_uniform_max": config.get("bocpd_uniform_max", 100)
        }
        
        change_points = run_bocpd_rolling_window(
            series,
            window_size=config.get("window_size", 12),
            stride=config.get("stride", 1),
            prior_config=prior_config
        )
        
        # Save results
        output_path = "data/processed/bocpd_results.csv"
        if change_points:
            df_cp = pd.DataFrame(change_points)
            df_cp.to_csv(output_path, index=False)
            logger.info(f"Saved BOCPD results to {output_path}")
        else:
            # Create empty file with headers
            pd.DataFrame(columns=["method", "window_start", "week_id", "statistic", "run_length", "prior_used", "prior_params"]).to_csv(output_path, index=False)
            logger.info(f"No change points detected, saved empty results to {output_path}")
        
    except E_NO_DATA as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running BOCPD: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
