import numpy as np
import pandas as pd
from typing import List, Dict, Any
from scipy import stats
from config import get_config
from analysis.statistics import run_permutation_test

def run_sensitivity_analysis(
    flexibility: np.ndarray,
    creativity: np.ndarray,
    window_lengths: List[int] = None
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by computing Pearson correlation and permutation p-values
    across different window lengths.

    Args:
        flexibility: Array of flexibility scores (currently static, but this function
                     is structured to accept window-specific flexibility if provided later).
                     For this implementation, we assume flexibility is calculated per
                     participant and we are testing the stability of the correlation
                     statistic across hypothetical window parameters or re-calculating
                     if the input flexibility was window-specific.
                     NOTE: In the current pipeline context, 'flexibility' is a single
                     array per participant. To perform a sensitivity analysis on
                     'window_lengths', we must re-calculate flexibility for each window
                     length. However, this function signature takes 'flexibility' as
                     input.
                     
                     To satisfy the task requirement of returning correlations for 
                     different window lengths, we assume the caller (or a wrapper) 
                     has already computed flexibility for each window length, OR we 
                     interpret this task as: "If we had flexibility calculated for these 
                     windows, what would the stats be?".
                     
                     CRITICAL INTERPRETATION FOR REAL IMPLEMENTATION:
                     The task asks to return p-values and correlations for each window length.
                     Since 'flexibility' is passed as a single array, we cannot re-calculate
                     it here without the raw fMRI data. 
                     
                     However, looking at the dependency T027 (run_permutation_test) and the 
                     nature of sensitivity analysis in this context: often it implies 
                     checking if the result holds under different parameters. 
                     
                     If the 'flexibility' array passed here was actually the result of 
                     T016 (calculate_flexibility) which averages across ROIs, it is a 
                     single value per participant. 
                     
                     To make this function functional and return a list of values for 
                     different window lengths, we must assume that the 'flexibility' 
                     argument is actually a 2D array (n_participants, n_windows) or 
                     that we are re-running the correlation on the *same* flexibility 
                     but checking robustness? No, that yields the same result.
                     
                     RE-READING TASK T046: "Implement ... that returns a dictionary 
                     containing a list of p-values and correlations for each window length."
                     
                     This implies the correlation changes with window length. Therefore, 
                     the 'flexibility' input must vary by window length. 
                     Since the function signature in the API surface provided is:
                     `from analysis.sensitivity import run_sensitivity_analysis`
                     and imports `from analysis.statistics import run_permutation_test`.
                     
                     We must assume that the 'flexibility' argument is a list of arrays, 
                     or a 2D array where columns correspond to window lengths, OR we 
                     need to fetch the raw data to re-calculate.
                     
                     Given the constraint "Extend, don't re-author" and the existing 
                     API, and the fact that T016 produces a single float per participant,
                     the only way to get multiple correlations is if the input 'flexibility'
                     is actually a matrix of flexibility scores for different windows.
                     
                     However, if the input is a 1D array (current state of T016 output),
                     we cannot produce multiple correlations without re-running the 
                     dynamics pipeline (T014->T015->T016) for each window.
                     
                     Let's look at the dependencies again. T046 depends on T027.
                     T027 is `run_permutation_test`.
                     
                     If the system expects us to re-calculate flexibility, we would need
                     access to the raw fMRI data or the sliding window matrices. 
                     The `code/analysis/connectivity.py` has `compute_sliding_window_connectivity`.
                     
                     Let's assume the 'flexibility' argument in this specific function 
                     call is actually a list of flexibility arrays, one for each window 
                     length, OR the function is expected to handle the re-calculation 
                     if raw data was available. 
                     
                     Since we cannot access raw data here without passing it, and the 
                     signature is fixed, we must assume the input 'flexibility' is 
                     actually a 2D array (n_samples, n_windows) or a list of arrays.
                     
                     ALTERNATIVE: The task might be testing the sensitivity of the 
                     *permutation test* itself or the correlation of a static metric 
                     across windows? No, the correlation is between flexibility and creativity.
                     
                     Correct Interpretation for the Code:
                     The function must iterate over `window_lengths`.
                     For each window length, it needs a corresponding flexibility vector.
                     If the input `flexibility` is a single vector, this task cannot 
                     produce a list of correlations unless we re-calculate flexibility.
                     
                     Let's assume the input `flexibility` is actually a dictionary or 
                     list of arrays mapped to window lengths, OR we need to re-calculate.
                     
                     Given the strict "real code" constraint and the fact that we don't 
                     have raw fMRI data in this function's scope, we will implement 
                     the logic assuming `flexibility` is a 2D array where columns 
                     correspond to the window lengths provided (or we map them).
                     
                     WAIT: The task says "returns a dictionary containing a list of 
                     p-values and correlations for each window length".
                     If we only have one flexibility vector, the correlation is the same.
                     Therefore, the input `flexibility` MUST be a collection of vectors.
                     
                     We will implement it to accept `flexibility` as a List[np.ndarray] 
                     or a 2D np.ndarray. If it's 1D, we cannot fulfill the "list of 
                     correlations" requirement without re-computation which requires 
                     raw data. 
                     
                     However, to be robust and match the likely intent of the pipeline 
                     (where T014.1/014.2 might have been run for multiple windows), 
                     we will assume `flexibility` is a 2D array (n_participants, n_windows)
                     and `window_lengths` aligns with the columns.
                     
                     If the input is 1D, we will raise an error or return a single 
                     value repeated (which is logically wrong). 
                     
                     Let's assume the caller provides `flexibility` as a 2D array 
                     (n_subjects, n_windows) corresponding to the `window_lengths`.
                     
    Args:
        flexibility: 2D numpy array of shape (n_subjects, n_windows) OR a list of 1D arrays.
        creativity: 1D numpy array of shape (n_subjects,).
        window_lengths: List of integers representing the window sizes used.

    Returns:
        Dict: {
            'p_values': List[float],
            'correlations': List[float],
            'window_lengths': List[int]
        }
    """
    config = get_config()
    
    # Handle input flexibility: ensure it's a list of arrays
    if isinstance(flexibility, np.ndarray):
        if flexibility.ndim == 1:
            # If only one window was provided but we need to sweep, 
            # we cannot do it without raw data. We will assume the input
            # is actually a list of arrays if multiple windows are needed.
            # If it's 1D and window_lengths has >1 item, we must fail or assume
            # the user made a mistake. 
            # However, to make the code runnable as a "sensitivity" tool,
            # we assume the input flexibility is a 2D array where columns are windows.
            if flexibility.shape[1] != len(window_lengths):
                raise ValueError(
                    f"Flexibility array shape {flexibility.shape} does not match "
                    f"window_lengths count {len(window_lengths)}. "
                    "Expected 2D array (n_subjects, n_windows)."
                )
            flex_list = [flexibility[:, i] for i in range(flexibility.shape[1])]
        else:
            flex_list = [flexibility[:, i] for i in range(flexibility.shape[1])]
    elif isinstance(flexibility, list):
        flex_list = flexibility
    else:
        raise TypeError("Flexibility must be a numpy array or list of arrays.")

    if len(flex_list) != len(window_lengths):
        raise ValueError(
            f"Number of flexibility vectors ({len(flex_list)}) must match "
            f"number of window_lengths ({len(window_lengths)})."
        )

    p_values = []
    correlations = []

    for i, (win_len, flex_vec) in enumerate(zip(window_lengths, flex_list)):
        # Ensure arrays are valid
        if len(flex_vec) != len(creativity):
            raise ValueError(f"Length mismatch at window {win_len}: flex={len(flex_vec)}, creat={len(creativity)}")
        
        # Calculate Pearson correlation
        corr, p_val = stats.pearsonr(flex_vec, creativity)
        
        # Run permutation test for robust p-value
        # T027 dependency: run_permutation_test(flexibility, creativity, n_permutations=10000)
        perm_result = run_permutation_test(flex_vec, creativity, n_permutations=10000)
        
        # Use the empirical p-value from permutation if available, else the parametric one
        # The task asks for p-values. Permutation is more robust.
        perm_p = perm_result.get('empirical_p_value', p_val)
        
        correlations.append(corr)
        p_values.append(perm_p)

    return {
        'p_values': p_values,
        'correlations': correlations,
        'window_lengths': window_lengths
    }
