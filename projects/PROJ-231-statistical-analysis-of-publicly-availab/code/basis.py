import numpy as np
from scipy.interpolate import LSQUnivariateSpline, UnivariateSpline
from scipy.special import loggamma
from scipy.linalg import pinv2
import logging
from pathlib import Path

from config import get_data_dir, get_project_root

# Configure logging
logger = logging.getLogger(__name__)

def select_optimal_basis_dimension(y, x, max_k=50, min_k=5):
    """
    Select optimal basis dimension K using Generalized Cross-Validation (GCV).
    """
    best_k = min_k
    best_gcv = float('inf')
    
    # Use a subset of knots for pilot selection if data is large
    n = len(x)
    if n > 200:
        # Subsample for pilot selection to save time
        indices = np.linspace(0, n-1, 200, dtype=int)
        x_sub, y_sub = x[indices], y[indices]
    else:
        x_sub, y_sub = x, y

    for k in range(min_k, min(max_k, n) + 1):
        try:
            # Equally spaced knots for simplicity in pilot selection
            # Number of knots = k + 2 (for cubic B-splines with boundary conditions)
            num_knots = k + 2
            if num_knots > len(x_sub):
                continue
            
            # Generate internal knots
            t_min, t_max = x_sub.min(), x_sub.max()
            internal_knots = np.linspace(t_min, t_max, num_knots - 2)[1:-1]
            # Full knot sequence with boundary knots repeated 4 times (cubic)
            t = np.concatenate(([t_min]*4, internal_knots, [t_max]*4))
            
            if len(t) < k + 4:
                continue

            spline = UnivariateSpline(x_sub, y_sub, k=3, t=t, s=None) # s=None triggers GCV
            
            # Calculate GCV score manually or use the one from the spline
            # UnivariateSpline stores the GCV score in the _data attribute if s=None
            # However, accessing private attributes is fragile. 
            # We approximate GCV as: RSS / (n * (1 - d/n)^2) where d is degrees of freedom
            # UnivariateSpline has a .get_residual() and .get_knots()
            
            # Let's use the built-in GCV if available, otherwise calculate RSS/DoF
            # UnivariateSpline with s=None optimizes for GCV. The score is not directly exposed.
            # We will use the residual sum of squares and the effective degrees of freedom.
            rss = spline.get_residual()
            # Effective degrees of freedom for smoothing splines is often approximated
            # by the trace of the smoother matrix. 
            # For UnivariateSpline, we can estimate k as the number of non-zero coefficients roughly.
            # A safer bet for pilot is to just minimize RSS for a fixed k if we can't get GCV easily.
            # But the spec asks for GCV/AIC.
            
            # Let's try LSQUnivariateSpline which takes knots explicitly and we can compute AIC/GCV
            # But LSQ requires fixed knots.
            # Let's stick to UnivariateSpline and use the 's' parameter logic.
            # If we fix k, we want the best 's'.
            # Actually, the task is to select K.
            # We will use the number of non-zero coefficients as a proxy for complexity if needed.
            # Let's assume the standard approach: minimize GCV.
            # UnivariateSpline minimizes GCV internally when s=None.
            # We can't easily get the GCV value.
            
            # Alternative: Use LSQUnivariateSpline with fixed knots and compute AIC.
            # AIC = n * log(RSS/n) + 2 * df
            # df approx = number of knots + 4 (for cubic) - 1 (mean)? 
            # Let's use the number of basis functions = k.
            
            # Re-implementation using LSQ for explicit K control
            if k > len(x_sub):
                continue
            
            # Create knots for LSQ
            # We need k internal knots for a basis of size k+4? 
            # Or k is the number of basis functions?
            # Usually K is the dimension of the basis.
            # For cubic splines, dimension = number of internal knots + 4.
            # So if we want dimension K, we need K-4 internal knots.
            num_internal = k - 4
            if num_internal < 0:
                continue
            
            if num_internal == 0:
                knots = []
            else:
                knots = np.linspace(t_min, t_max, num_internal + 2)[1:-1]
            
            t_ls = np.concatenate(([t_min]*4, knots, [t_max]*4))
            
            try:
                spline_ls = LSQUnivariateSpline(x_sub, y_sub, t_ls)
                rss = spline_ls.get_residual()
                n_sub = len(x_sub)
                # AIC = n * log(RSS/n) + 2 * k
                aic = n_sub * np.log(rss / n_sub) + 2 * k
                
                if aic < best_gcv: # Using AIC as the metric here
                    best_gcv = aic
                    best_k = k
            except Exception:
                continue

        except Exception as e:
            continue

    return best_k

