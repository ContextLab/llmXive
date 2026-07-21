import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from scipy import stats

# Import project utilities
from config import get_project_root, get_config_dict
from utils import setup_logging, get_logger

# Configure logging
logger = get_logger(__name__)

# Constants
DEFAULT_CONFIG = {
    'plots_dir': 'data/final/plots',
    'regression_summary_path': 'data/final/regression_summary.csv',
    'user_track_pairs_path': 'data/processed/user_track_pairs.parquet'
}

def load_regression_results() -> pd.DataFrame:
    """Load the regression summary CSV."""
    root = get_project_root()
    path = root / DEFAULT_CONFIG['regression_summary_path']
    if not path.exists():
        raise FileNotFoundError(f"Regression summary not found at {path}. "
                                "Run T038 (generate_regression_summary) first.")
    return pd.read_csv(path)

def load_user_track_pairs() -> pd.DataFrame:
    """Load the user-track pairs dataset."""
    root = get_project_root()
    path = root / DEFAULT_CONFIG['user_track_pairs_path']
    if not path.exists():
        raise FileNotFoundError(f"User-track pairs not found at {path}. "
                                "Run T029 (generate_user_track_pairs) first.")
    return pd.read_parquet(path)

def calculate_residuals(model_results: Any, data: pd.DataFrame, 
                        formula: str) -> np.ndarray:
    """
    Calculate residuals from a fitted model.
    
    Note: This function expects the model_results object to have a 
    `resid` attribute (common in statsmodels).
    """
    if hasattr(model_results, 'resid'):
        return model_results.resid
    else:
        # Fallback: if we only have summary data, we cannot calculate residuals directly.
        # In a real pipeline, we would need to re-fit the model here or store residuals.
        # Since T038 generates a summary CSV, we assume we need to re-fit or 
        # that the pipeline context allows access to the fitted model object.
        # For this task, we assume the model was fitted in T033/T034 and we can
        # re-fit using the same formula and data to get residuals.
        import statsmodels.formula.api as smf
        try:
            model = smf.mixedlm(formula, data, groups=data["user_id"])
            result = model.fit()
            return result.resid
        except Exception as e:
            logger.error(f"Failed to re-fit model to calculate residuals: {e}")
            raise

def create_residuals_plot(residuals: np.ndarray, fitted_values: np.ndarray, 
                          output_path: Path) -> None:
    """Create a Residuals vs Fitted plot."""
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x=fitted_values, y=residuals, alpha=0.6, edgecolor='k')
    plt.axhline(y=0, color='r', linestyle='--', linewidth=2)
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Fitted')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved residuals plot to {output_path}")

def create_qq_plot(residuals: np.ndarray, output_path: Path) -> None:
    """Create a Normal Q-Q plot of residuals."""
    plt.figure(figsize=(10, 8))
    sm.qqplot(residuals, line='s', fit=True)
    plt.title('Normal Q-Q')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved Q-Q plot to {output_path}")

def create_scale_location_plot(residuals: np.ndarray, fitted_values: np.ndarray, 
                               output_path: Path) -> None:
    """Create a Scale-Location plot (sqrt(|residuals|) vs fitted)."""
    sqrt_abs_residuals = np.sqrt(np.abs(residuals))
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x=fitted_values, y=sqrt_abs_residuals, alpha=0.6, edgecolor='k')
    
    # Add a smoothed trend line
    if len(fitted_values) > 1:
        try:
            z = np.polyfit(fitted_values, sqrt_abs_residuals, 1)
            p = np.poly1d(z)
            plt.plot(fitted_values, p(fitted_values), "r--", linewidth=2, label="Trend")
            plt.legend()
        except Exception:
            pass
    
    plt.xlabel('Fitted Values')
    plt.ylabel(r'$\sqrt{|Residuals|}$')
    plt.title('Scale-Location')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved scale-location plot to {output_path}")

def create_residuals_leverage_plot(residuals: np.ndarray, leverage: np.ndarray, 
                                   output_path: Path) -> None:
    """Create a Residuals vs Leverage plot."""
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x=leverage, y=residuals, alpha=0.6, edgecolor='k')
    plt.axhline(y=0, color='r', linestyle='--', linewidth=2)
    
    # Add Cook's distance contours if possible (simplified here)
    # In statsmodels, leverage is often available via get_influence().hat_matrix_diag
    # We assume 'leverage' is passed in correctly.
    
    plt.xlabel('Leverage')
    plt.ylabel('Residuals')
    plt.title('Residuals vs Leverage')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved residuals vs leverage plot to {output_path}")

def generate_all_plots() -> List[str]:
    """
    Main function to generate all diagnostic plots.
    Returns a list of generated file paths.
    """
    root = get_project_root()
    config = get_config_dict()
    
    # Ensure plots directory exists
    plots_dir = root / DEFAULT_CONFIG['plots_dir']
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        pairs_df = load_user_track_pairs()
    except FileNotFoundError as e:
        logger.error(str(e))
        return []
    
    try:
        summary_df = load_regression_results()
    except FileNotFoundError as e:
        logger.error(str(e))
        return []
    
    # We need to re-fit the model to get residuals and leverage
    # Formula from T033: mean_vividness ~ residualized_exposure + popularity + (1|user_id)
    formula = "mean_vividness ~ residualized_exposure_score + overall_popularity_score"
    
    # Filter for non-nulls
    valid_cols = ['mean_vividness', 'residualized_exposure_score', 'overall_popularity_score', 'user_id']
    clean_df = pairs_df[valid_cols].dropna()
    
    if clean_df.empty:
        logger.error("No valid data to fit model for diagnostics.")
        return []
    
    logger.info(f"Fitting model for diagnostics on {len(clean_df)} rows...")
    
    import statsmodels.formula.api as smf
    model = smf.mixedlm(formula, clean_df, groups=clean_df["user_id"])
    result = model.fit()
    
    residuals = result.resid
    fitted_values = result.fittedvalues
    
    # Leverage
    influence = result.get_influence()
    leverage = influence.hat_matrix_diag
    
    generated_files = []
    
    # 1. Residuals vs Fitted
    path1 = plots_dir / "residuals_vs_fitted.png"
    create_residuals_plot(residuals, fitted_values, path1)
    generated_files.append(str(path1))
    
    # 2. Normal Q-Q
    path2 = plots_dir / "qq_plot.png"
    create_qq_plot(residuals, path2)
    generated_files.append(str(path2))
    
    # 3. Scale-Location
    path3 = plots_dir / "scale_location.png"
    create_scale_location_plot(residuals, fitted_values, path3)
    generated_files.append(str(path3))
    
    # 4. Residuals vs Leverage
    path4 = plots_dir / "residuals_vs_leverage.png"
    create_residuals_leverage_plot(residuals, leverage, path4)
    generated_files.append(str(path4))
    
    logger.info(f"Successfully generated {len(generated_files)} diagnostic plots.")
    return generated_files

def main():
    """Entry point for the script."""
    setup_logging()
    logger.info("Starting diagnostic plot generation (T040)...")
    
    try:
        files = generate_all_plots()
        if files:
            logger.info(f"Done. Generated files: {files}")
        else:
            logger.warning("No plots generated.")
    except Exception as e:
        logger.error(f"Failed to generate plots: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
