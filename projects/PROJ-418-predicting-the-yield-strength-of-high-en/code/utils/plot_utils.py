"""
Plot utility functions for HEA yield strength prediction.
Includes disclaimer injection for all generated figures.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Optional, Union
from .logging import get_logger

logger = get_logger(__name__)

DISCLAIMER_TEXT = "Associational analysis only; no causal inference"

def inject_disclaimer(
    fig: Optional[plt.Figure] = None,
    ax: Optional[plt.Axes] = None,
    position: tuple = (0.01, 0.01),
    fontsize: int = 8,
    color: str = 'gray',
    alpha: float = 0.7
) -> None:
    """
    Inject a mandatory disclaimer into a matplotlib figure or axes.

    This function appends the text "Associational analysis only; no causal inference"
    to the bottom-left corner of the specified figure or axes. If neither is provided,
    it attempts to use the current active figure/axes.

    Args:
        fig: The matplotlib Figure object. If None, uses plt.gcf().
        ax: The matplotlib Axes object. If None, uses plt.gca().
        position: (x, y) coordinates for the text placement (fraction of figure).
        fontsize: Font size for the disclaimer text.
        color: Text color.
        alpha: Transparency of the text.
    """
    if fig is None:
        fig = plt.gcf()
    if ax is None:
        ax = plt.gca()

    # Convert axes coordinates to figure coordinates for consistent placement
    # We want the text to appear in the bottom-left of the figure
    trans = fig.transFigure
    
    # Add text to the figure
    fig.text(
        position[0],
        position[1],
        DISCLAIMER_TEXT,
        fontsize=fontsize,
        color=color,
        alpha=alpha,
        transform=trans,
        ha='left',
        va='bottom'
    )
    
    logger.debug(f"Injected disclaimer into figure at position {position}")

def save_plot_with_disclaimer(
    filepath: str,
    fig: Optional[plt.Figure] = None,
    ax: Optional[plt.Axes] = None,
    **savefig_kwargs
) -> None:
    """
    Save a matplotlib figure to disk after injecting the mandatory disclaimer.

    This is a wrapper around plt.savefig that ensures the disclaimer is added
    before the file is written.

    Args:
        filepath: Path where the figure will be saved.
        fig: The matplotlib Figure object. If None, uses plt.gcf().
        ax: The matplotlib Axes object. If None, uses plt.gca().
        **savefig_kwargs: Additional arguments passed to plt.savefig().
    """
    # Ensure disclaimer is present
    inject_disclaimer(fig, ax)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(filepath)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    # Save the figure
    if fig is None:
        fig = plt.gcf()
        
    default_kwargs = {
        'dpi': 150,
        'bbox_inches': 'tight',
        'facecolor': 'white',
        'edgecolor': 'none'
    }
    default_kwargs.update(savefig_kwargs)
    
    fig.savefig(filepath, **default_kwargs)
    logger.info(f"Saved plot with disclaimer to: {filepath}")

def apply_disclaimer_to_current_figure(
    position: tuple = (0.01, 0.01),
    fontsize: int = 8,
    color: str = 'gray',
    alpha: float = 0.7
) -> None:
    """
    Convenience function to apply disclaimer to the currently active figure.
    
    Use this when you have already created a plot and just want to add the disclaimer
    before saving or displaying.
    
    Args:
        position: (x, y) coordinates for the text placement.
        fontsize: Font size for the disclaimer text.
        color: Text color.
        alpha: Transparency of the text.
    """
    inject_disclaimer(position=position, fontsize=fontsize, color=color, alpha=alpha)