import numpy as np
from typing import List, Tuple, Optional, Union

def calculate_metrics(preds: List[float], refs: List[float]) -> dict:
    """Calculate MAE, RMSE, MSE, and MSE."""
    if len(preds) != len(refs) or len(preds) == 0:
        raise ValueError("Lists must be non-empty and of equal length")
    
    preds = np.array(preds)
    refs = np.array(refs)
    
    errors = preds - refs
    mae = np.mean(np.abs(errors))
    mse = np.mean(errors ** 2)
    rmse = np.sqrt(mse)
    me = np.mean(errors) # Mean Error (signed)
    
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mse": float(mse),
        "me": float(me)
    }

def bootstrap_resample(data: List[Union[int, float]], n_samples: int, rng: Optional[np.random.Generator] = None) -> List[List[Union[int, float]]]:
    """Generate n_samples bootstrap resamples of the input data."""
    if rng is None:
        rng = np.random.default_rng()
    
    data_arr = np.array(data)
    n = len(data_arr)
    resamples = []
    
    for _ in range(n_samples):
        indices = rng.integers(0, n, size=n)
        resamples.append(data_arr[indices].tolist())
    
    return resamples

def bootstrap_mean(data: List[float], n_replicates: int = 1000, rng: Optional[np.random.Generator] = None) -> Tuple[float, float]:
    """Compute bootstrap mean and 95% CI."""
    resamples = bootstrap_resample(data, n_replicates, rng)
    means = [np.mean(r) for r in resamples]
    mean_val = np.mean(means)
    ci_low = np.percentile(means, 2.5)
    ci_high = np.percentile(means, 97.5)
    return mean_val, (ci_low, ci_high)

def bootstrap_mae(preds: List[float], refs: List[float], n_replicates: int = 1000, rng: Optional[np.random.Generator] = None) -> Tuple[float, Tuple[float, float]]:
    """Compute bootstrap MAE and 95% CI."""
    if len(preds) != len(refs):
        raise ValueError("Preds and refs must be same length")
    
    n = len(preds)
    if rng is None:
        rng = np.random.default_rng()
    
    mae_values = []
    for _ in range(n_replicates):
        indices = rng.integers(0, n, size=n)
        p_sample = [preds[i] for i in indices]
        r_sample = [refs[i] for i in indices]
        mae_values.append(calculate_metrics(p_sample, r_sample)["mae"])
    
    mean_mae = np.mean(mae_values)
    ci_low = np.percentile(mae_values, 2.5)
    ci_high = np.percentile(mae_values, 97.5)
    
    return mean_mae, (ci_low, ci_high)
