import numpy as np
from typing import List, Tuple, Optional, Union

def calculate_metrics(errors: Union[List[float], np.ndarray]) -> dict:
    """
    Calculate error metrics (MAE, RMSE, MSE, Mean Signed Error).

    Args:
        errors: List or array of errors (DFT - Reference).

    Returns:
        Dictionary with MAE, RMSE, MSE, and Mean Signed Error.
    """
    errors = np.array(errors)
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors**2))
    mse = np.mean(errors**2)
    mse_signed = np.mean(errors)  # Mean Signed Error

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mse": float(mse),
        "mean_signed_error": float(mse_signed),
    }

def bootstrap_resample(
    data: Union[List[float], np.ndarray],
    n_replicates: int = 1000,
    random_state: Optional[int] = None,
) -> List[np.ndarray]:
    """
    Generate bootstrap resamples of the data.

    Args:
        data: Input data array.
        n_replicates: Number of resamples.
        random_state: Random seed for reproducibility.

    Returns:
        List of resampled arrays.
    """
    if random_state is not None:
        np.random.seed(random_state)
    data = np.array(data)
    n = len(data)
    resamples = []
    for _ in range(n_replicates):
        indices = np.random.choice(n, size=n, replace=True)
        resamples.append(data[indices])
    return resamples

def bootstrap_mean(
    data: Union[List[float], np.ndarray],
    n_replicates: int = 1000,
    random_state: Optional[int] = None,
) -> Tuple[float, float, float]:
    """
    Compute bootstrap estimate of the mean and 95% CI.

    Args:
        data: Input data array.
        n_replicates: Number of bootstrap replicates.
        random_state: Random seed.

    Returns:
        Tuple of (mean, ci_lower, ci_upper).
    """
    resamples = bootstrap_resample(data, n_replicates, random_state)
    means = [np.mean(r) for r in resamples]
    mean_est = np.mean(means)
    ci_lower = np.percentile(means, 2.5)
    ci_upper = np.percentile(means, 97.5)
    return mean_est, ci_lower, ci_upper

def bootstrap_mae(
    errors: Union[List[float], np.ndarray],
    n_replicates: int = 1000,
    random_state: Optional[int] = None,
) -> Tuple[float, float, float]:
    """
    Compute bootstrap estimate of MAE and 95% CI.

    Args:
        errors: Array of errors.
        n_replicates: Number of bootstrap replicates.
        random_state: Random seed.

    Returns:
        Tuple of (MAE, ci_lower, ci_upper).
    """
    resamples = bootstrap_resample(errors, n_replicates, random_state)
    maes = [np.mean(np.abs(r)) for r in resamples]
    mae_est = np.mean(maes)
    ci_lower = np.percentile(maes, 2.5)
    ci_upper = np.percentile(maes, 97.5)
    return mae_est, ci_lower, ci_upper