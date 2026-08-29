import os
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from typing import Optional, Union
import warnings
from pathlib import Path

# Ensure matplotlib uses a non-interactive backend for headless execution
import matplotlib
matplotlib.use('Agg')


def compress_image(path: str, max_mb: float = 5.0) -> None:
    """
    Compress an image file to ensure it is under max_mb.
    This is a placeholder for image compression logic (e.g., using PIL/Pillow).
    Since we are saving PNGs directly with optimization, we check size and
    potentially re-save with lower DPI if necessary.
    """
    file_size_bytes = os.path.getsize(path)
    max_bytes = max_mb * 1024 * 1024

    if file_size_bytes > max_bytes:
        # If too large, re-save with lower DPI or optimize parameters
        # For this implementation, we assume the default save is usually sufficient,
        # but if it fails, we could try reducing dpi in the save call.
        # Here we just log a warning as the primary mechanism is controlling DPI at source.
        warnings.warn(f"Image {path} exceeds {max_mb}MB ({file_size_bytes} bytes). "
                      "Consider reducing figure size or DPI.")


def plot_flexibility_vs_creativity(
    flexibility: Union[np.ndarray, list],
    creativity: Union[np.ndarray, list],
    output_path: str = 'docs/outputs/flexibility_vs_creativity.png'
) -> None:
    """
    Creates a scatter plot of flexibility vs creativity with a regression line
    and a confidence band. Saves the plot to the specified output path.

    Args:
        flexibility: Array of network flexibility values.
        creativity: Array of creativity scores (CAQ).
        output_path: Path where the plot will be saved.
    """
    # Convert inputs to numpy arrays
    flexibility = np.asarray(flexibility)
    creativity = np.asarray(creativity)

    # Filter out NaNs to avoid plotting errors
    valid_mask = ~(np.isnan(flexibility) | np.isnan(creativity))
    x = flexibility[valid_mask]
    y = creativity[valid_mask]

    if len(x) == 0:
        raise ValueError("No valid data points after filtering NaNs.")

    # Create the plot
    plt.figure(figsize=(10, 8))

    # Scatter plot
    plt.scatter(x, y, alpha=0.6, edgecolors='w', s=50, label='Participants')

    # Fit OLS regression
    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit()
    
    # Generate predictions for the regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    X_line = sm.add_constant(x_line)
    y_line = model.predict(X_line)
    
    # Confidence interval
    conf_int = model.get_prediction(X_line).conf_int(alpha=0.05)
    lower = conf_int[:, 0]
    upper = conf_int[:, 1]

    # Plot regression line
    plt.plot(x_line, y_line, color='red', linewidth=2, label='Regression Line')
    
    # Plot confidence band
    plt.fill_between(x_line, lower, upper, color='red', alpha=0.2, label='95% CI')

    # Labels and title
    plt.xlabel('Network Flexibility', fontsize=12)
    plt.ylabel('Creativity Score (CAQ)', fontsize=12)
    plt.title('Relationship between Brain Network Dynamics and Creativity', fontsize=14)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save the plot
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    # Compress if necessary (optional, based on requirements)
    if os.path.exists(output_path):
        compress_image(output_path, max_mb=5.0)


def plot_residuals(
    model: sm.OLSResults,
    residuals_path: str = 'docs/outputs/model_residuals.png',
    qq_path: str = 'docs/outputs/model_qq.png'
) -> None:
    """
    Generates residuals-vs-fitted and QQ plots for the given regression model.
    Saves the plots to the specified output paths.

    Args:
        model: A fitted statsmodels OLS regression result object.
        residuals_path: Path to save the residuals-vs-fitted plot.
        qq_path: Path to save the QQ plot.
    """
    # Extract residuals and fitted values
    residuals = model.resid
    fitted = model.fittedvalues

    # Filter out NaNs if any
    valid_mask = ~(np.isnan(residuals) | np.isnan(fitted))
    residuals = residuals[valid_mask]
    fitted = fitted[valid_mask]

    if len(residuals) == 0:
        raise ValueError("No valid data points for residual plots.")

    # --- Residuals vs Fitted Plot ---
    plt.figure(figsize=(10, 6))
    plt.scatter(fitted, residuals, alpha=0.6, edgecolors='w', s=50)
    plt.axhline(0, color='red', linestyle='--', linewidth=2)
    plt.xlabel('Fitted Values', fontsize=12)
    plt.ylabel('Residuals', fontsize=12)
    plt.title('Residuals vs Fitted', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.5)

    residuals_dir = os.path.dirname(residuals_path)
    if residuals_dir:
        os.makedirs(residuals_dir, exist_ok=True)
    plt.savefig(residuals_path, dpi=150, bbox_inches='tight')
    plt.close()

    # --- QQ Plot ---
    plt.figure(figsize=(10, 6))
    sm.qqplot(residuals, line='s', fit=True, ax=plt.gca())
    plt.title('Normal Q-Q Plot', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.5)

    qq_dir = os.path.dirname(qq_path)
    if qq_dir:
        os.makedirs(qq_dir, exist_ok=True)
    plt.savefig(qq_path, dpi=150, bbox_inches='tight')
    plt.close()

    # Compress images if needed
    if os.path.exists(residuals_path):
        compress_image(residuals_path, max_mb=5.0)
    if os.path.exists(qq_path):
        compress_image(qq_path, max_mb=5.0)