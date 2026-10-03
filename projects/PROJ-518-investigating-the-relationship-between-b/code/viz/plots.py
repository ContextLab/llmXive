import os
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from typing import Optional, Union
import warnings
import logging

from analysis.statistics import RegressionResult
from config import get_config

# Configure logging for the module
logger = logging.getLogger(__name__)

def _clean_nan_arrays(*arrays: Union[np.ndarray, list]) -> list:
    """
    Filter out NaN/Inf values from multiple aligned arrays.
    
    Args:
        *arrays: Variable number of array-like objects to be cleaned.
        
    Returns:
        A list of cleaned numpy arrays, aligned by the valid indices.
        If an array is empty after cleaning, an empty array is returned.
    """
    if len(arrays) == 0:
        return []
    
    # Convert all to numpy arrays
    np_arrays = [np.asarray(arr) for arr in arrays]
    
    # Handle empty inputs
    if any(arr.size == 0 for arr in np_arrays):
        return [arr for arr in np_arrays]
        
    # Find indices where ALL arrays are finite
    valid_mask = np.ones(np_arrays[0].shape[0], dtype=bool)
    
    for arr in np_arrays:
        if arr.size == 0:
            continue
        # Ensure we are checking the first dimension for 1D arrays
        if arr.ndim > 1:
            # Flatten if necessary for mask alignment, though typically 1D here
            valid_mask &= np.isfinite(arr.flatten())
        else:
            valid_mask &= np.isfinite(arr)
    
    cleaned = [arr[valid_mask] for arr in np_arrays]
    
    # Log if data was removed
    removed_count = np_arrays[0].size - valid_mask.sum()
    if removed_count > 0:
        logger.warning(f"Removed {removed_count} data points containing NaN or Inf values.")
    
    return cleaned