def pilot_basis_selection(X_data):
    """
    Pilot selection of global basis dimension K across the ensemble.
    """
    logger.info("Running pilot basis selection...")
    # X_data is a 2D array (n_samples, n_timepoints) or list of arrays
    # We sample a few rows to estimate optimal K
    if isinstance(X_data, list):
        samples = X_data[:10] if len(X_data) > 10 else X_data
        # Flatten to get a representative set of curves
        all_x, all_y = [], []
        # Assume time points are uniform and shared? 
        # If not, we need to handle differently. 
        # For pilot, let's assume we have a representative curve.
        # We'll just pick the first one if available.
        if len(samples) > 0:
            y_rep = samples[0]
            x_rep = np.arange(len(y_rep))
            k_opt = select_optimal_basis_dimension(y_rep, x_rep)
            logger.info(f"Selected optimal basis dimension K={k_opt} from pilot.")
            return k_opt
    else:
        # Assume X_data is (n, t)
        if X_data.shape[0] > 0:
            y_rep = X_data[0]
            x_rep = np.arange(len(y_rep))
            k_opt = select_optimal_basis_dimension(y_rep, x_rep)
            logger.info(f"Selected optimal basis dimension K={k_opt} from pilot.")
            return k_opt
    
    logger.warning("Could not determine optimal K, using default 10.")
    return 10

def expand_to_b_spline(y, x, k_dim):
    """
    Expand a single time-series y at points x into B-spline basis with dimension k_dim.
    Returns coefficients and the basis functions evaluated at x (for reconstruction check).
    """
    t_min, t_max = x.min(), x.max()
    num_internal = k_dim - 4
    if num_internal < 0:
        num_internal = 0
    
    if num_internal > 0:
        knots = np.linspace(t_min, t_max, num_internal + 2)[1:-1]
    else:
        knots = []
    
    t = np.concatenate(([t_min]*4, knots, [t_max]*4))
    
    try:
        spline = LSQUnivariateSpline(x, y, t)
        coeffs = spline._data[11] # Coefficients are in the 11th element of _data
        # Reconstruct to verify
        y_recon = spline(x)
        return coeffs, y_recon, spline
    except Exception as e:
        logger.error(f"Failed to fit B-spline: {e}")
        raise

def expand_ensemble_to_b_spline(ensemble_data, time_points, k_dim):
    """
    Expand an ensemble of time-series to B-spline coefficients.
    ensemble_data: list of arrays or 2D array
    time_points: 1D array of time coordinates
    k_dim: basis dimension
    """
    logger.info(f"Expanding ensemble to B-spline with K={k_dim}...")
    all_coeffs = []
    all_recon = []
    
    for i, y in enumerate(ensemble_data):
        try:
            coeffs, y_recon, _ = expand_to_b_spline(y, time_points, k_dim)
            all_coeffs.append(coeffs)
            all_recon.append(y_recon)
        except Exception as e:
            logger.error(f"Error processing ensemble member {i}: {e}")
            # Skip or handle error? 
            # For now, raise to fail loudly as per constraints
            raise e
    
    return np.array(all_coeffs), np.array(all_recon)

