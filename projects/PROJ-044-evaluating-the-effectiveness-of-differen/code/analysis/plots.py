"""
Plotting module for T026: Accuracy gap vs alpha, accuracy vs epsilon,
and specifically the minority vs global accuracy overlay plot.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np

# Configure matplotlib to use non-interactive backend for script execution
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

def load_filtered_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the filtered dataset produced by T035 (results/filtered_data.csv).
    
    Args:
        data_path: Path to the CSV file. Defaults to results/filtered_data.csv.
        
    Returns:
        DataFrame containing the filtered results.
        
    Raises:
        FileNotFoundError: If the data file does not exist.
    """
    if data_path is None:
        data_path = Path("results/filtered_data.csv")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Filtered data file not found at {data_path}. "
                              "Ensure T035 has been run successfully.")
    
    logger.info(f"Loading filtered data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Ensure required columns exist
    required_cols = ['seed', 'alpha', 'epsilon', 'global_accuracy', 
                    'minority_accuracy', 'majority_accuracy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in filtered data: {missing_cols}")
    
    return df

def plot_accuracy_gap_vs_alpha(df: pd.DataFrame, output_path: Path) -> None:
    """
    Plot accuracy gap (Global - Minority) vs alpha values.
    
    Args:
        df: Filtered DataFrame.
        output_path: Path to save the plot.
    """
    logger.info("Generating accuracy gap vs alpha plot")
    
    # Calculate accuracy gap
    df = df.copy()
    df['accuracy_gap'] = df['global_accuracy'] - df['minority_accuracy']
    
    plt.figure(figsize=(10, 6))
    
    # Group by alpha and calculate mean gap
    alpha_groups = df.groupby('alpha')['accuracy_gap'].mean()
    
    plt.plot(alpha_groups.index, alpha_groups.values, marker='o', 
            linestyle='-', linewidth=2, markersize=8, label='Mean Gap')
    
    # Add error bars (std deviation)
    alpha_std = df.groupby('alpha')['accuracy_gap'].std()
    plt.errorbar(alpha_groups.index, alpha_groups.values, yerr=alpha_std.values,
                fmt='none', ecolor='gray', capsize=5, alpha=0.7)
    
    plt.xlabel('Alpha (Dirichlet Heterogeneity Parameter)', fontsize=12)
    plt.ylabel('Accuracy Gap (Global - Minority)', fontsize=12)
    plt.title('Accuracy Gap vs Data Heterogeneity (Alpha)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved accuracy gap vs alpha plot to {output_path}")

def plot_accuracy_vs_epsilon(df: pd.DataFrame, output_path: Path) -> None:
    """
    Plot accuracy vs epsilon for different alpha values.
    
    Args:
        df: Filtered DataFrame.
        output_path: Path to save the plot.
    """
    logger.info("Generating accuracy vs epsilon plot")
    
    plt.figure(figsize=(10, 6))
    
    # Get unique alpha values
    alphas = sorted(df['alpha'].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(alphas)))
    
    for i, alpha in enumerate(alphas):
        alpha_df = df[df['alpha'] == alpha]
        # Sort by epsilon for smooth lines
        alpha_df = alpha_df.sort_values('epsilon')
        
        plt.plot(alpha_df['epsilon'], alpha_df['global_accuracy'], 
                marker='o', linewidth=2, markersize=6, 
                label=f'α={alpha}', color=colors[i])
    
    plt.xlabel('Privacy Budget (ε)', fontsize=12)
    plt.ylabel('Global Accuracy', fontsize=12)
    plt.title('Global Accuracy vs Privacy Budget (ε) by Heterogeneity (α)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved accuracy vs epsilon plot to {output_path}")

def plot_minority_degradation_overlay(df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate overlay plot showing minority-client degradation curves against 
    global accuracy curves as mandated by Constitution Principle VII.
    
    Y-axis: Accuracy
    X-axis: Epsilon (Privacy Budget)
    Lines: Global Accuracy and Minority Accuracy for each alpha value.
    
    Args:
        df: Filtered DataFrame.
        output_path: Path to save the plot (results/plots/minority_vs_global_overlay.png).
    """
    logger.info("Generating minority vs global accuracy overlay plot")
    
    # Create figure with larger size for clarity
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Get unique alpha values
    alphas = sorted(df['alpha'].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(alphas)))
    
    for i, alpha in enumerate(alphas):
        alpha_df = df[df['alpha'] == alpha].copy()
        # Sort by epsilon
        alpha_df = alpha_df.sort_values('epsilon')
        
        # Plot Global Accuracy
        ax.plot(alpha_df['epsilon'], alpha_df['global_accuracy'], 
               marker='s', linewidth=2.5, markersize=8, 
               label=f'Global (α={alpha})', color=colors[i], linestyle='-',
               alpha=0.9)
        
        # Plot Minority Accuracy
        ax.plot(alpha_df['epsilon'], alpha_df['minority_accuracy'], 
               marker='d', linewidth=2.5, markersize=8, 
               label=f'Minority (α={alpha})', color=colors[i], linestyle='--',
               alpha=0.9)
    
    # Add a reference line for random guessing (approx 1/num_classes for FEMNIST)
    # FEMNIST has 62 classes, so random guess ≈ 1.6%
    random_guess = 0.016
    ax.axhline(y=random_guess, color='gray', linestyle=':', 
              linewidth=1.5, alpha=0.5, label=f'Random Guess ({random_guess:.1%})')
    
    # Formatting
    ax.set_xlabel('Privacy Budget (ε)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Accuracy', fontsize=13, fontweight='bold')
    ax.set_title('Minority Client Degradation vs Global Accuracy\n'
                'Overlay Plot (Constitution Principle VII)', 
                fontsize=15, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='lower right', fontsize=10, framealpha=0.9)
    
    # Ensure y-axis starts at 0 for proper visualization of degradation
    ax.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    
    logger.info(f"Saved minority vs global overlay plot to {output_path}")
    
    # Validate that the file was created
    if not output_path.exists():
        raise RuntimeError(f"Failed to create plot file at {output_path}")

def generate_all_plots(data_path: Optional[Path] = None, 
                      output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Generate all required plots for T026.
    
    Args:
        data_path: Path to filtered data CSV. Defaults to results/filtered_data.csv.
        output_dir: Directory to save plots. Defaults to results/plots/.
        
    Returns:
        Dictionary mapping plot names to their file paths.
    """
    if output_dir is None:
        output_dir = Path("results/plots")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_filtered_data(data_path)
    
    plots = {}
    
    # 1. Accuracy gap vs alpha
    gap_path = output_dir / "accuracy_gap_vs_alpha.png"
    plot_accuracy_gap_vs_alpha(df, gap_path)
    plots['accuracy_gap_vs_alpha'] = gap_path
    
    # 2. Accuracy vs epsilon
    epsilon_path = output_dir / "accuracy_vs_epsilon.png"
    plot_accuracy_vs_epsilon(df, epsilon_path)
    plots['accuracy_vs_epsilon'] = epsilon_path
    
    # 3. Minority vs global overlay (CRITICAL for T026)
    overlay_path = output_dir / "minority_vs_global_overlay.png"
    plot_minority_degradation_overlay(df, overlay_path)
    plots['minority_vs_global_overlay'] = overlay_path
    
    logger.info(f"All plots generated successfully in {output_dir}")
    return plots

def main() -> None:
    """Main entry point for T026 plotting module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Default paths
        data_path = Path("results/filtered_data.csv")
        output_dir = Path("results/plots")
        
        # Check if data exists
        if not data_path.exists():
            logger.error(f"Data file not found: {data_path}")
            logger.error("Please run T035 (filter_utility_collapse) first to generate results/filtered_data.csv")
            sys.exit(1)
        
        # Generate all plots
        plots = generate_all_plots(data_path, output_dir)
        
        print("\n=== T026 Plot Generation Complete ===")
        for name, path in plots.items():
            print(f"  - {name}: {path}")
        
        # Verify the critical overlay plot exists
        overlay_path = output_dir / "minority_vs_global_overlay.png"
        if overlay_path.exists():
            print(f"\n✓ Critical overlay plot verified: {overlay_path}")
        else:
            print(f"\n✗ Critical overlay plot MISSING: {overlay_path}")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Error generating plots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()