"""
Metrics computation module for intra-modal consistency.

Implements cross-correlation logic to measure synchrony between facial and vocal
modalities over time.
"""
import numpy as np
from typing import Optional, Tuple
from logging_config import get_logger
from utils import handle_corrupted_file

logger = get_logger(__name__)

def validate_feature_input(signal_a: np.ndarray, signal_b: np.ndarray) -> None:
    """
    Validate that input signals are numpy arrays of the same length.
    
    Args:
        signal_a: First time-series signal.
        signal_b: Second time-series signal.
        
    Raises:
        ValueError: If inputs are not numpy arrays or lengths differ.
    """
    if not isinstance(signal_a, np.ndarray) or not isinstance(signal_b, np.ndarray):
        raise ValueError("Both inputs must be numpy arrays.")
    
    if len(signal_a) != len(signal_b):
        raise ValueError(f"Signal lengths must match: got {len(signal_a)} and {len(signal_b)}")
    
    if len(signal_a) == 0:
        raise ValueError("Signals cannot be empty.")

def compute_max_abs_cross_correlation(
    signal_a: np.ndarray, 
    signal_b: np.ndarray, 
    max_lag_samples: Optional[int] = None
) -> Tuple[float, int]:
    """
    Compute the maximum absolute cross-correlation and the optimal lag between two signals.
    
    This function calculates the cross-correlation between two time-series signals
    and returns the maximum absolute correlation value and the lag (in samples)
    at which it occurs.
    
    Args:
        signal_a: First time-series signal (e.g., facial valence).
        signal_b: Second time-series signal (e.g., vocal pitch).
        max_lag_samples: Maximum lag to consider in samples. If None, uses half the signal length.
        
    Returns:
        Tuple containing:
            - max_corr: The maximum absolute correlation coefficient.
            - optimal_lag: The lag (in samples) at which max_corr occurs.
    
    Raises:
        ValueError: If input validation fails.
    """
    # Validate inputs
    validate_feature_input(signal_a, signal_b)
    
    # Normalize signals to zero mean and unit variance for correlation
    norm_a = (signal_a - np.mean(signal_a)) / (np.std(signal_a) * len(signal_a))
    norm_b = (signal_b - np.mean(signal_b)) / (np.std(signal_b) * len(signal_b))
    
    # Determine max lag
    n = len(signal_a)
    if max_lag_samples is None:
        max_lag = n // 2
    else:
        max_lag = min(max_lag_samples, n // 2)
    
    # Compute cross-correlation using FFT for efficiency
    # We compute full cross-correlation then slice to relevant lags
    cross_corr = np.correlate(norm_a, norm_b, mode='full')
    
    # The full cross-correlation has length 2n - 1
    # The center (index n-1) corresponds to lag 0
    # We need indices corresponding to lags [-max_lag, max_lag]
    start_idx = (n - 1) - max_lag
    end_idx = (n - 1) + max_lag + 1
    
    relevant_corr = cross_corr[start_idx:end_idx]
    lags = np.arange(-max_lag, max_lag + 1)
    
    # Find the index of the maximum absolute correlation
    max_abs_idx = np.argmax(np.abs(relevant_corr))
    max_corr = np.abs(relevant_corr[max_abs_idx])
    optimal_lag = lags[max_abs_idx]
    
    logger.debug(f"Computed cross-correlation: max_abs={max_corr:.4f}, lag={optimal_lag}")
    
    return max_corr, int(optimal_lag)

def compute_consistency_score(
    signal_a: np.ndarray, 
    signal_b: np.ndarray, 
    max_lag_seconds: Optional[float] = None,
    sampling_rate: float = 10.0
) -> float:
    """
    Compute the intra-modal consistency score between two signals.
    
    The consistency score is defined as the maximum absolute cross-correlation
    within a specified time lag window.
    
    Args:
        signal_a: First time-series signal.
        signal_b: Second time-series signal.
        max_lag_seconds: Maximum lag to consider in seconds. If None, uses 2.0 seconds.
        sampling_rate: Sampling rate of the signals in Hz.
        
    Returns:
        The consistency score (maximum absolute correlation).
    """
    if max_lag_seconds is None:
        max_lag_seconds = 2.0
        
    max_lag_samples = int(max_lag_seconds * sampling_rate)
    
    try:
        max_corr, _ = compute_max_abs_cross_correlation(
            signal_a, signal_b, max_lag_samples
        )
        return max_corr
    except ValueError as e:
        logger.error(f"Error computing consistency score: {e}")
        return 0.0

def process_interaction_features(
    features_df: 'pd.DataFrame', 
    modality_a: str, 
    modality_b: str
) -> 'pd.DataFrame':
    """
    Process a DataFrame of interaction features to compute consistency scores.
    
    Args:
        features_df: DataFrame containing time-series data for multiple interactions.
        modality_a: Column name prefix for modality A signals.
        modality_b: Column name prefix for modality B signals.
        
    Returns:
        DataFrame with added 'consistency_score' column.
    """
    import pandas as pd
    
    results = []
    
    for idx, row in features_df.iterrows():
        try:
            # Extract signals assuming columns are named like 'facial_valence_t0', 'facial_valence_t1'...
            # This is a simplified example; actual implementation would depend on data format
            signal_a = row[[c for c in row.index if modality_a in c]].values.astype(float)
            signal_b = row[[c for c in row.index if modality_b in c]].values.astype(float)
            
            score = compute_consistency_score(signal_a, signal_b)
            results.append({'interaction_id': idx, 'consistency_score': score})
            
        except Exception as e:
            logger.warning(f"Failed to process interaction {idx}: {e}")
            handle_corrupted_file(f"interaction_{idx}", e)
            results.append({'interaction_id': idx, 'consistency_score': np.nan})
    
    return pd.DataFrame(results)

if __name__ == '__main__':
    # Simple demo to verify the module runs
    np.random.seed(42)
    t = np.linspace(0, 10, 100)
    s1 = np.sin(t)
    s2 = np.sin(t + 0.5)
    
    corr, lag = compute_max_abs_cross_correlation(s1, s2)
    print(f"Demo: Max Correlation = {corr:.4f}, Lag = {lag}")
    
    score = compute_consistency_score(s1, s2)
    print(f"Demo: Consistency Score = {score:.4f}")