import os
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from typing import Optional, Union
import warnings
from PIL import Image
from io import BytesIO
import logging

# Configure logging for the module
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def compress_image(path: str, max_mb: float = 5.0) -> bool:
    """
    Compress an image file to ensure it is under max_mb.
    Returns True if compressed successfully, False otherwise.
    """
    if not os.path.exists(path):
        logger.warning(f"Image not found for compression: {path}")
        return False

    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    if file_size_mb <= max_mb:
        return True

    try:
        img = Image.open(path)
        # Convert to RGB if necessary (e.g., if PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        quality = 95
        while file_size_mb > max_mb and quality > 10:
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            file_size_mb = len(buffer.getvalue()) / (1024 * 1024)
            quality -= 5

        buffer.seek(0)
        with open(path, 'wb') as f:
            f.write(buffer.read())
        
        logger.info(f"Compressed {path} to {os.path.getsize(path)/(1024*1024):.2f} MB")
        return True
    except Exception as e:
        logger.error(f"Failed to compress {path}: {e}")
        return False


def plot_flexibility_vs_creativity(
    flexibility: Union[np.ndarray, list],
    creativity: Union[np.ndarray, list],
    output_path: str = 'docs/outputs/flexibility_vs_creativity.png'
) -> None:
    """
    Creates a scatter plot of flexibility vs creativity with regression line.
    Skips NaN data points, logs warnings, and continues.
    """
    # Convert inputs to numpy arrays
    flex_arr = np.asarray(flexibility, dtype=float)
    creat_arr = np.asarray(creativity, dtype=float)

    # Ensure same length
    if flex_arr.shape[0] != creat_arr.shape[0]:
        raise ValueError("flexibility and creativity arrays must have the same length")

    # Mask NaN values
    valid_mask = ~(np.isnan(flex_arr) | np.isnan(creat_arr))
    
    if not np.all(valid_mask):
        skipped_count = np.sum(~valid_mask)
        logger.warning(f"Skipping {skipped_count} data points with NaN values in plot_flexibility_vs_creativity")
    
    flex_clean = flex_arr[valid_mask]
    creat_clean = creat_arr[valid_mask]

    if len(flex_clean) == 0:
        logger.error("No valid data points remaining after removing NaN. Cannot generate plot.")
        # Create an empty plot to avoid crashing downstream, but log error
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No valid data', transform=ax.transAxes, ha='center')
        plt.savefig(output_path)
        plt.close()
        compress_image(output_path)
        return

    # Perform linear regression
    X = sm.add_constant(flex_clean)
    model = sm.OLS(creat_clean, X).fit()
    line_x = np.linspace(flex_clean.min(), flex_clean.max(), 100)
    line_y = model.params[0] + model.params[1] * line_x

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(flex_clean, creat_clean, alpha=0.6, label='Data Points', color='blue')
    ax.plot(line_x, line_y, 'r-', label=f'Regression (r={model.rsquared:.3f})')
    
    # Confidence interval
    conf = model.conf_int(alpha=0.05)
    # Simple approximation for confidence band around the line
    # Note: For exact OLS prediction intervals, we'd use get_prediction, but this is sufficient for viz
    ax.fill_between(line_x, 
                    line_y - 1.96 * model.bse[1] * line_x - 1.96 * model.bse[0], 
                    line_y + 1.96 * model.bse[1] * line_x + 1.96 * model.bse[0],
                    alpha=0.2, color='gray', label='95% CI')

    ax.set_xlabel('Network Flexibility')
    ax.set_ylabel('Creativity Score (CAQ)')
    ax.set_title('Relationship between Network Flexibility and Creativity')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    compress_image(output_path)


def plot_residuals(
    model: 'RegressionResult',
    residuals_path: str = 'docs/outputs/model_residuals.png',
    qq_path: str = 'docs/outputs/model_qq.png'
) -> None:
    """
    Generates residuals-vs-fitted and QQ plots.
    Skips NaN data points, logs warnings, and continues.
    """
    # Extract residuals and fitted values from the model object
    # Assuming model has .resid and .fittedvalues attributes or similar
  #   If the passed object is a statsmodels OLSResults:
    if hasattr(model, 'resid'):
        residuals = np.asarray(model.resid)
        fitted = np.asarray(model.fittedvalues)
    else:
        # Fallback if it's a custom object with specific attributes
        # Adjust based on actual RegressionResult structure if different
        raise AttributeError("Model object must have 'resid' and 'fittedvalues' attributes")

    # Handle NaNs
    valid_mask = ~(np.isnan(residuals) | np.isnan(fitted))
    if not np.all(valid_mask):
        skipped = np.sum(~valid_mask)
        logger.warning(f"Skipping {skipped} NaN points in residuals plot")
    
    res_clean = residuals[valid_mask]
    fit_clean = fitted[valid_mask]

    if len(res_clean) == 0:
        logger.error("No valid data for residual plots.")
        return

    # 1. Residuals vs Fitted
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(fit_clean, res_clean, alpha=0.6, color='darkblue')
    ax.axhline(0, color='red', linestyle='--', linewidth=1)
    ax.set_xlabel('Fitted Values')
    ax.set_ylabel('Residuals')
    ax.set_title('Residuals vs Fitted')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    os.makedirs(os.path.dirname(residuals_path), exist_ok=True)
    plt.savefig(residuals_path, dpi=150, bbox_inches='tight')
    plt.close()
    compress_image(residuals_path)

    # 2. QQ Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    # Use statsmodels qqplot or manual
  #   sm.qqplot(res_clean, line='45', ax=ax) # This might not work directly with matplotlib axis in all versions
  #   Manual implementation for robustness:
    from scipy import stats
    stats.probplot(res_clean, dist="norm", plot=ax)
    ax.set_title('Normal Q-Q')
    ax.grid(True, linestyle='--', alpha=0.5)

    plt.savefig(qq_path, dpi=150, bbox_inches='tight')
    plt.close()
    compress_image(qq_path)