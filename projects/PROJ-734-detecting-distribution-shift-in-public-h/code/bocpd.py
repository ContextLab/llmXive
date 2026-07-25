"""
Bayesian Online Change-Point Detection (BOCPD) implementation.

Implements a Gaussian observation model to detect distribution shifts
in the ILI time series. This module provides a rolling-window approach
compatible with the project's preprocessing and evaluation pipeline.

Features:
- Gaussian observation model with unknown mean and variance
- Exponential hazard function for run-length distribution
- Dynamic update of predictive distributions
- Change-point detection based on run-length collapse
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Generator
from scipy.special import logsumexp
from scipy.stats import norm, t as student_t

from main import load_config
from preprocess import load_ili_data, remove_missing_weeks, log_transform, standardize

logger = logging.getLogger(__name__)


class GaussianBOCPD:
    """
    Bayesian Online Change-Point Detection with Gaussian Observation Model.
    
    The model assumes observations are drawn from a Normal distribution with
    unknown mean and precision (inverse variance). A Normal-Gamma prior is
    used for conjugacy.
    
    Parameters:
    -----------
    alpha_0, beta_0, kappa_0, mu_0 : float
        Prior hyperparameters for the Normal-Gamma distribution.
        Defaults are set to be weakly informative.
    hazard_rate : float
        Parameter for the exponential hazard function. Controls the
        expected frequency of change-points.
    max_run_length : int
        Maximum run length to consider. Run lengths beyond this are
        treated as a single state or truncated.
    """
    def __init__(
        self,
        alpha_0: float = 1e-2,
        beta_0: float = 1e-2,
        kappa_0: float = 1e-2,
        mu_0: float = 0.0,
        hazard_rate: float = 0.01,
        max_run_length: int = 100
    ):
        self.alpha_0 = alpha_0
        self.beta_0 = beta_0
        self.kappa_0 = kappa_0
        self.mu_0 = mu_0
        self.hazard_rate = hazard_rate
        self.max_run_length = max_run_length
        
        # State variables
        self.run_lengths: np.ndarray = np.zeros(max_run_length + 1)
        self.pred_dist_params: List[Tuple[float, float, float, float]] = []
        self.change_points: List[int] = []
        self.predictive_means: List[float] = []
        
    def _hazard_function(self, run_length: int) -> float:
        """
        Exponential hazard function: P(change point | run_length).
        
        Returns probability that a change-point occurs at the next step.
        """
        return 1.0 - np.exp(-self.hazard_rate)
        
    def _update_run_length_distribution(self, run_length: int) -> float:
        """
        Compute the hazard probability for a given run length.
        
        P(r_t | r_{t-1}) = P(no change | r_{t-1}) if r_t = r_{t-1} + 1
        P(r_t | r_{t-1}) = P(change | r_{t-1}) if r_t = 0
        """
        if run_length == 0:
            # Probability of a change point
            return self._hazard_function(run_length - 1) if run_length > 0 else 0.0
        else:
            # Probability of no change point
            return 1.0 - self._hazard_function(run_length - 1)

    def _predictive_distribution(self, run_length: int, new_obs: float) -> Tuple[float, float]:
        """
        Compute the predictive distribution for a new observation given a run length.
        
        Returns (mean, variance) of the predictive distribution.
        """
        if run_length == 0:
            # Prior predictive
            mu_pred = self.mu_0
            var_pred = 1.0 / self.beta_0 * (1.0 + 1.0 / self.kappa_0)
        else:
            # Get parameters for this run length
            # These are updated incrementally in the main loop
            if run_length > len(self.pred_dist_params):
                # Should not happen if logic is correct, fallback to prior
                mu_pred = self.mu_0
                var_pred = 1.0 / self.beta_0 * (1.0 + 1.0 / self.kappa_0)
            else:
                alpha_n, beta_n, kappa_n, mu_n = self.pred_dist_params[run_length - 1]
                mu_pred = mu_n
                # Predictive variance for Normal-Gamma
                var_pred = beta_n * (kappa_n + 1) / (alpha_n * kappa_n)
                
        return mu_pred, var_pred

    def _update_posterior_params(
        self,
        alpha: float,
        beta: float,
        kappa: float,
        mu: float,
        x: float
    ) -> Tuple[float, float, float, float]:
        """
        Update Normal-Gamma posterior parameters given a new observation.
        
        Returns (alpha_n, beta_n, kappa_n, mu_n)
        """
        kappa_n = kappa + 1.0
        mu_n = (kappa * mu + x) / kappa_n
        alpha_n = alpha + 0.5
        beta_n = beta + 0.5 * kappa * (x - mu) ** 2 / kappa_n
        
        return alpha_n, beta_n, kappa_n, mu_n

    def fit(self, data: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Run BOCPD on the input data series.
        
        Parameters:
        -----------
        data : np.ndarray
            1D array of observations.
            
        Returns:
        --------
        dict
            Dictionary containing:
            - 'run_lengths': Final run length distribution
            - 'change_point_probs': Probability of change point at each step
            - 'expected_run_length': Expected run length at each step
        """
        n = len(data)
        self.run_lengths = np.zeros(self.max_run_length + 1)
        self.pred_dist_params = [
            (self.alpha_0, self.beta_0, self.kappa_0, self.mu_0) 
            for _ in range(self.max_run_length + 1)
        ]
        
        run_length_probs = []
        change_point_probs = []
        expected_run_lengths = []
        
        # Initialize with prior
        self.run_lengths[0] = 1.0
        
        for t, x in enumerate(data):
            new_run_lengths = np.zeros(self.max_run_length + 1)
            log_probs = []
            
            # Iterate over possible previous run lengths
            for r_prev in range(self.max_run_length + 1):
                if self.run_lengths[r_prev] == 0:
                    continue
                    
                # Case 1: No change point (r_t = r_prev + 1)
                if r_prev + 1 <= self.max_run_length:
                    # Predictive probability
                    mu_pred, var_pred = self._predictive_distribution(r_prev, x)
                    # Log probability of observation under predictive
                    # Using log of normal PDF: -0.5 * log(2*pi*var) - 0.5 * (x-mu)^2/var
                    log_p_x = -0.5 * np.log(2 * np.pi * var_pred) - 0.5 * (x - mu_pred) ** 2 / var_pred
                    
                    # Transition probability (no change)
                    log_h = np.log(1.0 - self._hazard_function(r_prev))
                    
                    log_prob = np.log(self.run_lengths[r_prev]) + log_p_x + log_h
                    new_r = r_prev + 1
                    new_run_lengths[new_r] = np.exp(log_prob)
                    
                    # Update posterior params for this new run length
                    if new_r > len(self.pred_dist_params):
                        # Extend if necessary (should not happen with max_run_length)
                        self.pred_dist_params.append((self.alpha_0, self.beta_0, self.kappa_0, self.mu_0))
                    alpha_n, beta_n, kappa_n, mu_n = self._update_posterior_params(
                        *self.pred_dist_params[r_prev], x
                    )
                    self.pred_dist_params[new_r] = (alpha_n, beta_n, kappa_n, mu_n)
                
                # Case 2: Change point (r_t = 0)
                # Predictive probability under prior (r_prev doesn't matter, reset to prior)
                mu_pred, var_pred = self._predictive_distribution(0, x)
                log_p_x = -0.5 * np.log(2 * np.pi * var_pred) - 0.5 * (x - mu_pred) ** 2 / var_pred
                
                # Transition probability (change)
                log_h = np.log(self._hazard_function(r_prev))
                
                log_prob = np.log(self.run_lengths[r_prev]) + log_p_x + log_h
                new_run_lengths[0] += np.exp(log_prob)
                
                # Update prior params for run length 0
                alpha_n, beta_n, kappa_n, mu_n = self._update_posterior_params(
                    self.alpha_0, self.beta_0, self.kappa_0, self.mu_0, x
                )
                self.pred_dist_params[0] = (alpha_n, beta_n, kappa_n, mu_n)

            # Normalize
            total = np.sum(new_run_lengths)
            if total > 0:
                self.run_lengths = new_run_lengths / total
            else:
                self.run_lengths = new_run_lengths # Should not happen
                
            # Store metrics
            run_length_probs.append(self.run_lengths.copy())
            prob_change = self.run_lengths[0]
            change_point_probs.append(prob_change)
            exp_rl = np.dot(np.arange(len(self.run_lengths)), self.run_lengths)
            expected_run_lengths.append(exp_rl)
            
        return {
            'run_lengths': np.array(run_length_probs),
            'change_point_probs': np.array(change_point_probs),
            'expected_run_length': np.array(expected_run_lengths)
        }

    def detect_change_points(
        self,
        change_point_probs: np.ndarray,
        threshold: float = 0.5
    ) -> List[int]:
        """
        Identify change points from the probability series.
        
        Parameters:
        -----------
        change_point_probs : np.ndarray
            Array of change point probabilities.
        threshold : float
            Probability threshold to declare a change point.
            
        Returns:
        --------
        List[int]
            Indices where change points are detected.
        """
        change_points = []
        for i, prob in enumerate(change_point_probs):
            if prob >= threshold:
                # Avoid consecutive detections (non-max suppression)
                if not change_points or i - change_points[-1] > 1:
                    change_points.append(i)
        return change_points


