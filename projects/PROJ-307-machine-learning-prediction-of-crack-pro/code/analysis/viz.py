"""
Visualization utilities for crack propagation analysis.

Includes functions for generating Partial Dependence Plots (PDPs),
log-log scatter plots, and regime maps for US3.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def generate_pd_plot(
    model,
    feature_name: str,
    X: pd.DataFrame,
    y: Optional[pd.Series] = None,
    out_path: Optional[Union[str, Path]] = None
) -> None:
    """
    Generate a Partial Dependence Plot for a given feature.
    
    Args:
        model: Trained model with predict method.
        feature_name: Name of the feature to plot.
        X: Feature dataframe.
        y: Target series (optional, for reference).
        out_path: Path to save the plot.
    """
    try:
        import matplotlib.pyplot as plt
        from sklearn.inspection import PartialDependenceDisplay
    except ImportError as e:
        logger.error(f"Missing dependencies for plotting: {e}")
        return

    fig, ax = plt.subplots()
    PartialDependenceDisplay.from_estimator(model, X, [feature_name], ax=ax)
    plt.title(f"Partial Dependence: {feature_name}")
    
    if out_path:
        plt.savefig(out_path)
        logger.info(f"Saved PDP to {out_path}")
    else:
        plt.show()

def plot_log_log_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    out_path: Optional[Union[str, Path]] = None
) -> None:
    """
    Plot a log-log scatter plot for da/dN vs Delta K.
    
    Args:
        df: DataFrame containing the data.
        x_col: Column name for x-axis (Delta K).
        y_col: Column name for y-axis (da/dN).
        out_path: Path to save the plot.
    """
    import matplotlib.pyplot as plt

    plt.figure(figsize=(8, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.5)
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f"Log-Log Scatter: {y_col} vs {x_col}")
    plt.grid(True, which="both", ls="-", alpha=0.2)

    if out_path:
        plt.savefig(out_path)
        logger.info(f"Saved log-log scatter to {out_path}")
    else:
        plt.show()

def plot_regime_map(
    df: pd.DataFrame,
    delta_k_col: str,
    regime_col: str,
    r2_col: str,
    out_path: Optional[Union[str, Path]] = None
) -> None:
    """
    Generate a regime map showing R^2 (or Delta R^2) across identified regimes.
    
    This visualizes the stability of model performance across Low, Mid, and High
    Delta K regions as identified by change-point detection.
    
    Args:
        df: DataFrame containing regime analysis results.
        delta_k_col: Column name for Delta K (x-axis, log scale).
        regime_col: Column name for regime labels (e.g., 'Low', 'Mid', 'High').
        r2_col: Column name for R^2 or Delta R^2 values.
        out_path: Path to save the plot.
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    if not isinstance(df, pd.DataFrame) or df.empty:
        logger.warning("Empty or invalid DataFrame provided for regime map.")
        return

    # Ensure regime_col is categorical for consistent coloring
    if regime_col not in df.columns or delta_k_col not in df.columns or r2_col not in df.columns:
        logger.error(f"Missing required columns in regime map data: {regime_col}, {delta_k_col}, {r2_col}")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Create a scatter plot where x is Delta K, y is R^2, and hue is Regime
    # We use a categorical mapping for the regimes to ensure distinct colors
    unique_regimes = df[regime_col].unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(unique_regimes)))
    regime_colors = dict(zip(unique_regimes, colors))

    for regime in unique_regimes:
        subset = df[df[regime_col] == regime]
        if not subset.empty:
            ax.scatter(
                subset[delta_k_col],
                subset[r2_col],
                color=regime_colors[regime],
                label=regime,
                alpha=0.7,
                edgecolors='w',
                s=50
            )

    ax.set_xscale('log')
    ax.set_xlabel(r'$\Delta K$ (MPa$\sqrt{m}$)')
    ax.set_ylabel(r'$R^2$ (or $\Delta R^2$)')
    ax.set_title('Regime Map: Model Performance across Delta K Regions')
    ax.legend(title='Regime')
    ax.grid(True, which="both", ls="-", alpha=0.2)

    if out_path:
        plt.savefig(out_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved regime map to {out_path}")
    else:
        plt.show()

def plot_top_feature_pdps(
    model,
    X: pd.DataFrame,
    feature_names: List[str],
    out_dir: Union[str, Path]
) -> None:
    """
    Generate Partial Dependence Plots for the top 3 non-Delta K features.
    
    Args:
        model: Trained model (Random Forest or XGBoost).
        X: Feature dataframe used for training.
        feature_names: List of feature names to plot (should be top 3).
        out_dir: Directory to save the generated plots.
    """
    try:
        import matplotlib.pyplot as plt
        from sklearn.inspection import PartialDependenceDisplay
    except ImportError as e:
        logger.error(f"Missing dependencies for PDP generation: {e}")
        return

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating PDPs for features: {feature_names}")

    fig, axes = plt.subplots(1, len(feature_names), figsize=(6 * len(feature_names), 5), sharey=True)
    if len(feature_names) == 1:
        axes = [axes]

    for ax, feat in zip(axes, feature_names):
        if feat not in X.columns:
            logger.warning(f"Feature {feat} not found in X. Skipping.")
            continue
        
        # Generate PDP for this feature
        PartialDependenceDisplay.from_estimator(
            model, X, [feat], ax=ax, kind='average'
        )
        ax.set_title(f"Partial Dependence: {feat}")
        ax.set_xlabel(feat)
        
        # Save individual plot
        individual_path = out_path / f"pdp_{feat.replace(' ', '_').replace('/', '_')}.png"
        plt.savefig(individual_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved individual PDP to {individual_path}")

    plt.tight_layout()
    combined_path = out_path / "top_features_pdps_combined.png"
    plt.savefig(combined_path, dpi=150, bbox_inches='tight')
    logger.info(f"Saved combined PDPs to {combined_path}")
    plt.close()

def save_regime_map_and_pdps(
    regime_df: pd.DataFrame,
    model,
    X: pd.DataFrame,
    top_features: List[str],
    delta_k_col: str,
    regime_col: str,
    r2_col: str,
    output_dir: Union[str, Path]
) -> None:
    """
    Orchestrate the generation of the regime map and top feature PDPs.
    
    This function is the main entry point for T032 visualization requirements.
    
    Args:
        regime_df: DataFrame containing regime analysis results (Delta K, Regime, R^2).
        model: Trained model for PDP generation.
        X: Feature dataframe.
        top_features: List of top 3 feature names to plot PDPs for.
        delta_k_col: Column name for Delta K in regime_df.
        regime_col: Column name for regime labels in regime_df.
        r2_col: Column name for R^2 values in regime_df.
        output_dir: Directory to save all generated figures.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Generate Regime Map
    regime_map_path = output_path / "regime_map.png"
    plot_regime_map(
        df=regime_df,
        delta_k_col=delta_k_col,
        regime_col=regime_col,
        r2_col=r2_col,
        out_path=regime_map_path
    )

    # 2. Generate Top Feature PDPs
    plot_top_feature_pdps(
        model=model,
        X=X,
        feature_names=top_features,
        out_dir=output_path
    )

    logger.info(f"All visualization artifacts saved to {output_path}")
