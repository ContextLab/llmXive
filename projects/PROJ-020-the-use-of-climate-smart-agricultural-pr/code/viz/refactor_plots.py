"""
Refactored visualization utilities for consistent, maintainable plotting code.
Provides helper functions for figure management and style consistency.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Default figure settings
DEFAULT_FIGSIZE = (10, 6)
DEFAULT_DPI = 150
DEFAULT_STYLE = 'whitegrid'
DEFAULT_PALETTE = 'viridis'


def setup_figure(
    figsize: Tuple[float, float] = DEFAULT_FIGSIZE,
    dpi: int = DEFAULT_DPI,
    style: str = DEFAULT_STYLE,
    tight_layout: bool = True
) -> plt.Figure:
    """
    Set up a matplotlib figure with consistent styling.
    
    Args:
        figsize: Figure size (width, height)
        dpi: Dots per inch
        style: Seaborn style to use
        tight_layout: Whether to apply tight layout
        
    Returns:
        Configured matplotlib figure
    """
    # Apply seaborn style
    if style:
        sns.set_style(style)
        sns.set_context("notebook")
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Apply tight layout if requested
    if tight_layout:
        fig.tight_layout()
    
    logger.debug(f"Created figure with size {figsize}, dpi {dpi}")
    return fig, ax


def save_figure(
    fig: plt.Figure,
    output_path: Union[str, Path],
    format: str = 'png',
    dpi: Optional[int] = None,
    bbox_inches: str = 'tight'
) -> Path:
    """
    Save a figure to disk with consistent settings.
    
    Args:
        fig: Matplotlib figure to save
        output_path: Path to save the figure
        format: File format ('png', 'pdf', 'svg', etc.)
        dpi: Dots per inch (overrides figure DPI if specified)
        bbox_inches: Bbox adjustment ('tight' or None)
        
    Returns:
        Path to the saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure format is correct
    if output_path.suffix[1:] != format:
        output_path = output_path.with_suffix(f'.{format}')
    
    save_kwargs = {
        'dpi': dpi or DEFAULT_DPI,
        'bbox_inches': bbox_inches
    }
    
    fig.savefig(output_path, **save_kwargs)
    logger.info(f"Saved figure to {output_path}")
    
    return output_path


def add_timestamp_to_path(
    path: Union[str, Path],
    timestamp_format: str = "%Y%m%d_%H%M%S"
) -> Path:
    """
    Add a timestamp to a file path.
    
    Args:
        path: Original file path
        timestamp_format: Format string for timestamp
        
    Returns:
        New path with timestamp inserted before extension
    """
    path = Path(path)
    timestamp = datetime.now().strftime(timestamp_format)
    
    stem = path.stem
    suffix = path.suffix
    
    new_filename = f"{stem}_{timestamp}{suffix}"
    return path.parent / new_filename


def create_color_map(
    categorical_data: pd.Series,
    palette: str = DEFAULT_PALETTE,
    reverse: bool = False
) -> Dict[Any, str]:
    """
    Create a color mapping for categorical data.
    
    Args:
        categorical_data: Series with categorical values
        palette: Seaborn/matplotlib palette name
        reverse: Whether to reverse the palette
        
    Returns:
        Dictionary mapping categories to colors
    """
    unique_values = sorted(categorical_data.unique())
    n_colors = len(unique_values)
    
    # Get color palette
    if n_colors <= 10:
        colors = sns.color_palette(palette, n_colors)
    else:
        # Use continuous colormap for many categories
        cmap = sns.color_palette(palette, as_cmap=True)
        colors = [cmap(i / n_colors) for i in range(n_colors)]
    
    if reverse:
        colors = colors[::-1]
    
    return {val: color for val, color in zip(unique_values, colors)}


def format_axis_labels(
    ax: plt.Axes,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    title: Optional[str] = None,
    font_size: int = 12
) -> None:
    """
    Format axis labels and title with consistent styling.
    
    Args:
        ax: Matplotlib axes object
        xlabel: X-axis label
        ylabel: Y-axis label
        title: Plot title
        font_size: Font size for labels
    """
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=font_size)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=font_size)
    if title:
        ax.set_title(title, fontsize=font_size + 2, fontweight='bold')
    
    # Rotate x-axis labels if they're long
    labels = ax.get_xticklabels()
    if any(len(str(label)) > 10 for label in labels):
        plt.setp(labels, rotation=45, ha='right')


def add_grid_to_axes(ax: plt.Axes, alpha: float = 0.3) -> None:
    """
    Add a subtle grid to axes.
    
    Args:
        ax: Matplotlib axes object
        alpha: Transparency of grid lines
    """
    ax.grid(True, alpha=alpha, linestyle='--', linewidth=0.5)


def create_subplots_grid(
    n_plots: int,
    cols: int = 2,
    figsize_per_plot: Tuple[float, float] = (5, 4),
    **kwargs
) -> Tuple[plt.Figure, List[plt.Axes]]:
    """
    Create a grid of subplots.
    
    Args:
        n_plots: Total number of plots needed
        cols: Number of columns
        figsize_per_plot: Size of each individual plot
        **kwargs: Additional arguments to plt.subplots
        
    Returns:
        Tuple of (figure, axes list)
    """
    rows = (n_plots + cols - 1) // cols
    total_size = (figsize_per_plot[0] * cols, figsize_per_plot[1] * rows)
    
    fig, axes = plt.subplots(
        rows, cols,
        figsize=total_size,
        constrained_layout=True,
        **kwargs
    )
    
    # Flatten axes if single row or column
    if n_plots == 1:
        axes = [axes]
    elif rows == 1 or cols == 1:
        axes = axes.flatten()
    else:
        axes = axes.flatten()
    
    # Hide unused subplots
    for i in range(n_plots, len(axes)):
        axes[i].set_visible(False)
    
    return fig, axes[:n_plots]


def log_plot_metadata(
    plot_type: str,
    output_path: Path,
  figsize: Tuple[float, float],
  data_shape: Tuple[int, int],
  features: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log metadata about a generated plot.
    
    Args:
        plot_type: Type of plot created
        output_path: Path where plot was saved
        figsize: Figure size used
        data_shape: Shape of the underlying data
        features: Additional plot features
    """
    metadata = {
        'plot_type': plot_type,
        'output_path': str(output_path),
        'figsize': figsize,
        'data_shape': data_shape,
        'timestamp': datetime.now().isoformat()
    }
    
    if features:
        metadata.update(features)
    
    logger.info(f"Plot metadata: {metadata}")
