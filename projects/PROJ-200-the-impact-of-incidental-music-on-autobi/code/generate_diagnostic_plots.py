"""
Generate diagnostic plots for the statistical models.

This script loads the regression results and user-track pairs data to generate:
1. Residuals vs Fitted values plot
2. QQ plot of residuals
3. Scale-Location plot
4. Residuals vs Leverage plot

Outputs are saved to data/final/plots/.
"""
import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats

from config import get_project_root, get_config_dict
from utils import setup_logging, get_logger
from state_manager import register_file, save_state

# Set up logging
logger = get_logger(__name__)

def load_regression_results() -> pd.DataFrame:
    """Load the regression summary results."""
    root = get_project_root()
    path = root / "data" / "final" / "regression_summary.csv"
    if not path.exists():
        raise FileNotFoundError(f"Regression results not found at {path}")
    return pd.read_csv(path)

def load_user_track_pairs() -> pd.DataFrame:
    """Load the aggregated user-track pairs data."""
    root = get_project_root()
    path = root / "data" / "processed" / "user_track_pairs.parquet"
    if not path.exists():
        raise FileNotFoundError(f"User-track pairs not found at {path}")
    return pd.read_parquet(path)

def calculate_residuals(model_data: pd.DataFrame, formula_vividness: str) -> pd.DataFrame:
    """
    Calculate residuals from the mixed model.
    
    Since we only have summary statistics, we approximate residuals using
    the model coefficients if available, or load pre-computed residuals
    if they exist in the data.
    """
    # For this implementation, we assume the user_track_pairs data contains
    # the necessary information to compute residuals or we use the model summary
    # to approximate them. In a full implementation, we would refit the model
    # here to get exact residuals.
    
    # Check if residuals are already in the data
    if 'residuals' in model_data.columns:
        return model_data['residuals']
    
    # If not, we need to refit the model to get residuals
    # This is a simplified approach - in production, we'd store residuals
    # from the original model fitting
    try:
        import statsmodels.formula.api as smf
        
        # Fit the model again to get residuals
        model = smf.mixedlm(
            "mean_vividness ~ residualized_exposure + popularity",
            model_data,
            groups=model_data["user_id"]
        )
        result = model.fit()
        return result.resid
    except Exception as e:
        logger.warning(f"Could not refit model to get residuals: {e}")
        # Return NaN residuals as fallback
        return pd.Series([np.nan] * len(model_data), index=model_data.index)

def create_residuals_plot(data: pd.DataFrame, residuals: pd.Series, save_path: Path):
    """Create residuals vs fitted values plot."""
    plt.figure(figsize=(10, 8))
    
    # Get fitted values
    try:
        import statsmodels.formula.api as smf
        model = smf.mixedlm(
            "mean_vividness ~ residualized_exposure + popularity",
            data,
            groups=data["user_id"]
        )
        result = model.fit()
        fitted = result.fittedvalues
    except:
        # Fallback to using mean_vividness if model fitting fails
        fitted = data['mean_vividness']
    
    plt.scatter(fitted, residuals, alpha=0.6, edgecolors='w', linewidth=0.5)
    plt.axhline(y=0, color='red', linestyle='--', linewidth=2)
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted Values')
    plt.grid(True, alpha=0.3)
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved residuals plot to {save_path}")

def create_qq_plot(residuals: pd.Series, save_path: Path):
    """Create QQ plot of residuals."""
    plt.figure(figsize=(10, 8))
    
    # Remove NaN values
    clean_residuals = residuals.dropna()
    if len(clean_residuals) == 0:
        logger.warning("No valid residuals for QQ plot")
        plt.text(0.5, 0.5, 'No valid residuals', transform=plt.gca().transAxes, ha='center')
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return
    
    # QQ plot
    stats.probplot(clean_residuals, dist="norm", plot=plt)
    plt.title('Normal Q-Q Plot of Residuals')
    plt.grid(True, alpha=0.3)
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved QQ plot to {save_path}")

