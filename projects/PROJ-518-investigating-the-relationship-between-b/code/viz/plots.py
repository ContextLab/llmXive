import os
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from typing import Optional, Union
import warnings
import logging
from pathlib import Path

from config import get_config
from analysis.statistics import RegressionResult

logger = logging.getLogger(__name__)

def _clean_nan_arrays(x: Union[np.ndarray, list], y: Union[np.ndarray, list]) -> tuple[np.ndarray, np.ndarray]:
    """
    Remove NaN values from x and y arrays.
    Returns cleaned arrays and logs warnings for each removal.
    """
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)

    if x_arr.shape != y_arr.shape:
        raise ValueError(f"Array shapes mismatch: {x_arr.shape} vs {y_arr.shape}")

    # Create mask for valid (non-NaN) entries
    valid_mask = ~(np.isnan(x_arr) | np.isnan(y_arr))

    nan_count = np.sum(~valid_mask)
    if nan_count > 0:
        logger.warning(f"Detected {nan_count} NaN data points in input arrays. Skipping them.")

    return x_arr[valid_mask], y_arr[valid_mask]

def plot_flexibility_vs_creativity(
    flexibility: Union[np.ndarray, list],
    creativity: Union[np.ndarray, list],
    output_path: str = 'docs/outputs/flexibility_vs_creativity.png'
) -> None:
    """
    Creates a scatter plot with regression line and confidence band.
    Robustly handles NaN data points by skipping them.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Clean data
    x_clean, y_clean = _clean_nan_arrays(flexibility, creativity)

    if len(x_clean) == 0:
        raise ValueError("No valid data points remaining after NaN removal.")

    # Prepare for regression
    X = sm.add_constant(x_clean)
    model = sm.OLS(y_clean, X).fit()

    # Generate predictions for the plot
    x_range = np.linspace(x_clean.min(), x_clean.max(), 100)
    X_range = sm.add_constant(x_range)
    y_pred = model.predict(X_range)

    # Confidence intervals
    conf_int = model.predict(X_range, interval='confidence')

    plt.figure(figsize=(8, 6))
    plt.scatter(x_clean, y_clean, alpha=0.6, label='Data')
    plt.plot(x_range, y_pred, 'r-', label='Regression Fit')
    plt.fill_between(x_range, conf_int[:, 0], conf_int[:, 1], color='r', alpha=0.2, label='95% CI')

    plt.xlabel('Network Flexibility')
    plt.ylabel('Creativity Score (CAQ)')
    plt.title('Flexibility vs Creativity')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Plot saved to {output_path}")

def plot_residuals(
    model: RegressionResult,
    residuals_path: str = 'docs/outputs/model_residuals.png',
    qq_path: str = 'docs/outputs/model_qq.png'
) -> None:
    """
    Generates residuals-vs-fitted and QQ plots.
    Handles NaN values in model residuals.
    """
    output_dir = Path(residuals_path).parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Extract residuals and fitted values
    residuals = np.asarray(model.residuals, dtype=float)
    fitted = np.asarray(model.fitted_values, dtype=float)

    if len(residuals) != len(fitted):
        raise ValueError("Residuals and fitted values length mismatch.")

    # Clean NaNs
    valid_mask = ~(np.isnan(residuals) | np.isnan(fitted))
    if np.sum(~valid_mask) > 0:
        logger.warning(f"Skipping {np.sum(~valid_mask)} NaN residual/fitted pairs.")

    res_clean = residuals[valid_mask]
    fit_clean = fitted[valid_mask]

    if len(res_clean) == 0:
        raise ValueError("No valid data points for residual plots.")

    # Plot 1: Residuals vs Fitted
    plt.figure(figsize=(8, 6))
    plt.scatter(fit_clean, res_clean, alpha=0.6)
    plt.hlines(0, linestyle='--', color='red')
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(residuals_path, dpi=300)
    plt.close()
    logger.info(f"Residuals plot saved to {residuals_path}")

    # Plot 2: QQ Plot
    plt.figure(figsize=(8, 6))
    sm.qqplot(res_clean, line='45', fit=True)
    plt.title('Normal Q-Q')
    plt.tight_layout()
    plt.savefig(qq_path, dpi=300)
    plt.close()
    logger.info(f"QQ plot saved to {qq_path}")

def compress_image(path: str, max_mb: float = 5.0) -> None:
    """
    Compresses the image at `path` to be under `max_mb` MB.
    Raises RuntimeError if compression fails to meet the size limit.
    """
    import subprocess
    import sys

    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    initial_size = path_obj.stat().st_size / (1024 * 1024)
    logger.info(f"Initial file size: {initial_size:.2f} MB")

    if initial_size <= max_mb:
        logger.info("File size already within limit.")
        return

    # Attempt compression using ImageMagick (commonly available) or convert to JPEG
    # Strategy: Convert to JPEG with quality reduction if it's a PNG, or use pngquant if available
    # Since we cannot guarantee external tools like pngquant, we will try a robust conversion approach
    # or rely on matplotlib saving with optimization if possible. However, for strict file size control,
    # we often need external tools.
    
    # Fallback strategy: Re-save as JPEG with optimized quality
    # Check if PIL is available
    try:
        from PIL import Image
        img = Image.open(path)
        
        # Determine output path
        if path_obj.suffix.lower() == '.png':
            jpeg_path = str(path_obj.with_suffix('.jpg'))
            quality = 85
            # Iterative quality reduction to meet size
            while quality > 10:
                img.save(jpeg_path, quality=quality, optimize=True)
                new_size = Path(jpeg_path).stat().st_size / (1024 * 1024)
                if new_size <= max_mb:
                    # Replace original
                    path_obj.unlink()
                    Path(jpeg_path).rename(path_obj)
                    logger.info(f"Compressed to JPEG with quality {quality}. Final size: {new_size:.2f} MB")
                    return
                quality -= 5
        
        raise RuntimeError(f"Failed to compress {path} to under {max_mb} MB via JPEG conversion.")

    except ImportError:
        # PIL not available, try ImageMagick
        try:
            subprocess.run(['convert', path, '-quality', '80', path], check=True)
            new_size = path_obj.stat().st_size / (1024 * 1024)
            if new_size <= max_mb:
                logger.info(f"Compressed via ImageMagick. Final size: {new_size:.2f} MB")
                return
            # Try lower quality
            subprocess.run(['convert', path, '-quality', '50', path], check=True)
            new_size = path_obj.stat().st_size / (1024 * 1024)
            if new_size <= max_mb:
                logger.info(f"Compressed via ImageMagick (q50). Final size: {new_size:.2f} MB")
                return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    raise RuntimeError(f"Compression failed: {path} remains larger than {max_mb} MB.")

def log_regression_summary(result: RegressionResult, output_path: str = 'results/regression_summary.csv') -> None:
    """
    Logs regression summary to CSV.
    """
    import pandas as pd
    from datetime import datetime

    output_dir = Path(output_path).parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame([{
        'timestamp': datetime.now().isoformat(),
        'r_squared': result.r_squared,
        'adj_r_squared': result.adj_r_squared,
        'pearson_r': result.pearson_r,
        'delta_r2_str': result.delta_r2_str if hasattr(result, 'delta_r2_str') else 'N/A'
    }])

    df.to_csv(output_path, index=False)
    logger.info(f"Regression summary logged to {output_path}")
