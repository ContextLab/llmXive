import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Callable
from joblib import Parallel, delayed
import json
import os
from scipy import stats

from src.lib.config import get_config

def benjamini_hochberg_fdr(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction.
    T026 Implementation.
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return []
    
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # BH calculation
    ranks = np.arange(1, n + 1)
    corrected = (sorted_p * n) / ranks
    
    # Ensure monotonicity (cumulative min from the back)
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    corrected = np.minimum(corrected, 1.0)
    
    # Restore original order
    result = np.empty(n)
    result[sorted_indices] = corrected
    return result.tolist()

def bootstrap_confidence_interval(data: np.ndarray, n_bootstrap: int = 1000, seed: int = 42) -> Tuple[float, float]:
    """
    Generate bootstrap confidence intervals.
    T033 Implementation.
    """
    rng = np.random.default_rng(seed)
    boot_means = []
    for _ in range(n_bootstrap):
        sample = rng.choice(data, size=len(data), replace=True)
        boot_means.append(np.mean(sample))
    
    return np.percentile(boot_means, 2.5), np.percentile(boot_means, 97.5)

def run_permutation_test_early_stop(
    data: np.ndarray, 
    n_shuffles: int = 10000, 
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run permutation test with early stop flag (for reporting only).
    T025/T032 Implementation.
    SC-005 Optimization: Uses joblib for parallelization (n_jobs=1 as per spec constraint).
    """
    config = get_config()
    rng = np.random.default_rng(seed)
    
    observed_stat = np.mean(data) # Placeholder statistic
    null_stats = []
    
    # Early stop tracking
    early_stop_flag = False
    interim_p = 1.0
    
    # Optimization: Vectorize shuffling if possible, but loop is safer for complex stats
    # Spec requires n_jobs=1 and batch_size=100 for CI budget compliance
    
    # We simulate the parallel joblib call structure
    def shuffle_batch(start_idx: int, end_idx: int, rng_seed: int) -> List[float]:
        local_rng = np.random.default_rng(rng_seed)
        batch_stats = []
        for _ in range(end_idx - start_idx):
            # Shuffle data
            shuffled = local_rng.permutation(data)
            batch_stats.append(np.mean(shuffled))
        return batch_stats

    # Run in chunks to manage memory and allow early checking
    batch_size = 100
    total_batches = n_shuffles // batch_size
    
    for i in range(total_batches):
        start = i * batch_size
        end = (i + 1) * batch_size
        
        # Parallel execution (n_jobs=1 per spec)
        results = Parallel(n_jobs=1, batch_size=100)(
            [delayed(shuffle_batch)(start, end, seed + i) for _ in range(1)]
        )
        
        batch_stats = results[0]
        null_stats.extend(batch_stats)
        
        # Check early stop condition (T025 logic)
        if (i + 1) * batch_size >= 100: # Check after 100
            count_extreme = sum(1 for s in null_stats if abs(s) >= abs(observed_stat))
            interim_p = count_extreme / len(null_stats)
            if interim_p < 0.001:
                early_stop_flag = True
                # Spec says: CONTINUE to full 10000, flag is for reporting only
    
    # Final p-value
    count_extreme = sum(1 for s in null_stats if abs(s) >= abs(observed_stat))
    final_p = count_extreme / len(null_stats)
    
    return {
        "n_shuffles": n_shuffles,
        "early_stop_flag": early_stop_flag,
        "interim_p": interim_p,
        "final_p_value": final_p,
        "observed_stat": observed_stat
    }

def save_permutation_results(results: Dict[str, Any], path: str) -> None:
    """Save permutation results to JSON."""
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