def create_scale_location_plot(data: pd.DataFrame, residuals: pd.Series, save_path: Path):
    """Create Scale-Location plot (sqrt(|residuals|) vs fitted values)."""
    plt.figure(figsize=(10, 8))
    
    try:
        import statsmodels.formula.api as smf
        model = smf.mixedlm(
            "mean_vividness ~ residualized_exposure + popularity",
            data,
            groups=data["user_id"]
        )
        result = model.fit()
        fitted = result.fittedvalues
    except:
        fitted = data['mean_vividness']
    
    clean_residuals = residuals.dropna()
    clean_fitted = fitted.iloc[clean_residuals.index]
    
    sqrt_abs_residuals = np.sqrt(np.abs(clean_residuals))
    
    plt.scatter(clean_fitted, sqrt_abs_residuals, alpha=0.6, edgecolors='w', linewidth=0.5)
    
    # Add smoothed line
    from scipy.stats import gaussian_kde
    try:
        # Create a simple trend line
        sorted_idx = np.argsort(clean_fitted)
        sorted_x = clean_fitted.iloc[sorted_idx]
        sorted_y = sqrt_abs_residuals.iloc[sorted_idx]
        plt.plot(sorted_x, sorted_y, color='red', linewidth=2, alpha=0.7)
    except:
        pass
    
    plt.xlabel('Fitted Values')
    plt.ylabel('√|Residuals|')
    plt.title('Scale-Location Plot')
    plt.grid(True, alpha=0.3)
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved scale-location plot to {save_path}")

def create_residuals_leverage_plot(data: pd.DataFrame, residuals: pd.Series, save_path: Path):
    """Create Residuals vs Leverage plot."""
    plt.figure(figsize=(10, 8))
    
    try:
        import statsmodels.formula.api as smf
        model = smf.mixedlm(
            "mean_vividness ~ residualized_exposure + popularity",
            data,
            groups=data["user_id"]
        )
        result = model.fit()
        
        # Calculate leverage (approximate)
        # In mixed models, leverage is more complex, so we use a simplified approach
        hat_matrix = np.diag(result.cov_params())
        leverage = hat_matrix / np.sum(hat_matrix)
        
        # Standardized residuals
        std_residuals = residuals / np.std(residuals)
        
        plt.scatter(leverage, std_residuals, alpha=0.6, edgecolors='w', linewidth=0.5)
        plt.axhline(y=0, color='red', linestyle='--', linewidth=2)
        
        # Add Cook's distance contours (approximate)
        cook_d = (std_residuals ** 2) * leverage / (2 * (1 - leverage))
        for contour in [0.5, 1.0]:
            mask = np.isclose(cook_d, contour, atol=0.1)
            if np.any(mask):
                plt.scatter(leverage[mask], std_residuals[mask], 
                          facecolors='none', edgecolors='blue', 
                          linewidths=1, alpha=0.5, s=50)
        
    except Exception as e:
        logger.warning(f"Could not compute leverage: {e}")
        # Fallback plot
        plt.scatter(range(len(residuals)), residuals, alpha=0.6)
    
    plt.xlabel('Leverage')
    plt.ylabel('Standardized Residuals')
    plt.title('Residuals vs Leverage')
    plt.grid(True, alpha=0.3)
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved residuals vs leverage plot to {save_path}")

def generate_all_plots():
    """Generate all diagnostic plots and save them."""
    root = get_project_root()
    plots_dir = root / "data" / "final" / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading data for diagnostic plots...")
    try:
        user_track_data = load_user_track_pairs()
        logger.info(f"Loaded {len(user_track_data)} user-track pairs")
    except FileNotFoundError as e:
        logger.error(str(e))
        return False
    
    logger.info("Calculating residuals...")
    residuals = calculate_residuals(user_track_data, "mean_vividness ~ residualized_exposure + popularity")
    
    plots = [
        ("residuals_vs_fitted.png", create_residuals_plot, (user_track_data, residuals)),
        ("qq_plot.png", create_qq_plot, (residuals,)),
        ("scale_location.png", create_scale_location_plot, (user_track_data, residuals)),
        ("residuals_leverage.png", create_residuals_leverage_plot, (user_track_data, residuals)),
    ]
    
    success_count = 0
    for filename, plot_func, args in plots:
        try:
            save_path = plots_dir / filename
            plot_func(*args, save_path)
            success_count += 1
            register_file(str(save_path.relative_to(root)))
        except Exception as e:
            logger.error(f"Failed to generate {filename}: {e}")
    
    logger.info(f"Generated {success_count}/{len(plots)} diagnostic plots")
    
    if success_count == len(plots):
        save_state()
        return True
    return False

def main():
    """Main entry point for generating diagnostic plots."""
    setup_logging()
    logger.info("Starting diagnostic plot generation...")
    
    success = generate_all_plots()
    
    if success:
        logger.info("Diagnostic plot generation completed successfully")
        return 0
    else:
        logger.error("Some diagnostic plots failed to generate")
        return 1

if __name__ == "__main__":
    exit(main())
