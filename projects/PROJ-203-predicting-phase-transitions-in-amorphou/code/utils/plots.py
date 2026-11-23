"""
Plotting helpers for SHAP and partial dependence visualization.

This module provides functions to generate standard interpretability plots
for the machine learning models trained on amorphous solid data.

Dependencies:
    - shap
    - matplotlib
    - seaborn
    - pandas
    - numpy
"""
import os
import json
from pathlib import Path
from typing import Optional, Union, Dict, Any, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Optional import for SHAP; fail loudly if not present as it's a core dependency
try:
    import shap
except ImportError:
    raise ImportError(
        "The 'shap' library is required for plotting interpretability. "
        "Please install it via 'pip install shap'."
    )

from utils.logging_config import get_missing_data_logger
from utils.validators import validate_physical_bounds

logger = get_missing_data_logger(__name__)

# Ensure output directories exist
PLOTS_DIR = Path("docs/reports/shap_plots")
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Global style settings for scientific plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("deep")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 9


def plot_shap_summary(
    shap_values: Union[shap.SummaryPlot, np.ndarray],
    features: pd.DataFrame,
    model_type: str = "regressor",
    output_path: Optional[Path] = None,
    family: Optional[str] = None
) -> Path:
    """
    Generate a SHAP summary plot (beeswarm) showing feature importance.
    
    Args:
        shap_values: SHAP values object or array from a model explainer.
        features: DataFrame containing the feature names and values used for explanation.
        model_type: 'regressor' or 'classifier' to adjust title.
        output_path: Optional path to save the plot. Defaults to docs/reports/shap_plots/.
        family: Optional chemical family name to include in the filename.
        
    Returns:
        Path to the saved plot file.
    """
    if shap_values is None:
        logger.error("SHAP values are None; cannot generate summary plot.")
        raise ValueError("shap_values cannot be None")
        
    if features is None or features.empty:
        logger.error("Feature DataFrame is empty or None; cannot generate summary plot.")
        raise ValueError("features DataFrame cannot be empty")

    # Prepare filename
    if family:
        filename = f"shap_summary_{model_type}_{family}.png"
    else:
        filename = f"shap_summary_{model_type}.png"
        
    if output_path is None:
        output_path = PLOTS_DIR / filename
    else:
        output_path = Path(output_path)

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the plot
    plt.figure(figsize=(10, 8))
    
    # Handle both SHAP summary plot objects and raw arrays
    if isinstance(shap_values, shap.plots.Bar) or hasattr(shap_values, 'values'):
        # If it's a SHAP object, try to plot directly or extract values
        # Standard SHAP workflow: explainer(shap_values)
        try:
            shap.summary_plot(shap_values, features, plot_type="dot", show=False)
        except Exception as e:
            logger.warning(f"Standard summary_plot failed: {e}. Attempting fallback.")
            # Fallback: manual plot if SHAP object is malformed
            if hasattr(shap_values, 'values'):
                vals = shap_values.values
            else:
                vals = np.array(shap_values)
            shap.summary_plot(vals, features, plot_type="dot", show=False)
    else:
        # Assume raw array
        shap.summary_plot(shap_values, features, plot_type="dot", show=False)

    plt.title(f"SHAP Summary Plot ({model_type.capitalize()})")
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved SHAP summary plot to {output_path}")
    return output_path


def plot_shap_beeswarm(
    shap_values: np.ndarray,
    features: pd.DataFrame,
    output_path: Optional[Path] = None,
    title: Optional[str] = None
) -> Path:
    """
    Generate a specific beeswarm-style SHAP plot for detailed distribution analysis.
    
    Args:
        shap_values: 2D numpy array of SHAP values (samples x features).
        features: DataFrame of feature values.
        output_path: Path to save the plot.
        title: Optional custom title.
        
    Returns:
        Path to the saved plot.
    """
    if shap_values.shape[0] != len(features):
        raise ValueError(f"Shape mismatch: SHAP values ({shap_values.shape[0]}) vs features ({len(features)})")

    if output_path is None:
        output_path = PLOTS_DIR / "shap_beeswarm.png"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 10))
    shap.plots.beeswarm(shap_values, features, show=False)
    
    if title:
        plt.title(title)
    else:
        plt.title("SHAP Beeswarm Plot")
        
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved SHAP beeswarm plot to {output_path}")
    return output_path