def plot_flexibility_vs_creativity(
    flexibility: Union[np.ndarray, list],
    creativity: Union[np.ndarray, list],
    output_path: str = 'docs/outputs/flexibility_vs_creativity.png'
) -> None:
    """
    Creates a scatter plot with regression line and confidence band.
    
    Handles NaN data points by filtering them out and logging a warning.
    
    Args:
        flexibility: Array of network flexibility values.
        creativity: Array of creativity scores.
        output_path: Path to save the plot.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Clean data
    flex_clean, creat_clean = _clean_nan_arrays(flexibility, creativity)
    
    if len(flex_clean) == 0:
        logger.error("No valid data points remaining after filtering NaN/Inf. Cannot generate plot.")
        # Create a minimal empty plot to avoid crashing, or raise? 
        # Task says "continue", so we create an empty plot with a note.
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No valid data points', ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Flexibility vs Creativity (No Data)')
        plt.savefig(output_path)
        plt.close()
        return

    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot
    ax.scatter(flex_clean, creat_clean, alpha=0.6, edgecolors='w', s=70, label='Data Points')
    
    # Fit OLS for regression line
    X = sm.add_constant(flex_clean)
    model = sm.OLS(creat_clean, X).fit()
    
    # Sort for line plotting
    sort_idx = np.argsort(flex_clean)
    x_sorted = flex_clean[sort_idx]
    y_pred = model.predict(sm.add_constant(x_sorted))
    
    # Plot regression line
    ax.plot(x_sorted, y_pred, color='red', linewidth=2, label='Regression Fit')
    
    # Confidence band (95%)
    conf = model.get_prediction(sm.add_constant(flex_clean)).conf_int(alpha=0.05)
    # We need to sort the conf bounds as well to match x_sorted
    conf_sorted = conf[sort_idx]
    ax.fill_between(x_sorted, conf_sorted[:, 0], conf_sorted[:, 1], color='red', alpha=0.2, label='95% CI')
    
    ax.set_xlabel('Network Flexibility')
    ax.set_ylabel('Creativity Score')
    ax.set_title('Relationship Between Network Flexibility and Creativity')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Scatter plot saved to {output_path}")

def plot_residuals(
    model: RegressionResult,
    residuals_path: str = 'docs/outputs/model_residuals.png',
    qq_path: str = 'docs/outputs/model_qq.png'
) -> None:
    """
    Generates residuals-vs-fitted and QQ plots.
    
    Handles NaN data points by filtering them out and logging a warning.
    
    Args:
        model: RegressionResult object containing fitted values and residuals.
        residuals_path: Path to save the residuals plot.
        qq_path: Path to save the QQ plot.
    """
    os.makedirs(os.path.dirname(residuals_path), exist_ok=True)
    os.makedirs(os.path.dirname(qq_path), exist_ok=True)
    
    fitted = np.asarray(model.fittedvalues)
    residuals = np.asarray(model.resid)
    
    # Clean NaNs
    fitted_clean, resid_clean = _clean_nan_arrays(fitted, residuals)
    
    if len(fitted_clean) == 0:
        logger.error("No valid data points for residual plots.")
        # Create placeholder plots
        for path, title in [(residuals_path, 'Residuals vs Fitted (No Data)'), 
                            (qq_path, 'QQ Plot (No Data)')]:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No valid data', ha='center', va='center')
            ax.set_title(title)
            plt.savefig(path)
            plt.close()
        return

    # Plot 1: Residuals vs Fitted
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(fitted_clean, resid_clean, alpha=0.6, edgecolors='w')
    ax.axhline(0, color='red', linestyle='--', linewidth=1)
    ax.set_xlabel('Fitted Values')
    ax.set_ylabel('Residuals')
    ax.set_title('Residuals vs Fitted')
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(residuals_path, dpi=150)
    plt.close()
    
    # Plot 2: QQ Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    sm.qqplot(resid_clean, line='45', fit=True, ax=ax)
    ax.set_title('Normal Q-Q')
    plt.tight_layout()
    plt.savefig(qq_path, dpi=150)
    plt.close()
    
    logger.info(f"Residual plots saved to {residuals_path} and {qq_path}")

def compress_image(path: str, max_mb: float = 5.0) -> None:
    """
    Compresses an image file to ensure it is under max_mb.
    
    Args:
        path: Path to the image file.
        max_mb: Maximum size in megabytes.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image file not found: {path}")
    
    initial_size = os.path.getsize(path) / (1024 * 1024)
    logger.info(f"Initial image size: {initial_size:.2f} MB")
    
    if initial_size <= max_mb:
        return
    
    # Simple compression strategy: Convert to JPEG with quality reduction if PNG
    # or re-save PNG with lower compression level. 
    # For this implementation, we assume we can re-save as JPEG if it's PNG, 
    # or just reduce quality if we had PIL. Since we rely on matplotlib mostly,
    # we will try to re-save with optimized=True and lower dpi if needed,
    # but strictly speaking, re-processing the plot is better.
    # However, to strictly follow "compress_image" on an existing file:
    # We will use PIL if available, otherwise we might need to re-generate.
    # Given the constraints, let's try to use PIL for compression.
    
    try:
        from PIL import Image
        img = Image.open(path)
        
        # If it's already small enough after loading? No, size is on disk.
        # We need to reduce quality.
        base, ext = os.path.splitext(path)
        
        if ext.lower() == '.png':
            # Convert to RGB if necessary for JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            # Save as JPEG with quality reduction
            new_path = base + ".jpg"
            quality = 95
            while os.path.getsize(new_path) > max_mb * 1024 * 1024 and quality > 10:
                quality -= 5
                img.save(new_path, "JPEG", quality=quality)
            os.remove(path)
            os.rename(new_path, path)
            final_size = os.path.getsize(path) / (1024 * 1024)
            logger.info(f"Compressed to JPEG: {final_size:.2f} MB (Quality: {quality})")
        else:
            # For JPEG, just reduce quality
            quality = 95
            while os.path.getsize(path) > max_mb * 1024 * 1024 and quality > 10:
                quality -= 5
                img.save(path, "JPEG", quality=quality)
            final_size = os.path.getsize(path) / (1024 * 1024)
            logger.info(f"Compressed JPEG: {final_size:.2f} MB (Quality: {quality})")
            
    except ImportError:
        logger.warning("PIL not available. Cannot compress image automatically.")
        # If we can't compress, we raise the critical error as per task T057 logic
        # But T057 says "raise CriticalError". Let's assume we just log and fail the check.
        # Actually, T057 says: "If compression fails... raise CriticalError".
        # We are in T058, but we must respect T057's contract.
        # Since we can't compress without PIL, we should probably raise an error if size is too big.
        if initial_size > max_mb:
             raise RuntimeError(f"Image {path} exceeds {max_mb}MB and compression failed (PIL missing).")
    
    final_size = os.path.getsize(path) / (1024 * 1024)
    if final_size > max_mb:
        logger.critical(f"Compression failed: {path} is still {final_size:.2f} MB > {max_mb} MB")
        raise RuntimeError(f"Failed to compress {path} under {max_mb} MB")
    
    assert os.path.getsize(path) <= max_mb * 1024 * 1024, "Compression verification failed"

def log_regression_summary(result: RegressionResult, output_path: str = 'results/regression_summary.csv') -> None:
    """
    Logs regression results to a CSV file.
    
    Args:
        result: RegressionResult object.
        output_path: Path to the CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    import pandas as pd
    from analysis.statistics import format_delta_r2
    
    row = {
        'r_squared': result.rsquared,
        'adj_r_squared': result.rsquared_adj,
        'pearson_r': result.pearson_r,
        'delta_r2': result.delta_r2,
        'delta_r2_str': format_delta_r2(result.delta_r2),
        'coefficients': str(result.params.to_dict()) if hasattr(result.params, 'to_dict') else str(result.params)
    }
    
    df = pd.DataFrame([row])
    df.to_csv(output_path, index=False)
    logger.info(f"Regression summary saved to {output_path}")

# Re-export RegressionResult for convenience if needed in other modules, 
# though it's defined in statistics.py. 
# The API surface says we import it from here, so we ensure it's available.
# Actually, the API surface says: "import as: from viz.plots import RegressionResult..."
# So we must define it here or import it. Since it's defined in statistics, we import it.
from analysis.statistics import RegressionResult
