import os
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from typing import Optional, Union
import warnings
import logging
from PIL import Image
import io

# Configure logging for the module
logger = logging.getLogger(__name__)

def compress_image(path: str, max_mb: float = 5.0) -> None:
    """
    Compress an image file to be under max_mb size.
    If the image is already under the limit, no action is taken.
    """
    if not os.path.exists(path):
        logger.warning(f"Cannot compress {path}: file does not exist.")
        return

    file_size = os.path.getsize(path)
    if file_size <= max_mb * 1024 * 1024:
        return

    try:
        img = Image.open(path)
        # Convert to RGB if necessary (e.g., for PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        quality = 95
        while quality > 10:
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality)
            if buffer.tell() <= max_mb * 1024 * 1024:
                with open(path, 'wb') as f:
                    f.write(buffer.getvalue())
                logger.info(f"Compressed {path} to {buffer.tell() / (1024*1024):.2f} MB")
                return
            quality -= 5
        
        # If we get here, even low quality is too big, just save what we have
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=10)
        with open(path, 'wb') as f:
            f.write(buffer.getvalue())
        logger.warning(f"Could not compress {path} below {max_mb} MB, saved at minimum quality.")
        
    except Exception as e:
        logger.error(f"Failed to compress image {path}: {e}")

def plot_flexibility_vs_creativity(
    flexibility: Union[np.ndarray, list],
    creativity: Union[np.ndarray, list],
    output_path: str = 'docs/outputs/flexibility_vs_creativity.png'
) -> None:
    """
    Creates a scatter plot of flexibility vs creativity with a regression line and confidence band.
    Skips NaN data points, logs warnings, and continues.
    """
    flexibility = np.asarray(flexibility, dtype=float)
    creativity = np.asarray(creativity, dtype=float)

    if flexibility.shape != creativity.shape:
        raise ValueError("flexibility and creativity must have the same shape")

    # Identify valid (non-NaN) points
    valid_mask = ~(np.isnan(flexibility) | np.isnan(creativity))
    n_valid = np.sum(valid_mask)
    n_total = len(flexibility)

    if n_valid == 0:
        logger.warning("No valid data points (all NaN) for flexibility vs creativity plot.")
        # Create an empty plot or a placeholder to avoid crash
        plt.figure(figsize=(8, 6))
        plt.title("No Valid Data")
        plt.xlabel("Network Flexibility")
        plt.ylabel("Creativity Score")
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        plt.savefig(output_path)
        plt.close()
        compress_image(output_path)
        return

    if n_valid < n_total:
        skipped = n_total - n_valid
        logger.warning(f"Skipping {skipped} data point(s) with NaN values in flexibility or creativity.")

    x = flexibility[valid_mask]
    y = creativity[valid_mask]

    # Sort by x for plotting regression line
    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    y_sorted = y[sort_idx]

    # Fit regression
    X = sm.add_constant(x_sorted)
    model = sm.OLS(y_sorted, X).fit()
    y_pred = model.predict(X)
    y_lower = model.get_prediction(X).conf_int(alpha=0.05)[:, 0]
    y_upper = model.get_prediction(X).conf_int(alpha=0.05)[:, 1]

    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, alpha=0.6, label='Data Points')
    plt.plot(x_sorted, y_pred, color='red', label='Regression Line')
    plt.fill_between(x_sorted, y_lower, y_upper, color='red', alpha=0.2, label='95% Confidence Interval')
    plt.xlabel('Network Flexibility')
    plt.ylabel('Creativity Score')
    plt.title('Flexibility vs Creativity')
    plt.legend()
    plt.grid(True, alpha=0.3)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    compress_image(output_path)

def plot_residuals(
    model: sm.OLSResults,
    residuals_path: str = 'docs/outputs/model_residuals.png',
    qq_path: str = 'docs/outputs/model_qq.png'
) -> None:
    """
    Generates residuals-vs-fitted and QQ plots.
    Skips NaN data points, logs warnings, and continues.
    """
    residuals = model.resid
    fitted = model.fittedvalues

    # Check for NaNs
    valid_mask = ~(np.isnan(residuals) | np.isnan(fitted))
    n_valid = np.sum(valid_mask)
    n_total = len(residuals)

    if n_valid == 0:
        logger.warning("No valid residuals for plotting.")
        # Create empty plots
        for path, title in [(residuals_path, "Residuals vs Fitted (No Data)"), 
                            (qq_path, "QQ Plot (No Data)")]:
            plt.figure(figsize=(8, 6))
            plt.title(title)
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
            plt.savefig(path)
            plt.close()
            compress_image(path)
        return

    if n_valid < n_total:
        skipped = n_total - n_valid
        logger.warning(f"Skipping {skipped} residual/fitted pair(s) with NaN values.")

    res_clean = residuals[valid_mask]
    fit_clean = fitted[valid_mask]

    # Residuals vs Fitted
    plt.figure(figsize=(8, 6))
    plt.scatter(fit_clean, res_clean, alpha=0.6)
    plt.axhline(0, color='red', linestyle='--')
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted')
    plt.grid(True, alpha=0.3)
    os.makedirs(os.path.dirname(residuals_path) if os.path.dirname(residuals_path) else '.', exist_ok=True)
    plt.savefig(residuals_path)
    plt.close()
    compress_image(residuals_path)

    # QQ Plot
    plt.figure(figsize=(8, 6))
    sm.qqplot(res_clean, line='45', fit=True)
    plt.title('Normal Q-Q')
    os.makedirs(os.path.dirname(qq_path) if os.path.dirname(qq_path) else '.', exist_ok=True)
    plt.savefig(qq_path)
    plt.close()
    compress_image(qq_path)