def reconstruct_and_verify(coeffs, time_points, k_dim, original_data, tolerance=0.01):
    """
    Reconstruct curves from coefficients and verify MSE <= tolerance.
    """
    logger.info("Reconstructing curves and verifying MSE...")
    
    if len(coeffs) == 0:
        logger.error("No coefficients to reconstruct.")
        return False, 0.0

    t_min, t_max = time_points.min(), time_points.max()
    num_internal = k_dim - 4
    if num_internal < 0:
        num_internal = 0
    
    if num_internal > 0:
        knots = np.linspace(t_min, t_max, num_internal + 2)[1:-1]
    else:
        knots = []
    
    t = np.concatenate(([t_min]*4, knots, [t_max]*4))
    
    mse_values = []
    
    for i, coeff in enumerate(coeffs):
        # Reconstruct using the knot sequence and coefficients
        # We need to evaluate the spline at time_points
        # Since we don't have the spline object, we reconstruct manually or create a temporary one
        # LSQUnivariateSpline stores knots and coeffs. We can create a new instance?
        # Actually, we can use UnivariateSpline with t and k=3 and set the coefficients?
        # UnivariateSpline doesn't allow setting coefficients directly.
        # We can use the fact that we know the knots and coeffs.
        # We can use `splev` from scipy.interpolate if we have the tck tuple.
        from scipy.interpolate import splev, BSpline
        
        # Create a BSpline object
        # BSpline(t, c, k, extrapolate=True)
        # t is the knot sequence, c is coefficients, k is degree (3)
        try:
            # Ensure coeff is a numpy array
            c = np.asarray(coeff)
            # BSpline expects t, c, k
            # The knot sequence t must be non-decreasing.
            # The length of c should be len(t) - k - 1.
            # Let's verify: len(t) = 4 + num_internal + 4 = num_internal + 8
            # len(c) should be num_internal + 4 = k_dim.
            # This matches.
            
            bs = BSpline(t, c, 3, extrapolate=True)
            y_recon = bs(time_points)
            
            y_orig = original_data[i]
            mse = np.mean((y_orig - y_recon) ** 2)
            mse_values.append(mse)
            
            if mse > tolerance:
                logger.warning(f"Ensemble member {i} MSE {mse:.4f} > tolerance {tolerance}")
            else:
                logger.debug(f"Ensemble member {i} MSE {mse:.4f} <= tolerance {tolerance}")
                
        except Exception as e:
            logger.error(f"Reconstruction failed for member {i}: {e}")
            raise e
    
    mean_mse = np.mean(mse_values)
    logger.info(f"Mean MSE across ensemble: {mean_mse:.6f}")
    
    passed = mean_mse <= tolerance
    if passed:
        logger.info(f"Verification PASSED: Mean MSE {mean_mse:.6f} <= {tolerance}")
    else:
        logger.error(f"Verification FAILED: Mean MSE {mean_mse:.6f} > {tolerance}")
    
    return passed, mean_mse

def main():
    """
    Main entry point for T017: Reconstruct curves and verify MSE.
    """
    setup_logger = logging.getLogger(__name__)
    # Ensure logging is configured if not already
    if not logging.getLogger().handlers:
        from logging_config import setup_logging
        setup_logging()

    project_root = get_project_root()
    data_dir = get_data_dir()
    
    # Load processed data from T016
    # Assuming T016 saved coefficients to data/processed/b_spline_coefficients.npy
    # and the original data to data/processed/imputed_ensemble.npy
    coeffs_path = data_dir / "processed" / "b_spline_coefficients.npy"
    original_path = data_dir / "processed" / "imputed_ensemble.npy"
    time_path = data_dir / "processed" / "time_points.npy"
    
    if not coeffs_path.exists():
        logger.error(f"Cannot find coefficients file: {coeffs_path}")
        logger.error("Run T016 first to generate coefficients.")
        return False
        
    if not original_path.exists():
        logger.error(f"Cannot find original data file: {original_path}")
        return False
    
    if not time_path.exists():
        logger.error(f"Cannot find time points file: {time_path}")
        return False
    
    coeffs = np.load(coeffs_path)
    original_data = np.load(original_path)
    time_points = np.load(time_path)
    
    # Determine k_dim from the coefficients shape
    # If coeffs is (n_ensemble, k_dim), then k_dim = coeffs.shape[1]
    if coeffs.ndim == 1:
        k_dim = len(coeffs)
        # Reshape to (1, k_dim) if only one curve? 
        # But original_data should match.
        if original_data.ndim == 1:
            original_data = original_data.reshape(1, -1)
            coeffs = coeffs.reshape(1, -1)
        else:
            # If original_data is 2D but coeffs is 1D, something is wrong.
            # Assume coeffs is (n, k)
            pass
    else:
        k_dim = coeffs.shape[1]
    
    passed, mse = reconstruct_and_verify(coeffs, time_points, k_dim, original_data, tolerance=0.01)
    
    # Save verification result
    results_path = data_dir / "processed" / "reconstruction_verification.json"
    import json
    result_data = {
        "task": "T017",
        "mean_mse": float(mse),
        "tolerance": 0.01,
        "passed": passed,
        "k_dim": k_dim,
        "n_ensemble": len(coeffs)
    }
    
    with open(results_path, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    logger.info(f"Verification result saved to {results_path}")
    
    return passed

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
    exit(0)