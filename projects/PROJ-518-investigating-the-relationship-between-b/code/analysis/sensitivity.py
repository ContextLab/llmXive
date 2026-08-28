import numpy as np
import pandas as pd
from typing import List, Tuple
from scipy import stats
from analysis.statistics import run_permutation_test
from config import get_config

def run_sensitivity_analysis(
    flexibility: np.ndarray,
    creativity: np.ndarray,
    window_lengths: List[int] = None
) -> pd.DataFrame:
    """
    Run sensitivity analysis across different window lengths.
    
    Computes correlation and p-value for each window length provided.
    Uses the global config for default window lengths if none provided.
    
    Args:
        flexibility: Array of network flexibility values (one per subject).
        creativity: Array of creativity scores (one per subject).
        window_lengths: List of window lengths to test. Defaults to config WINDOW_SIZES.
        
    Returns:
        pd.DataFrame with columns: window_length, correlation, p_value.
    """
    if window_lengths is None:
        config = get_config()
        window_lengths = config.WINDOW_SIZES
    
    results = []
    
    for window_len in window_lengths:
        # For this sensitivity analysis, we assume flexibility and creativity
        # are already computed. In a full pipeline, we might re-compute flexibility
        # for each window length, but the task description implies analyzing
        # the relationship across pre-defined window configurations.
        # 
        # Since the task asks for a table with correlation and p-value per window length,
        # and the inputs are already computed arrays, we interpret this as:
        # The flexibility array corresponds to a specific window configuration,
        # and we are testing the stability of the correlation across different
        # theoretical window lengths (perhaps from a prior multi-window computation).
        #
        # However, strictly following the task "run_sensitivity_analysis... returns a table
        # with columns window_length, correlation, p_value", and given that flexibility
        # is a single array here, the most logical interpretation in a real pipeline context
        # is that this function is called *per subject group* or that the flexibility
        # array passed is actually a matrix (subjects x windows), but the signature
        # suggests 1D arrays.
        #
        # Re-reading the task: "returns a table with columns window_length, correlation, p_value".
        # If we only have one flexibility array, we can only compute one correlation.
        # Therefore, the function likely implies that 'flexibility' here is a dictionary
        # or the caller computes flexibility for each window length before calling this.
        #
        # Let's look at the existing API surface for `run_sensitivity_analysis`.
        # It takes `flexibility` (np.ndarray) and `creativity` (np.ndarray).
        # This implies the caller has already computed flexibility for the specific
        # window length being tested, OR the function is expected to compute it.
        #
        # But `run_sensitivity_analysis` doesn't have access to raw fMRI data to re-compute.
        # It only has the summary statistics (flexibility, creativity).
        #
        # Correction: The task description for T046 says: "Implement ... run_sensitivity_analysis
        # ... that returns a table with columns window_length, correlation, p_value."
        # The existing API surface for `code/analysis/sensitivity.py` shows:
        # `def run_sensitivity_analysis(flexibility, creativity, window_lengths=[20,30,40]) -> pd.DataFrame`
        #
        # If the inputs are single arrays, we cannot compute correlations for multiple window lengths
        # unless the `flexibility` argument is actually a 2D array (subjects x windows) or a dict.
        # But the type hint says `np.ndarray`.
        #
        # Hypothesis: The function is intended to be called in a loop by the caller for each window,
        # OR the `flexibility` array passed here is actually a 2D array where columns correspond
        # to different window lengths.
        #
        # Given the signature `window_lengths: List[int]`, it strongly suggests the function
        # iterates over these lengths. This is only possible if `flexibility` contains data
        # for all these lengths.
        #
        # Let's assume `flexibility` is a 2D numpy array where shape is (n_subjects, n_windows).
        # If it's 1D, we can only compute one value, making the `window_lengths` argument useless.
        #
        # However, if the task implies that we should re-compute the correlation for different
        # window lengths, we need the raw data. Since we don't have raw data here, we must
        # assume `flexibility` is pre-computed for multiple windows.
        #
        # Let's check the type hint again: `flexibility: np.ndarray`. It doesn't specify dimension.
        # If it's 1D, we can't do the task as described with multiple window lengths.
        # If it's 2D, we can.
        #
        # Let's implement it assuming `flexibility` is 2D (n_subjects, n_windows) and
        # `window_lengths` corresponds to the columns. If it's 1D, we raise an error or handle it.
        #
        # Actually, a more robust interpretation for a "sensitivity analysis" function
        # in this context, given the constraints, is that the caller passes a dictionary
        # or the function is a wrapper that calls a lower-level function multiple times.
        # But the signature is fixed by the API surface.
        #
        # Let's reconsider the standard usage:
        # In many pipelines, `run_sensitivity_analysis` is a high-level function that
        # orchestrates the re-computation of metrics for different parameters.
        # But without raw data, it can't re-compute.
        #
        # Therefore, the only logical path is: `flexibility` is a 2D array where each column
        # corresponds to a window length in `window_lengths`.
        #
        # Implementation:
        if flexibility.ndim == 1:
            # If 1D, we can only compute for one window length.
            # We'll treat the single window length provided as the one used.
            if len(window_lengths) != 1:
                raise ValueError("If flexibility is 1D, window_lengths must contain exactly one value.")
            corr, p_val = stats.pearsonr(flexibility, creativity)
            results.append({
                "window_length": window_lengths[0],
                "correlation": corr,
                "p_value": p_val
            })
        elif flexibility.ndim == 2:
            if flexibility.shape[1] != len(window_lengths):
                raise ValueError(f"flexibility shape {flexibility.shape[1]} does not match window_lengths {len(window_lengths)}")
            
            for i, window_len in enumerate(window_lengths):
                col = flexibility[:, i]
                # Filter out NaNs if any
                valid_mask = ~(np.isnan(col) | np.isnan(creativity))
                if np.sum(valid_mask) < 3:
                    corr, p_val = np.nan, np.nan
                else:
                    corr, p_val = stats.pearsonr(col[valid_mask], creativity[valid_mask])
                
                results.append({
                    "window_length": window_len,
                    "correlation": corr,
                    "p_value": p_val
                })
        else:
            raise ValueError("flexibility must be 1D or 2D numpy array")
    
    return pd.DataFrame(results)
