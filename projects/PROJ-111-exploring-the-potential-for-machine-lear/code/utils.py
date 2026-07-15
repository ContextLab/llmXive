"""
utils.py - Statistical utilities for Monte Carlo analysis.

Implements:
- Integrated autocorrelation time (tau_int) calculation
- Data thinning based on tau_int
- Magnetic susceptibility (chi) calculation
- Finite-size scaling (FSS) extrapolation for T*
"""
import numpy as np
from typing import List, Tuple, Dict, Optional
import warnings

def calculate_autocorrelation_time(
    data: np.ndarray,
    max_lag: Optional[int] = None,
    window_factor: float = 5.0
) -> float:
    """
    Calculate the integrated autocorrelation time (tau_int) for a 1D time series.
    
    Uses the standard windowing method: integrate the autocorrelation function
    up to a window where the noise dominates.
    
    Args:
        data: 1D array of measurements (e.g., energy, magnetization).
        max_lag: Maximum lag to consider. Defaults to len(data)//2.
        window_factor: Factor to determine window size (tau_int * window_factor).
        
    Returns:
        Estimated integrated autocorrelation time.
    """
    n = len(data)
    if n < 10:
        return 1.0
    
    # Normalize data to zero mean
    mean = np.mean(data)
    var = np.var(data)
    if var == 0:
        return 1.0
    
    data_centered = data - mean
    
    # Calculate autocorrelation function (ACF)
    # Using FFT for efficiency if data is large
    if n > 1000:
        # FFT-based ACF
        f = np.fft.rfft(data_centered, n=2*n)
        acf = np.fft.irfft(f * np.conj(f))[:n]
        acf = acf / acf[0]  # Normalize
    else:
        # Direct calculation for small arrays
        acf = np.correlate(data_centered, data_centered, mode='full')
        acf = acf[n-1:]
        acf = acf / acf[0]
    
    # Integrate ACF with windowing
    tau_int = 0.5
    window = int(window_factor)
    
    if max_lag is None:
        max_lag = n // 2
    
    for t in range(1, min(max_lag, n)):
        if t > window * tau_int:
            break
        if acf[t] < 0:
            break
        tau_int += acf[t]
    
    return max(1.0, tau_int)


def thin_dataset(
    data: np.ndarray,
    tau_int: float,
    min_thin_factor: int = 2
) -> np.ndarray:
    """
    Thin a dataset to reduce autocorrelation.
    
    Args:
        data: 1D array of measurements.
        tau_int: Integrated autocorrelation time.
        min_thin_factor: Minimum thinning factor (default 2 * tau_int).
        
    Returns:
        Thinned dataset.
    """
    thin_factor = max(min_thin_factor, int(2 * tau_int))
    return data[::thin_factor]


def calculate_magnetic_susceptibility(
    spins: np.ndarray,
    beta: float
) -> float:
    """
    Calculate magnetic susceptibility (chi) for a spin configuration.
    
    chi = (beta / N) * ( <M^2> - <M>^2 )
    where M is the total magnetization.
    
    Args:
        spins: Array of shape (N_samples, 3, L, L) or (N_samples, L, L) for XY.
               For Heisenberg: 3 components (x, y, z).
               For XY: 1 component or (L, L) with angle.
        beta: Inverse temperature (1/T).
        
    Returns:
        Magnetic susceptibility.
    """
    if spins.ndim == 4:
        # Heisenberg model: (N, 3, L, L)
        # Total magnetization vector
        M_vec = np.sum(spins, axis=(2, 3))  # (N, 3)
        M_sq = np.sum(M_vec**2, axis=1)     # (N,)
        M = np.sqrt(M_sq)                   # Magnitude (N,)
    elif spins.ndim == 3:
        # XY model or single component: (N, L, L)
        M_vec = np.sum(spins, axis=(1, 2))  # (N,)
        M_sq = M_vec**2
        M = np.abs(M_vec)
    else:
        raise ValueError(f"Expected 3D or 4D spins array, got {spins.ndim}D")
    
    N_samples = len(M)
    if N_samples == 0:
        return 0.0
    
    mean_M = np.mean(M)
    mean_M_sq = np.mean(M_sq)
    
    # chi = (beta / N) * ( <M^2> - <M>^2 )
    # N here is the number of spins in the lattice (L*L)
    # But for susceptibility per spin, we use the lattice size
    if spins.ndim == 4:
        lattice_size = spins.shape[2] * spins.shape[3]
    else:
        lattice_size = spins.shape[1] * spins.shape[2]
    
    chi = (beta / lattice_size) * (mean_M_sq - mean_M**2)
    return chi


def perform_finite_size_scaling(
    T_list: List[float],
    chi_list: List[float],
    L_list: List[int],
    nu: float = 1.0
) -> Dict[str, float]:
    """
    Perform finite-size scaling to extrapolate T* to the thermodynamic limit.
    
    Uses the scaling form: T*(L) = T_c + a * L^(-1/nu)
    
    Args:
        T_list: List of pseudo-critical temperatures for each L.
        chi_list: List of peak susceptibility values (not directly used in fit).
        L_list: List of lattice sizes.
        nu: Critical exponent (default 1.0 for 2D Ising/XY).
        
    Returns:
        Dictionary with:
            - 'T_c': Extrapolated critical temperature (L->inf)
            - 'a': Fitting parameter
            - 'R2': R-squared of the fit
    """
    if len(T_list) < 2:
        raise ValueError("Need at least 2 lattice sizes for FSS")
    
    T_list = np.array(T_list)
    L_list = np.array(L_list)
    
    # Transform: T*(L) vs L^(-1/nu)
    x = L_list ** (-1.0 / nu)
    y = T_list
    
    # Linear regression: y = a*x + T_c
    # Using least squares
    A = np.vstack([x, np.ones(len(x))]).T
    a, T_c = np.linalg.lstsq(A, y, rcond=None)[0]
    
    # Calculate R-squared
    y_pred = a * x + T_c
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    R2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return {
        'T_c': float(T_c),
        'a': float(a),
        'R2': float(R2),
        'nu_fixed': nu
    }


def find_peak_temperature(
    T_list: List[float],
    values: List[float]
) -> Tuple[float, float]:
    """
    Find the temperature at which values peak.
    
    Args:
        T_list: List of temperatures.
        values: List of values (e.g., susceptibility, latent variance).
        
    Returns:
        Tuple of (peak_temperature, peak_value)
    """
    T_list = np.array(T_list)
    values = np.array(values)
    
    idx = np.argmax(values)
    return float(T_list[idx]), float(values[idx])


def calculate_latent_variance(
    latent_means: np.ndarray
) -> float:
    """
    Calculate total latent variance (sum of variances across latent dimensions).
    
    Args:
        latent_means: Array of shape (N_samples, latent_dim)
        
    Returns:
        Sum of variances across all latent dimensions.
    """
    if latent_means.ndim != 2:
        raise ValueError(f"Expected 2D latent_means, got {latent_means.ndim}D")
    
    return float(np.sum(np.var(latent_means, axis=0)))