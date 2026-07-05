import os
import logging
import math
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Import config utilities from the project's existing API
from src.utils.config import get_project_root, get_processed_data_dir, get_figures_dir
from src.utils.logging import setup_logger

# Ensure we have the logger set up
logger = setup_logger("viz_t035")

def load_final_dataset() -> pd.DataFrame:
    """
    Loads the final processed dataset containing vocal complexity metrics
    and noise levels.
    """
    processed_dir = get_processed_data_dir()
    file_path = processed_dir / "final_dataset.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Final dataset not found at {file_path}. "
                                "Run T020 (preprocessing) first.")
    
    logger.info(f"Loading final dataset from {file_path}")
    df = pd.read_csv(file_path)
    
    # Expected columns based on project flow:
    # 'complexity_metric' (or similar), 'noise_level_db', 'species_id', 'location_id'
    # We assume the primary complexity metric is named 'complexity_metric' or the first numeric column
    # that isn't an ID. For robustness, we'll check for common names.
    target_cols = ['complexity_metric', 'syllable_count', 'spectral_entropy']
    complexity_col = None
    for col in target_cols:
        if col in df.columns:
            complexity_col = col
            break
    
    if complexity_col is None:
        # Fallback: try to find a numeric column that looks like a metric
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        # Exclude noise_level_db if it's the only other obvious numeric
        potential_metrics = [c for c in numeric_cols if c not in ['noise_level_db', 'species_id', 'location_id']]
        if potential_metrics:
            complexity_col = potential_metrics[0]
            logger.warning(f"Using '{complexity_col}' as complexity metric column.")
        else:
            raise ValueError("Could not identify a complexity metric column in the dataset.")
    
    required_cols = ['noise_level_db', complexity_col]
    # Check for IDs if needed for grouping, though for simple residual plots we might not need them
    # But for the model, we assume the data was prepared with these.
    
    return df, complexity_col

def calculate_regression_stats(df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, float]:
    """
    Calculates basic regression statistics (slope, intercept, r, p-value).
    Used for plotting regression lines if needed, though LME residuals are the focus here.
    """
    x = df[x_col].dropna()
    y = df[y_col].dropna()
    
    # Align indices after dropna
    min_len = min(len(x), len(y))
    x = x.iloc[:min_len]
    y = y.iloc[:min_len]
    
    if len(x) < 2:
        return {"slope": 0, "intercept": 0, "r": 0, "p_value": 1.0}
    
    slope, intercept, r, p_value, std_err = stats.linregress(x, y)
    return {
        "slope": slope,
        "intercept": intercept,
        "r": r,
        "p_value": p_value
    }

def generate_scatter_with_regression(df: pd.DataFrame, x_col: str, y_col: str, 
                                     out_path: Path, title: str = "Scatter Plot"):
    """
    Generates a scatter plot with regression line. (Already implemented in T033).
    Included here for completeness of the module API if called externally.
    """
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x=x_col, y=y_col, alpha=0.6)
    
    stats = calculate_regression_stats(df, x_col, y_col)
    x_vals = np.linspace(df[x_col].min(), df[x_col].max(), 100)
    y_vals = stats["slope"] * x_vals + stats["intercept"]
    
    plt.plot(x_vals, y_vals, 'r-', label=f'Regression (r={stats["r"]:.2f})')
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved scatter plot to {out_path}")

def generate_heatmap_complexity_by_noise(df: pd.DataFrame, out_path: Path, 
                                         x_col: str = "noise_level_db", 
                                         y_col: str = "complexity_metric"):
    """
    Generates a heatmap mapping noise levels to complexity metrics. (Already implemented in T034).
    Included for API completeness.
    """
    # Bin the noise levels for the heatmap
    df_copy = df.copy()
    df_copy['noise_bin'] = pd.cut(df_copy[x_col], bins=10)
    pivot = df_copy.pivot_table(values=y_col, index='noise_bin', aggfunc='mean')
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap='YlOrRd')
    plt.title(f"Mean {y_col} by Noise Level Bins")
    plt.ylabel("Noise Level (dB)")
    plt.xlabel("Complexity")
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved heatmap to {out_path}")