def plot_partial_dependence(
    model,
    features: pd.DataFrame,
    target_feature: str,
    feature_range: Optional[tuple] = None,
    n_points: int = 20,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a partial dependence plot (PDP) for a specific feature.
    
    Args:
        model: Trained model object (must support .predict).
        features: DataFrame containing the data used for training.
        target_feature: Name of the feature to plot.
        feature_range: Optional tuple (min, max) for the feature range.
                       If None, uses min/max of the data.
        n_points: Number of points to evaluate the PDP.
        output_path: Path to save the plot.
        
    Returns:
        Path to the saved plot.
    """
    if target_feature not in features.columns:
        raise ValueError(f"Feature '{target_feature}' not found in DataFrame. Columns: {list(features.columns)}")

    if output_path is None:
        # Sanitize filename
        safe_name = "".join([c if c.isalnum() or c in ('_', '-') else '_' for c in target_feature])
        output_path = PLOTS_DIR / f"pdp_{safe_name}.png"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine range
    if feature_range:
        min_val, max_val = feature_range
    else:
        min_val = features[target_feature].min()
        max_val = features[target_feature].max()
        
    # Create grid values
    grid_values = np.linspace(min_val, max_val, n_points)
    pdp_values = []

    # Make copies to avoid modifying original
    base_features = features.copy()

    for val in grid_values:
        # Create a copy for this point
        temp_features = base_features.copy()
        temp_features[target_feature] = val
        
        try:
            pred = model.predict(temp_features)
            pdp_values.append(np.mean(pred))
        except Exception as e:
            logger.error(f"Prediction failed for value {val} in PDP: {e}")
            pdp_values.append(np.nan)

    pdp_values = np.array(pdp_values)

    plt.figure(figsize=(10, 6))
    plt.plot(grid_values, pdp_values, marker='o', linestyle='-', color='darkblue')
    plt.xlabel(target_feature.replace('_', ' ').title())
    plt.ylabel("Partial Dependence (Predicted Value)")
    plt.title(f"Partial Dependence Plot: {target_feature}")
    plt.grid(True, alpha=0.3)
    
    # Add min/max lines for context
    plt.axvline(x=base_features[target_feature].mean(), color='gray', linestyle='--', label='Mean')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved Partial Dependence Plot for '{target_feature}' to {output_path}")
    return output_path


def plot_feature_importance_bar(
    importances: Dict[str, float],
    top_n: int = 10,
    output_path: Optional[Path] = None,
    title: Optional[str] = None
) -> Path:
    """
    Plot a bar chart of feature importances (e.g., from Random Forest).
    
    Args:
        importances: Dictionary mapping feature names to importance scores.
        top_n: Number of top features to display.
        output_path: Path to save the plot.
        title: Optional custom title.
        
    Returns:
        Path to the saved plot.
    """
    if not importances:
        logger.warning("Importance dictionary is empty.")
        return output_path or (PLOTS_DIR / "feature_importance_empty.png")

    # Sort and slice
    sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:top_n]
    names = [f[0] for f in sorted_features]
    scores = [f[1] for f in sorted_features]

    if output_path is None:
        output_path = PLOTS_DIR / "feature_importance_bar.png"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 8))
    # Reverse for horizontal bar chart so top is at the top
    plt.barh(names[::-1], scores[::-1], color='steelblue')
    plt.xlabel("Importance Score")
    plt.ylabel("Feature")
    
    if title:
        plt.title(title)
    else:
        plt.title(f"Top {top_n} Feature Importances")
        
    plt.gca().invert_yaxis() # Ensure top feature is at top
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved Feature Importance Bar chart to {output_path}")
    return output_path


def save_plot_metadata(
    plot_type: str,
    features_used: List[str],
  model_type: str,
  family: Optional[str] = None,
  output_dir: Optional[Path] = None
) -> Path:
    """
    Save metadata about the generated plots for reproducibility.
    
    Args:
        plot_type: Type of plot generated (e.g., 'summary', 'pdp').
        features_used: List of feature names involved.
        model_type: Type of model (regressor/classifier).
        family: Chemical family if applicable.
        output_dir: Directory to save metadata JSON.
        
    Returns:
        Path to the metadata file.
    """
    if output_dir is None:
        output_dir = PLOTS_DIR
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    meta_filename = f"plot_metadata_{plot_type}_{model_type}"
    if family:
        meta_filename += f"_{family}"
    meta_filename += ".json"
    
    meta_path = output_dir / meta_filename
    
    metadata = {
        "plot_type": plot_type,
        "model_type": model_type,
        "family": family,
        "features_used": features_used,
        "generated_at": pd.Timestamp.now().isoformat()
    }
    
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Saved plot metadata to {meta_path}")
    return meta_path