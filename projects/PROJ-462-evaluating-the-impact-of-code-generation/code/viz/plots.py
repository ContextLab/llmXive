import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

from viz.logging import get_viz_logger, log_operation_start, log_operation_end, log_plot_generation, log_warning, log_error

@dataclass
class BoxplotData:
    """Data structure for boxplot visualization."""
    data: pd.DataFrame
    x_variable: str
    y_variable: str
    hue_variable: str
    title: str
    xlabel: str
    ylabel: str
    interaction_lines: Optional[List[Tuple[str, str, float, float]]] = None

@dataclass
class VisualizationOutput:
    """Output structure for visualization results."""
    plot_type: str
    stratification_variable: str
    interaction_lines: List[Tuple[str, str, float, float]]
    file_path: str
    title: str
    summary_stats: Dict[str, Any]

def prepare_boxplot_data(
    df: pd.DataFrame,
    tool_usage_col: str = "tool_usage",
    experience_col: str = "experience_level",
    outcome_col: str = "task_time",
    title: str = "Task Time by Tool Usage and Experience Level"
) -> BoxplotData:
    """
    Prepare data for boxplot visualization stratified by experience level.
    
    Args:
        df: Input dataframe with required columns
        tool_usage_col: Column name for tool usage
        experience_col: Column name for experience level
        outcome_col: Column name for the outcome variable (e., task_time)
        title: Title for the plot
    
    Returns:
        BoxplotData object with prepared data and metadata
    """
    log_operation_start("prepare_boxplot_data")
    
    # Validate required columns exist
    missing_cols = []
    if tool_usage_col not in df.columns:
        missing_cols.append(tool_usage_col)
    if experience_col not in df.columns:
        missing_cols.append(experience_col)
    if outcome_col not in df.columns:
        missing_cols.append(outcome_col)
    
    if missing_cols:
        error_msg = f"Missing required columns: {', '.join(missing_cols)}"
        log_error(error_msg)
        raise ValueError(error_msg)
    
    # Ensure categorical types for proper plotting
    df_plot = df.copy()
    df_plot[tool_usage_col] = df_plot[tool_usage_col].astype(str)
    df_plot[experience_col] = df_plot[experience_col].astype(str)
    
    # Drop rows with missing values in key columns
    initial_count = len(df_plot)
    df_plot = df_plot.dropna(subset=[tool_usage_col, experience_col, outcome_col])
    dropped_count = initial_count - len(df_plot)
    
    if dropped_count > 0:
        log_warning(f"Dropped {dropped_count} rows with missing values for plotting")
    
    boxplot_data = BoxplotData(
        data=df_plot,
        x_variable=tool_usage_col,
        y_variable=outcome_col,
        hue_variable=experience_col,
        title=title,
        xlabel="Tool Usage",
        ylabel="Task Time (minutes)"
    )
    
    log_operation_end("prepare_boxplot_data", success=True)
    return boxplot_data

def calculate_interaction_lines(
    data: pd.DataFrame,
    x_variable: str,
    y_variable: str,
    hue_variable: str
) -> List[Tuple[str, str, float, float]]:
    """
    Calculate means for each group to draw interaction lines connecting group means.
    
    Args:
        data: Input dataframe
        x_variable: Column name for x-axis (tool usage)
        y_variable: Column name for y-axis (outcome)
        hue_variable: Column name for grouping (experience level)
    
    Returns:
        List of tuples (x1, x2, y1, y2) representing line segments between means
    """
    log_operation_start("calculate_interaction_lines")
    
    # Calculate means for each combination
    means = data.groupby([x_variable, hue_variable])[y_variable].mean().reset_index()
    
    # Sort by x and hue to ensure consistent ordering
    means = means.sort_values([x_variable, hue_variable])
    
    interaction_lines = []
    unique_x = sorted(means[x_variable].unique())
    unique_hue = sorted(means[hue_variable].unique())
    
    # Create lines connecting means across experience levels for each tool usage
    for x_val in unique_x:
        x_points = []
        for h_val in unique_hue:
            subset = means[(means[x_variable] == x_val) & (means[hue_variable] == h_val)]
            if not subset.empty:
                mean_val = subset[y_variable].iloc[0]
                x_points.append((h_val, mean_val))
        
        # Connect consecutive points
        for i in range(len(x_points) - 1):
            x1, y1 = x_points[i]
            x2, y2 = x_points[i+1]
            # Map hue values to x positions for plotting
            interaction_lines.append((str(x1), str(x2), y1, y2))
    
    log_operation_end("calculate_interaction_lines", success=True)
    return interaction_lines

