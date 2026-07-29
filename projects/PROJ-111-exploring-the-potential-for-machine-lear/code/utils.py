import numpy as np
from typing import List, Tuple, Dict, Optional
import warnings

def calculate_autocorrelation_time(series: np.ndarray) -> float:
    """Calculates the integrated autocorrelation time of a series."""
    window_size = len(series) // 2
    autocorr = np.correlate(series, series, mode='full')
    autocorr = autocorr[len(series)-1:]  # Keep only positive lags
    autocorr = autocorr / np.max(autocorr)
    tau_int = 0
    for i in range(window_size):
        tau_int += autocorr[i]

    return tau_int

def thin_dataset(series: np.ndarray, thinning_factor: int) -> np.ndarray:
    """Thins a dataset by a given factor."""
    if thinning_factor <= 0:
        raise ValueError("Thinning factor must be greater than zero.")
    return series[::thinning_factor]

def calculate_magnetic_susceptibility(spins: np.ndarray) -> float:
    """Calculates the magnetic susceptibility for a spin configuration."""
    # Calculate total magnetization
    magnetization = np.sum(spins)
    # Calculate squared magnetization
    squared_magnetization = magnetization**2
    # Calculate magnetic susceptibility (proportional to variance of magnetization)
    chi = squared_magnetization / spins.size # Placeholder value, needs refinement based on model details

    return chi

def perform_finite_size_scaling(data: List[float], lattice_sizes: List[int]) -> float:
    """Performs finite-size scaling to extrapolate T* to the thermodynamic limit."""
    # This is a placeholder implementation. A more sophisticated approach would involve fitting data to a theoretical model.
    # For example, using a power law with exponent nu.

    # Example: simple linear extrapolation
    if len(data) != len(lattice_sizes):
        raise ValueError("Data and lattice sizes lists must have the same length.")

    # Perform linear regression
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(np.log(lattice_sizes), data)

    # Extrapolate to infinite size (L -> infinity)
    t_star = intercept # placeholder
    return t_star

def find_peak_temperature(variance_data: List[float], temperatures: List[float]) -> float:
    """Finds the peak temperature in a variance curve."""
    if len(variance_data) != len(temperatures):
        raise ValueError("Variance data and temperatures lists must have the same length.")

    # Find the index of the maximum variance
    peak_index = np.argmax(variance_data)

    # Return the corresponding temperature
    return temperatures[peak_index]

def calculate_latent_variance(latent_vectors: List[np.ndarray]) -> float:
      """Calculates the total latent variance."""
      total_variance = 0.0
      for vector in latent_vectors:
          total_variance += np.var(vector)
      return total_variance