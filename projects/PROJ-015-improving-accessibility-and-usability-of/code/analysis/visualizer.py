import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure we can import from the project root if run as a script
# This is a safeguard for local execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def plot_completion_time(df: pd.DataFrame, output_path: Optional[str] = None) -> None:
    """
    Generates a box-plot visualization for Completion Time.
    
    Args:
        df: DataFrame containing 'completion_time' and 'interface_type' columns.
        output_path: Path to save the figure. Defaults to 'figures/completion_time.png'.
    """
    if output_path is None:
        output_path = str(PROJECT_ROOT / "figures" / "completion_time.png")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.figure(figsize=(10, 6))
    
    # Group by interface type for boxplot
    data_to_plot = [
        df[df['interface_type'] == 'Traditional']['completion_time'].dropna(),
        df[df['interface_type'] == 'Explainable']['completion_time'].dropna()
    ]
    
    labels = ['Traditional', 'Explainable']
    
    bp = plt.boxplot(data_to_plot, labels=labels, patch_artist=True)
    
    # Color coding
    colors = ['#4C72B0', '#55A868']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    plt.ylabel('Completion Time (seconds)')
    plt.title('Completion Time by Interface Type')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Saved completion time plot to {output_path}")

def plot_error_count(df: pd.DataFrame, output_path: Optional[str] = None) -> None:
    """
    Generates a box-plot visualization for Error Count.
    
    Args:
        df: DataFrame containing 'error_count' and 'interface_type' columns.
        output_path: Path to save the figure. Defaults to 'figures/error_count.png'.
    """
    if output_path is None:
        output_path = str(PROJECT_ROOT / "figures" / "error_count.png")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.figure(figsize=(10, 6))
    
    data_to_plot = [
        df[df['interface_type'] == 'Traditional']['error_count'].dropna(),
        df[df['interface_type'] == 'Explainable']['error_count'].dropna()
    ]
    
    labels = ['Traditional', 'Explainable']
    
    bp = plt.boxplot(data_to_plot, labels=labels, patch_artist=True)
    
    colors = ['#4C72B0', '#55A868']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    plt.ylabel('Error Count')
    plt.title('Error Count by Interface Type')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Saved error count plot to {output_path}")

def plot_sus_score(df: pd.DataFrame, output_path: Optional[str] = None) -> None:
    """
    Generates a box-plot visualization for SUS (System Usability Scale) scores.
    
    Args:
        df: DataFrame containing 'sus_score' and 'interface_type' columns.
        output_path: Path to save the figure. Defaults to 'figures/sus_score.png'.
    """
    if output_path is None:
        output_path = str(PROJECT_ROOT / "figures" / "sus_score.png")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.figure(figsize=(10, 6))
    
    # Prepare data for boxplot
    data_to_plot = [
        df[df['interface_type'] == 'Traditional']['sus_score'].dropna(),
        df[df['interface_type'] == 'Explainable']['sus_score'].dropna()
    ]
    
    labels = ['Traditional', 'Explainable']
    
    bp = plt.boxplot(data_to_plot, labels=labels, patch_artist=True,
                     whis=1.5)  # Standard boxplot whiskers
    
    # Color coding
    colors = ['#4C72B0', '#55A868']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    plt.ylabel('SUS Score (0-100)')
    plt.title('System Usability Scale (SUS) Score by Interface Type')
    plt.ylim(0, 105)  # SUS scores are 0-100
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"Saved SUS score plot to {output_path}")

def main():
    """
    Main entry point to generate all visualizations.
    Reads from data/processed/cleaned_sessions.csv and generates figures.
    """
    # Determine paths
    input_path = PROJECT_ROOT / "data" / "processed" / "cleaned_sessions.csv"
    
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        print("Please run the cleaning pipeline first (T021c-cli).")
        sys.exit(1)
    
    print(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)
    
    # Verify required columns exist
    required_cols = ['interface_type', 'completion_time', 'error_count', 'sus_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Error: Missing required columns in data: {missing}")
        sys.exit(1)
    
    print(f"Loaded {len(df)} records.")
    
    # Generate plots
    print("Generating Completion Time plot...")
    plot_completion_time(df)
    
    print("Generating Error Count plot...")
    plot_error_count(df)
    
    print("Generating SUS Score plot...")
    plot_sus_score(df)
    
    print("All visualizations generated successfully.")

if __name__ == "__main__":
    main()