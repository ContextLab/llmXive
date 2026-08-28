import os
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from typing import Optional, Union
import warnings
from pathlib import Path
import subprocess
import sys

from config import get_config
from utils.logging import log_exclusion

def compress_image(path: str, max_mb: float = 5.0) -> None:
    """
    Compress an image file to ensure it is under max_mb.
    Uses Python's built-in PIL (via matplotlib or directly) to resize/re-save.
    If the file is already under the limit, no action is taken.
    """
    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    if file_size_mb <= max_mb:
        return

    # Use PIL to compress
    try:
        from PIL import Image
    except ImportError:
        # Fallback to converting via matplotlib if PIL is not available
        # This is less efficient but ensures functionality
        log_exclusion("PIL_MISSING", "image_compression")
        raise ImportError("PIL (Pillow) is required for image compression. Install with: pip install Pillow")

    img = Image.open(path)
    original_size = img.size

    # If it's too big, try reducing quality (for JPEG) or resizing
    # We assume PNG or JPEG. For PNG, we might need to convert to RGB or reduce bit depth,
    # but for simplicity and robustness, we'll try saving as JPEG with high quality first.
    # If the original was PNG and we need to keep transparency, we might need a different strategy,
    # but scientific plots are usually opaque.
    
    save_path = Path(path)
    quality = 95
    step = 5
    resized = False
    
    # Try saving with reduced quality first
    while quality >= 10:
        # Determine format
        fmt = save_path.suffix.lower()
        if fmt == '.png':
            # For PNG, we can't use quality, so we might need to resize or convert to JPEG
            # Let's try converting to JPEG if it's too big, but keep the original name if possible
            # Or just resize the PNG
            if not resized:
                # Calculate new size to roughly fit the limit
                # Area scales with square of linear dimension
                scale_factor = np.sqrt((max_mb * 1024 * 1024) / os.path.getsize(path))
                new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                resized = True
            
            # Save as JPEG to ensure compression works, or re-save PNG with optimize
            # Let's try saving as JPEG first if it's PNG and too big
            if save_path.suffix.lower() == '.png':
                # Convert to RGB if necessary (remove alpha)
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                temp_path = str(save_path.with_suffix('.jpg'))
                img.save(temp_path, 'JPEG', quality=quality)
                if os.path.getsize(temp_path) <= max_mb * 1024 * 1024:
                    os.replace(temp_path, path)
                    return
                else:
                    os.remove(temp_path)
            else:
                # It's already JPEG or similar
                img.save(path, quality=quality)
                if os.path.getsize(path) <= max_mb * 1024 * 1024:
                    return
        else:
            # JPEG
            img.save(path, 'JPEG', quality=quality)
            if os.path.getsize(path) <= max_mb * 1024 * 1024:
                return

        quality -= step

    # If we still can't compress, resize more aggressively
    if not resized:
        scale_factor = np.sqrt((max_mb * 1024 * 1024) / os.path.getsize(path))
        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        img.save(path)
        if os.path.getsize(path) > max_mb * 1024 * 1024:
            # Last resort: extremely aggressive resize
            scale_factor = np.sqrt((max_mb * 1024 * 1024) / os.path.getsize(path))
            new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            img.save(path)

def plot_flexibility_vs_creativity(
    flexibility: np.ndarray,
    creativity: np.ndarray,
    output_path: str = 'docs/outputs/flexibility_vs_creativity.png'
) -> None:
    """
    Creates a scatter plot of flexibility vs creativity with a regression line and confidence band.
    Saves the plot to the specified output path.
    Enforces the <= 5MB limit via compress_image.
    """
    # Filter out NaNs
    mask = ~(np.isnan(flexibility) | np.isnan(creativity))
    flex_clean = flexibility[mask]
    creat_clean = creativity[mask]

    if len(flex_clean) == 0:
        log_exclusion("NO_DATA", "plot_flexibility_vs_creativity")
        warnings.warn("No valid data points to plot.")
        return

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 6))
    plt.scatter(flex_clean, creat_clean, alpha=0.7, edgecolors='k', linewidth=0.5)

    # Fit regression
    X = sm.add_constant(flex_clean)
    model = sm.OLS(creat_clean, X).fit()
    pred = model.predict(X)

    # Sort for plotting line
    sort_idx = np.argsort(flex_clean)
    plt.plot(flex_clean[sort_idx], pred[sort_idx], 'r-', linewidth=2, label='Regression')

    # Confidence interval
    conf = model.get_prediction(X).conf_int(alpha=0.05)
    plt.fill_between(
        flex_clean[sort_idx],
        conf[sort_idx, 0],
        conf[sort_idx, 1],
        color='red',
        alpha=0.2,
        label='95% CI'
    )

    plt.xlabel('Network Flexibility')
    plt.ylabel('Creativity Score (CAQ)')
    plt.title('Relationship between Network Flexibility and Creativity')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    # Compress if necessary
    compress_image(output_path, max_mb=5.0)

def plot_residuals(
    model: sm.OLSResults,
    residuals_path: str = 'docs/outputs/model_residuals.png',
    qq_path: str = 'docs/outputs/model_qq.png'
) -> None:
    """
    Generates residuals-vs-fitted and QQ plots for a regression model.
    Saves the plots to the specified output paths.
    Enforces the <= 5MB limit via compress_image.
    """
    # Ensure output directories exist
    Path(residuals_path).parent.mkdir(parents=True, exist_ok=True)
    Path(qq_path).parent.mkdir(parents=True, exist_ok=True)

    # Get residuals and fitted values
    residuals = model.resid
    fitted = model.fittedvalues

    # Filter NaNs if any (though OLS usually handles this)
    valid_mask = ~(np.isnan(residuals) | np.isnan(fitted))
    residuals_clean = residuals[valid_mask]
    fitted_clean = fitted[valid_mask]

    if len(residuals_clean) == 0:
        log_exclusion("NO_DATA", "plot_residuals")
        warnings.warn("No valid data points for residual plots.")
        return

    # Plot 1: Residuals vs Fitted
    plt.figure(figsize=(8, 6))
    plt.scatter(fitted_clean, residuals_clean, alpha=0.7, edgecolors='k', linewidth=0.5)
    plt.axhline(0, color='red', linestyle='--', linewidth=2)
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(residuals_path, dpi=150)
    plt.close()
    compress_image(residuals_path, max_mb=5.0)

    # Plot 2: QQ Plot
    plt.figure(figsize=(8, 6))
    sm.qqplot(residuals_clean, line='45', fit=True)
    plt.title('Q-Q Plot of Residuals')
    plt.tight_layout()
    plt.savefig(qq_path, dpi=150)
    plt.close()
    compress_image(qq_path, max_mb=5.0)