def generate_residual_diagnostics(model_results: Dict[str, Any], df: pd.DataFrame, 
                                  complexity_col: str, noise_col: str = "noise_level_db",
                                  output_dir: Optional[Path] = None):
    """
    Generates residual diagnostics for the LME model.
    
    Since we don't have the actual fitted statsmodels object passed here (as it's in modeling.py),
    and the task requires generating plots from the LME model, we need to either:
    1. Re-fit the model here (expensive, redundant).
    2. Load pre-calculated residuals from a file generated by T024/T028.
    3. Expect the caller to pass the fitted model or residuals.
    
    Looking at the task description: "Implement ... to generate residual plots from the LME model".
    The existing API surface for `src/analysis/modeling.py` has `generate_residual_diagnostics`.
    However, T035 specifically asks to implement this in `viz.py`.
    
    Strategy:
    - We will attempt to fit the LME model here using statsmodels to get residuals.
    - If the model fitting is too heavy or dependencies are missing, we will assume
      the 'model_results' dict passed in contains the necessary residuals or we load them.
    
    However, the prompt says "Implement ... to generate residual plots".
    To be robust and self-contained for this task, we will:
    1. Try to load the model results if they were saved by T024 (modeling.py).
    2. If not, we will fit a simple OLS or LME (if statsmodels mixedlm is available) to generate the plots.
    
    Given the constraints of a single task implementation, and that T024 is a prerequisite,
    we assume the model was fitted. But `viz.py` shouldn't re-fit.
    
    Let's assume the `modeling.py` task (T024) saved the residuals to `data/interim/model_residuals.csv`.
    If that file doesn't exist, we will try to compute them on the fly using a simple OLS fit 
    as a proxy for the LME residuals if the full LME object isn't available, 
    OR we will raise a clear error if the expected data isn't there.
    
    Actually, looking at T028 in tasks.md: "Implement ... to generate residual diagnostics ... and save to data/figures/".
    T035 is "Implement ... to generate residual plots from the LME model".
    It seems T028 and T035 overlap. T035 is in US3 (Visualization), T028 in US2 (Modeling).
    T028 likely generates the plots during modeling. T035 might be a re-implementation or a specific
    visualization task for the report.
    
    We will implement `generate_residual_diagnostics` in `viz.py` to:
    1. Load the final dataset.
    2. Fit the LME model (using statsmodels) to get residuals.
    3. Plot: Residuals vs Fitted, Q-Q Plot.
    4. Save to `data/figures/`.
    
    This ensures the plots are generated from the real data and model logic, satisfying "real outputs".
    """
    if output_dir is None:
        output_dir = get_figures_dir()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if we can import statsmodels
    try:
        import statsmodels.api as sm
        from statsmodels.regression.mixed_linear_model import MixedLM
    except ImportError:
        logger.error("statsmodels is required for LME residual diagnostics.")
        raise

    # 1. Prepare Data
    # We need: Y (complexity), X (noise), groups (species, location)
    # Assuming the dataset has columns: 'complexity_metric', 'noise_level_db', 'species_id', 'location_id'
    
    # Re-load data to ensure we have the latest
    # We already have df passed in, but let's ensure columns exist
    if complexity_col not in df.columns or noise_col not in df.columns:
        raise ValueError(f"Dataset missing required columns. Expected {complexity_col} and {noise_col}")
    
    # Identify group columns
    group_cols = [c for c in df.columns if 'species' in c.lower() or 'location' in c.lower()]
    if not group_cols:
        # Fallback: try standard names
        group_cols = []
        if 'species_id' in df.columns: group_cols.append('species_id')
        if 'location_id' in df.columns: group_cols.append('location_id')
    
    if not group_cols:
        logger.warning("No group columns found. Using OLS instead of LME.")
        use_ols = True
    else:
        use_ols = False
    
    # Drop rows with missing values in critical columns
    cols_to_check = [complexity_col, noise_col] + group_cols
    clean_df = df.dropna(subset=cols_to_check)
    
    if len(clean_df) < 10:
        raise ValueError("Insufficient data for residual diagnostics after cleaning.")
    
    Y = clean_df[complexity_col].values
    X = sm.add_constant(clean_df[noise_col].values)
    
    residuals = []
    fitted_values = []
    
    if not use_ols and len(group_cols) > 0:
        # Try to fit LME
        # statsmodels MixedLM: endog, exog, groups, exog_re (optional)
        # We'll use a random intercept model: (1|species) + (1|location)
        # statsmodels doesn't easily handle multiple random effects in one go without complex formula API
        # or merging groups. We'll pick the primary group (species) for simplicity if multiple exist,
        # or try to fit a simple LME.
        
        # Let's try a simple LME with 'species_id' as the group
        group_col = 'species_id' if 'species_id' in clean_df.columns else group_cols[0]
        groups = clean_df[group_col]
        
        try:
            model = MixedLM(endog=Y, exog=X, groups=groups)
            result = model.fit()
            residuals = result.resid
            fitted_values = result.fittedvalues
            logger.info(f"LME Model fitted. AIC: {result.aic}")
        except Exception as e:
            logger.warning(f"LME fitting failed ({e}). Falling back to OLS.")
            use_ols = True
    
    if use_ols:
        # Fallback to OLS
        model = sm.OLS(Y, X)
        result = model.fit()
        residuals = result.resid
        fitted_values = result.fittedvalues
        logger.info("OLS Model fitted for residuals.")
    
    residuals = np.array(residuals)
    fitted_values = np.array(fitted_values)
    
    # 2. Plot 1: Residuals vs Fitted
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(fitted_values, residuals, alpha=0.6, edgecolors='w', linewidth=0.5)
    ax.axhline(0, color='red', linestyle='--', linewidth=1.5)
    ax.set_xlabel("Fitted Values")
    ax.set_ylabel("Residuals")
    ax.set_title("Residuals vs Fitted")
    ax.grid(True, alpha=0.3)
    
    # Add a lowess smooth line to check for patterns
    try:
        from statsmodels.nonparametric.smoothers_lowess import lowess
        z = lowess(residuals, fitted_values, frac=0.3)
        ax.plot(z[:, 0], z[:, 1], 'r-', lw=1, label='Lowess Smooth')
        ax.legend()
    except Exception:
        pass # Skip lowess if it fails
    
    path_resid_vs_fitted = output_dir / "residuals_vs_fitted.png"
    plt.savefig(path_resid_vs_fitted, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved residuals vs fitted to {path_resid_vs_fitted}")
    
    # 3. Plot 2: Q-Q Plot
    fig, ax = plt.subplots(figsize=(8, 8))
    sm.qqplot(residuals, line='45', fit=True, ax=ax)
    ax.set_title("Q-Q Plot of Residuals")
    
    path_qq = output_dir / "residual_qq_plot.png"
    plt.savefig(path_qq, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved Q-Q plot to {path_qq}")
    
    # 4. Plot 3: Histogram of Residuals
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.hist(residuals, bins=30, edgecolor='black', alpha=0.7)
    ax.set_xlabel("Residuals")
    ax.set_ylabel("Frequency")
    ax.set_title("Histogram of Residuals")
    ax.grid(True, alpha=0.3)
    
    path_hist = output_dir / "residual_histogram.png"
    plt.savefig(path_hist, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved residual histogram to {path_hist}")

def main():
    """
    Main entry point for T035: Generate residual plots from the LME model.
    """
    logger.info("Starting T035: Residual Diagnostics Generation")
    
    try:
        # Load data
        df, complexity_col = load_final_dataset()
        noise_col = "noise_level_db"
        
        # Ensure noise_col exists
        if noise_col not in df.columns:
            # Try to find it
            candidates = [c for c in df.columns if 'noise' in c.lower()]
            if candidates:
                noise_col = candidates[0]
                logger.warning(f"Using '{noise_col}' as noise column.")
            else:
                raise ValueError("Noise level column not found in dataset.")
        
        # Generate diagnostics
        generate_residual_diagnostics(
            model_results={}, # Not used directly, we fit inside
            df=df,
            complexity_col=complexity_col,
            noise_col=noise_col
        )
        
        logger.info("T035 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in T035: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()