def render_boxplot(
    boxplot_data: BoxplotData,
    output_path: str,
    figsize: Tuple[int, int] = (10, 6),
    dpi: int = 300,
    style: str = "whitegrid"
) -> VisualizationOutput:
    """
    Render a publication-ready boxplot with interaction lines.
    
    Args:
        boxplot_data: Prepared BoxplotData object
        output_path: Path to save the figure (must end in .png)
        figsize: Figure size tuple
        dpi: Resolution for saving
        style: Seaborn style ('whitegrid', 'darkgrid', 'ticks', etc.)
    
    Returns:
        VisualizationOutput object with metadata and file path
    """
    log_operation_start("render_boxplot")
    
    # Validate output path
    if not output_path.endswith('.png'):
        output_path = output_path + '.png'
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    sns.set_style(style)
    
    # Create boxplot
    sns.boxplot(
        data=boxplot_data.data,
        x=boxplot_data.x_variable,
        y=boxplot_data.y_variable,
        hue=boxplot_data.hue_variable,
        ax=ax,
        palette="Set2",
        linewidth=1.5,
        fliersize=3
    )
    
    # Add interaction lines if available
    if boxplot_data.interaction_lines:
        # Calculate means again for drawing lines
        means = boxplot_data.data.groupby([boxplot_data.x_variable, boxplot_data.hue_variable])[boxplot_data.y_variable].mean().reset_index()
        
        # Get unique categories for positioning
        x_categories = sorted(means[boxplot_data.x_variable].unique())
        hue_categories = sorted(means[boxplot_data.hue_variable].unique())
        
        # Draw lines connecting means across hue groups for each x category
        for x_cat in x_categories:
            line_data = means[means[boxplot_data.x_variable] == x_cat]
            line_data = line_data.sort_values(boxplot_data.hue_variable)
            
            # Map hue categories to x positions (matplotlib positions)
            x_pos = x_categories.index(x_cat)
            hue_positions = [hue_categories.index(h) for h in line_data[boxplot_data.hue_variable]]
            y_values = line_data[boxplot_data.y_variable].values
            
            # Connect consecutive points
            for i in range(len(hue_positions) - 1):
                # Convert hue positions to x positions with offset
                offset = 0.25  # Offset from box center
                x1 = x_pos - offset + (hue_positions[i] * 0.5) / len(hue_categories)
                x2 = x_pos - offset + (hue_positions[i+1] * 0.5) / len(hue_categories)
                # Actually, simpler approach: just connect points at specific x offsets
                # For each x category, we have multiple hue groups at slightly different x positions
                # Standard seaborn boxplot positions hue groups at: x_pos - 0.2, x_pos, x_pos + 0.2
                n_hues = len(hue_categories)
                for j in range(n_hues - 1):
                    pos1 = x_pos - 0.2 + (j * 0.4) / (n_hues - 1)
                    pos2 = x_pos - 0.2 + ((j + 1) * 0.4) / (n_hues - 1)
                    y1 = line_data[boxplot_data.y_variable].iloc[j]
                    y2 = line_data[boxplot_data.y_variable].iloc[j+1]
                    ax.plot([pos1, pos2], [y1, y2], 'k-', alpha=0.6, linewidth=1.5)
    
    # Customize appearance for publication quality
    ax.set_title(boxplot_data.title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(boxplot_data.xlabel, fontsize=12)
    ax.set_ylabel(boxplot_data.ylabel, fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=10)
    ax.legend(title=boxplot_data.hue_variable, title_fontsize=11, fontsize=10)
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    # Calculate summary statistics for the output
    summary_stats = {}
    for tool in boxplot_data.data[boxplot_data.x_variable].unique():
        tool_data = boxplot_data.data[boxplot_data.data[boxplot_data.x_variable] == tool]
        summary_stats[tool] = {
            "count": len(tool_data),
            "mean": float(tool_data[boxplot_data.y_variable].mean()),
            "std": float(tool_data[boxplot_data.y_variable].std()),
            "min": float(tool_data[boxplot_data.y_variable].min()),
            "max": float(tool_data[boxplot_data.y_variable].max())
        }
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    # Get interaction lines for the output
    interaction_lines = calculate_interaction_lines(
        boxplot_data.data,
        boxplot_data.x_variable,
        boxplot_data.y_variable,
        boxplot_data.hue_variable
    )
    
    output = VisualizationOutput(
        plot_type="boxplot",
        stratification_variable=boxplot_data.hue_variable,
        interaction_lines=interaction_lines,
        file_path=output_path,
        title=boxplot_data.title,
        summary_stats=summary_stats
    )
    
    log_plot_generation(output_path, "success")
    log_operation_end("render_boxplot", success=True)
    return output

def run_viz_pipeline(
    input_data_path: str,
    output_dir: str,
    tool_usage_col: str = "tool_usage",
    experience_col: str = "experience_level",
    outcome_col: str = "task_time",
    title: str = "Task Time by Tool Usage and Experience Level"
) -> List[VisualizationOutput]:
    """
    Run the complete visualization pipeline.
    
    Args:
        input_data_path: Path to the input CSV file
        output_dir: Directory to save output figures
        tool_usage_col: Column name for tool usage
        experience_col: Column name for experience level
        outcome_col: Column name for outcome variable
        title: Title for the plot
    
    Returns:
        List of VisualizationOutput objects
    """
    log_operation_start("run_viz_pipeline")
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        df = pd.read_csv(input_data_path)
        log_plot_generation(f"Loaded data from {input_data_path}", "success")
    except Exception as e:
        log_error(f"Failed to load data: {str(e)}")
        raise
    
    # Prepare boxplot data
    boxplot_data = prepare_boxplot_data(
        df,
        tool_usage_col=tool_usage_col,
        experience_col=experience_col,
        outcome_col=outcome_col,
        title=title
    )
    
    # Render boxplot
    output_file = output_path / "productivity_boxplot.png"
    viz_output = render_boxplot(
        boxplot_data,
        str(output_file)
    )
    
    log_operation_end("run_viz_pipeline", success=True)
    return [viz_output]

def main():
    """Main entry point for the visualization module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate publication-ready visualizations")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output", type=str, required=True, help="Output directory for figures")
    parser.add_argument("--tool-col", type=str, default="tool_usage", help="Column name for tool usage")
    parser.add_argument("--exp-col", type=str, default="experience_level", help="Column name for experience level")
    parser.add_argument("--outcome-col", type=str, default="task_time", help="Column name for outcome variable")
    parser.add_argument("--title", type=str, default="Task Time by Tool Usage and Experience Level", help="Plot title")
    
    args = parser.parse_args()
    
    try:
        outputs = run_viz_pipeline(
            input_data_path=args.input,
            output_dir=args.output,
            tool_usage_col=args.tool_col,
            experience_col=args.exp_col,
            outcome_col=args.outcome_col,
            title=args.title
        )
        
        for output in outputs:
            print(f"Generated visualization: {output.file_path}")
            print(f"  Type: {output.plot_type}")
            print(f"  Stratification: {output.stratification_variable}")
            print(f"  Title: {output.title}")
        
        return 0
    except Exception as e:
        log_error(f"Pipeline failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())