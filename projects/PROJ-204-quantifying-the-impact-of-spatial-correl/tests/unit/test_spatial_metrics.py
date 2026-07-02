"""
Unit test for autocorrelation decay fit accuracy (T017).

Asserts deviation <= 5% against synthetic Gaussian noise with known correlation length.
"""
import numpy as np
from scipy import ndimage
from scipy.optimize import curve_fit

# Import from the project's analysis module
from code.analysis.spatial_metrics import compute_autocorrelation, fit_decay_model

def test_autocorrelation_decay_fit_accuracy():
    """
    Generate synthetic Gaussian noise with a known correlation length,
    compute autocorrelation, fit the decay model, and assert the fitted
    length is within 5% of the ground truth.
    """
    np.random.seed(42)
    
    # Parameters
    size = 256  # Increased size for better statistical stability
    true_sigma = 15.0  # Known correlation length (sigma)
    
    # Generate synthetic Gaussian random field with known correlation
    # We create white noise and convolve with a Gaussian kernel
    # The kernel standard deviation determines the correlation length
    kernel_sigma = true_sigma
    kernel_size = int(6 * kernel_sigma) + 1
    if kernel_size % 2 == 0:
        kernel_size += 1
        
    x = np.linspace(-3 * kernel_sigma, 3 * kernel_sigma, kernel_size)
    y = np.linspace(-3 * kernel_sigma, 3 * kernel_sigma, kernel_size)
    X, Y = np.meshgrid(x, y)
    kernel = np.exp(-(X**2 + Y**2) / (2 * kernel_sigma**2))
    kernel /= kernel.sum()
    
    white_noise = np.random.normal(0, 1, (size, size))
    correlated_field = ndimage.convolve(white_noise, kernel, mode='constant', cval=0.0)
    
    # Compute autocorrelation using the project's implementation
    autocorr = compute_autocorrelation(correlated_field)
    
    # Extract the radial average for fitting
    # We take the center row to analyze the decay profile
    center = size // 2
    row_slice = autocorr[center, :]
    
    # Normalize to 1 at lag 0
    if row_slice[0] > 0:
        row_slice = row_slice / row_slice[0]
    else:
        # Fallback if center value is non-positive (unlikely with proper normalization)
        row_slice = row_slice / np.max(row_slice)
    
    # Create distance array for the row (assuming isotropic, 1 pixel = 1 unit)
    distances = np.abs(np.arange(len(row_slice)) - center)
    
    # Fit decay model
    # We expect a Gaussian decay: exp(-r^2 / (2 * sigma_fit^2))
    try:
        fitted_params = fit_decay_model(distances, row_slice, model_type='gaussian')
        fitted_sigma = fitted_params['sigma']
        
        # Calculate deviation
        deviation = abs(fitted_sigma - true_sigma) / true_sigma
        
        assert deviation <= 0.05, (
            f"Decay fit accuracy failed. True sigma: {true_sigma}, "
            f"Fitted sigma: {fitted_sigma:.4f}, Deviation: {deviation:.4f} ({deviation*100:.2f}%). "
            f"Allowed deviation is <= 5%."
        )
        
    except Exception as e:
        # If fitting fails, it might be due to numerical issues or incorrect model assumption
        raise AssertionError(f"Fit model failed with error: {e}")

if __name__ == "__main__":
    test_autocorrelation_decay_fit_accuracy()
    print("Test passed: Autocorrelation decay fit accuracy within 5% tolerance.")