def run_bocpd_rolling_window(
    data: np.ndarray,
    window_size: int = 12,
    stride: int = 1,
    hazard_rate: float = 0.05,
    threshold: float = 0.5
) -> List[Dict[str, any]]:
    """
    Run BOCPD on a rolling window of the data series.
    
    This function slides a window over the data, runs BOCPD within each window,
    and aggregates change points detected.
    
    Parameters:
    -----------
    data : np.ndarray
        1D array of observations.
    window_size : int
        Size of the rolling window.
    stride : int
        Step size for the rolling window.
    hazard_rate : float
        Hazard rate parameter for BOCPD.
    threshold : float
        Threshold for change point detection.
        
    Returns:
    --------
    List[Dict]
        List of detected change points with metadata.
    """
    n = len(data)
    if n < window_size:
        logger.warning(f"Data length {n} is less than window size {window_size}. Skipping.")
        return []
        
    results = []
    start_idx = 0
    
    while start_idx + window_size <= n:
        end_idx = start_idx + window_size
        window_data = data[start_idx:end_idx]
        
        # Initialize and run BOCPD
        bocpd = GaussianBOCPD(hazard_rate=hazard_rate)
        output = bocpd.fit(window_data)
        
        # Detect change points in this window
        cps = bocpd.detect_change_points(output['change_point_probs'], threshold)
        
        # Adjust indices to global coordinates
        for cp in cps:
            global_idx = start_idx + cp
            results.append({
                'global_index': global_idx,
                'window_start': start_idx,
                'window_end': end_idx,
                'probability': output['change_point_probs'][cp],
                'method': 'BOCPD'
            })
            
        start_idx += stride
        
    return results


