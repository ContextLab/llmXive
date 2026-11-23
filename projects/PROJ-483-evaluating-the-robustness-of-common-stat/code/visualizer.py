import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any, Optional
import numpy as np
import os

# Set style for scientific plotting
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10

def plot_error_rate_curve(
    df: pd.DataFrame,
    x_col: str = "dependency_strength",
    y_col: str = "observed_error_rate",
    hue_col: str = "test_type",
    style_col: Optional[str] = None,
    nominal_alpha: float = 0.05,
    output_path: Optional[str] = None
) -> None:
    """
    Plot Type I error rate curves against dependency strength.

    Args:
        df: DataFrame containing simulation results (aggregated.csv).
        x_col: Column name for dependency strength (r).
        y_col: Column name for observed error rate.
        hue_col: Column name for grouping by test type (e.g., 't-test', 'anova').
        style_col: Optional column for line styles (e.g., dependency structure).
        nominal_alpha: The nominal significance level (horizontal reference line).
        output_path: If provided, saves the figure to this path.
    """
    plt.figure(figsize=(10, 6))

    # Determine if we have a style column for different dependency structures
    if style_col and style_col in df.columns:
        sns.lineplot(
            data=df,
            x=x_col,
            y=y_col,
            hue=hue_col,
            style=style_col,
            marker="o",
            err_style="band",
            alpha=0.8
        )
    else:
        sns.lineplot(
            data=df,
            x=x_col,
            y=y_col,
            hue=hue_col,
            marker="o",
            err_style="band",
            alpha=0.8
        )

    # Add nominal alpha reference line
    plt.axhline(y=nominal_alpha, color='red', linestyle='--', label=f'Nominal $\alpha$={nominal_alpha}')

    plt.title('Type I Error Rate Inflation vs. Dependency Strength', fontsize=16)
    plt.xlabel('Dependency Strength ($r$)', fontsize=14)
    plt.ylabel('Observed Type I Error Rate', fontsize=14)
    plt.legend(title='Test Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()


def plot_power_comparison(
    df: pd.DataFrame,
    x_col: str = "dependency_strength",
    y_col: str = "observed_power",
    hue_col: str = "test_type",
    effect_size_col: Optional[str] = "effect_size",
    output_path: Optional[str] = None
) -> None:
    """
    Plot Power Loss Curves (US3): x=dependency strength, y=power.

    This visualizes how statistical power decreases as dependency strength increases
    for a fixed true effect size.

    Args:
        df: DataFrame containing power analysis results.
            Expected columns: dependency_strength, observed_power, test_type.
        x_col: Column name for dependency strength (r).
        y_col: Column name for observed power.
        hue_col: Column name for test type.
        effect_size_col: Column name for effect size (optional, for legend).
        output_path: If provided, saves the figure to this path.
    """
    plt.figure(figsize=(10, 6))

    # Prepare plotting data
    # If effect_size_col exists, we might want to facet or color by it,
    # but for the core US3 task, we usually fix effect size and vary r.
    # We assume the input df is already filtered or aggregated for a specific effect size
    # unless specified otherwise.

    if effect_size_col and effect_size_col in df.columns:
        # If multiple effect sizes exist, we might plot them as separate panels or styles.
        # For simplicity in this specific task, we plot lines grouped by test_type.
        # If the user wants to compare effect sizes, they should pass a filtered df.
        sns.lineplot(
            data=df,
            x=x_col,
            y=y_col,
            hue=hue_col,
            marker="s",
            linewidth=2,
            markersize=8
        )
    else:
        sns.lineplot(
            data=df,
            x=x_col,
            y=y_col,
            hue=hue_col,
            marker="s",
            linewidth=2,
            markersize=8
        )

    # Add baseline power reference (r=0) if present in data
    # This helps visualize the "loss"
    zero_r_data = df[df[x_col] == 0]
    if not zero_r_data.empty:
        # We don't draw a line for r=0, but we ensure the x-axis starts at 0
        pass

    plt.title('Statistical Power vs. Dependency Strength', fontsize=16)
    plt.xlabel('Dependency Strength ($r$)', fontsize=14)
    plt.ylabel('Observed Power', fontsize=14)
    plt.ylim(0, 1.05)
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.legend(title='Test Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()


def plot_ci_bands(
    df: pd.DataFrame,
    x_col: str = "dependency_strength",
    y_col: str = "observed_error_rate",
    ci_lower_col: str = "ci_lower",
    ci_upper_col: str = "ci_upper",
    hue_col: str = "test_type",
    output_path: Optional[str] = None
) -> None:
    """
    Plot error rate curves with Clopper-Pearson confidence interval bands.

    Args:
        df: DataFrame with columns for x, y, and CI bounds.
        x_col: Dependency strength column.
        y_col: Observed rate column.
        ci_lower_col: Lower bound of CI.
        ci_upper_col: Upper bound of CI.
        hue_col: Grouping column (e.g., test type).
        output_path: Path to save the figure.
    """
    plt.figure(figsize=(10, 6))

    # Sort by x to ensure lines are drawn correctly
    df = df.sort_values(by=[hue_col, x_col])

    for name, group in df.groupby(hue_col):
        plt.fill_between(
            group[x_col],
            group[ci_lower_col],
            group[ci_upper_col],
            alpha=0.2,
            label=f'{name} CI'
        )
        plt.plot(
            group[x_col],
            group[y_col],
            marker='o',
            label=name
        )

    plt.title('Type I Error Rate with 95% Clopper-Pearson Confidence Intervals', fontsize=16)
    plt.xlabel('Dependency Strength ($r$)', fontsize=14)
    plt.ylabel('Observed Error Rate', fontsize=14)
    plt.legend(title='Test Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    else:
        plt.show()