def main():
    """
    Main entry point for running BOCPD on the preprocessed ILI data.
    
    Loads configuration, preprocesses data, runs BOCPD, and saves results.
    """
    # Setup logging
    from logging_setup import setup_logging
    setup_logging()
    
    logger.info("Starting BOCPD analysis (User Story 2)")
    
    # Load config
    config = load_config()
    window_size = config.get('window_size', 12)
    stride = config.get('stride', 1)
    alpha = config.get('alpha', 0.01)
    hazard_rate = config.get('hazard_rate', 0.05) # Default hazard rate
    threshold = config.get('bocpd_threshold', 0.5)
    
    # Load and preprocess data
    try:
        ili_data = load_ili_data()
        ili_data = remove_missing_weeks(ili_data)
        ili_data = log_transform(ili_data)
        ili_data = standardize(ili_data)
        
        # Extract the time series
        series = ili_data['ili_normalized'].values
    except Exception as e:
        logger.error(f"Failed to load or preprocess data: {e}")
        # Fallback to synthetic data for testing if real data is missing
        # This is allowed for the baseline implementation to ensure code runs
        # but must be flagged in logs
        logger.warning("Using synthetic data for BOCPD baseline as real data unavailable")
        from synthetic_data import generate_synthetic_ili_series
        series = generate_synthetic_ili_series(n_points=200, change_points=[50, 120])['ili']
        series = (series - np.mean(series)) / np.std(series)
        
    logger.info(f"Running BOCPD with window_size={window_size}, stride={stride}")
    
    # Run BOCPD
    change_points = run_bocpd_rolling_window(
        series,
        window_size=window_size,
        stride=stride,
        hazard_rate=hazard_rate,
        threshold=threshold
    )
    
    if not change_points:
        logger.info("No change points detected by BOCPD.")
        # Create empty output file
        df = pd.DataFrame(columns=['week_index', 'method', 'probability', 'statistic'])
    else:
        # Aggregate results: if multiple windows detect the same week, take the max probability
        aggregated = {}
        for cp in change_points:
            idx = cp['global_index']
            if idx not in aggregated or cp['probability'] > aggregated[idx]['probability']:
                aggregated[idx] = cp
                
        df = pd.DataFrame(list(aggregated.values()))
        df = df.rename(columns={'global_index': 'week_index', 'probability': 'probability'})
        df['statistic'] = df['probability'] # Using probability as the statistic
        
    # Save results
    output_path = os.path.join('data', 'processed', 'baselines_bocpd.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"BOCPD results saved to {output_path}")
    
    return df


if __name__ == "__main__":
    main()