"""
Module for saving generated plots to the data/visualization directory.
Implements T027: Save all plots to data/visualization/ directory with descriptive filenames.
"""
import os
import json
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
from code.visualization.plotter import generate_all_plots, load_error_rates, load_thresholds
from code.visualization.comparative_plots import generate_comparative_plots, load_low_sample_data

def ensure_output_directory(output_dir: str = "data/visualization") -> str:
    """
    Ensures the output directory exists. Creates it if it doesn't.
    
    Args:
        output_dir: Path to the output directory.
        
    Returns:
        The absolute path to the output directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.abspath(output_dir)

def get_plot_filename(test_type: str, metric: str, suffix: str = "") -> str:
    """
    Generates a descriptive filename for a plot.
    
    Args:
        test_type: The statistical test type (e.g., 't_test', 'anova', 'chi_squared').
        metric: The metric being plotted (e.g., 'type_i_error', 'power').
        suffix: Optional suffix for specific variations.
        
    Returns:
        A descriptive filename with .png extension.
    """
    # Sanitize inputs to ensure valid filenames
    safe_test = test_type.replace(" ", "_").replace("-", "_").lower()
    safe_metric = metric.replace(" ", "_").replace("-", "_").lower()
    
    base_name = f"{safe_test}_{safe_metric}"
    if suffix:
        safe_suffix = suffix.replace(" ", "_").replace("-", "_").lower()
        base_name = f"{base_name}_{safe_suffix}"
    
    return f"{base_name}.png"

def save_individual_plots(
    error_rates: List[Dict[str, Any]],
    thresholds: List[Dict[str, Any]],
    output_dir: str = "data/visualization"
) -> List[str]:
    """
    Saves individual plots for each test type and metric.
    
    Args:
        error_rates: List of error rate dictionaries from load_error_rates.
        thresholds: List of threshold dictionaries from load_thresholds.
        output_dir: Directory to save plots to.
        
    Returns:
        List of paths to saved plot files.
    """
    ensure_output_directory(output_dir)
    saved_files = []
    
    # Group error rates by test type
    test_types = set()
    for row in error_rates:
        if 'test_type' in row:
            test_types.add(row['test_type'])
    
    # Group by metric
    metrics = ['type_i_error', 'type_ii_error', 'power']
    
    for test_type in test_types:
        for metric in metrics:
            # Filter data for this test type and metric
            filtered_data = [
                row for row in error_rates 
                if row.get('test_type') == test_type
            ]
            
            if not filtered_data:
                continue
            
            # Create a figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot sample size vs metric
            sample_sizes = sorted(list(set(row.get('sample_size', 0) for row in filtered_data)))
            metric_values = []
            
            for n in sample_sizes:
                # Find the average metric value for this sample size
                values = [
                    row.get(metric, 0) 
                    for row in filtered_data 
                    if row.get('sample_size') == n
                ]
                if values:
                  metric_values.append(sum(values) / len(values))
                else:
                  metric_values.append(0)
            
            ax.plot(sample_sizes, metric_values, marker='o', label=f'{test_type} {metric}')
            
            # Add threshold line if available
            for threshold in thresholds:
                if threshold.get('test_type') == test_type and threshold.get('metric') == metric:
                    threshold_n = threshold.get('threshold_n')
                    if threshold_n:
                        ax.axvline(x=threshold_n, color='r', linestyle='--', label=f'Threshold ({metric})')
            
            ax.set_xlabel('Sample Size (n)')
            ax.set_ylabel(metric.replace('_', ' ').title())
            ax.set_title(f'{test_type.replace("_", " ").title()} - {metric.replace("_", " ").title()} vs Sample Size')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Save the plot
            filename = get_plot_filename(test_type, metric)
            filepath = os.path.join(output_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            saved_files.append(filepath)
            plt.close(fig)
    
    return saved_files

def save_comparative_plots(
    output_dir: str = "data/visualization"
) -> List[str]:
    """
    Saves comparative plots showing divergence between tests at low sample sizes.
    
    Args:
        output_dir: Directory to save plots to.
        
    Returns:
        List of paths to saved plot files.
    """
    ensure_output_directory(output_dir)
    saved_files = []
    
    # Load low sample data
    low_sample_data = load_low_sample_data("data/simulation/error_rates_summary.csv")
    
    if not low_sample_data:
        return saved_files
    
    # Generate comparative plots
    fig, axes = generate_comparative_plots(low_sample_data)
    
    # Save the comparative plot
    filename = "comparative_test_divergence_low_sample.png"
    filepath = os.path.join(output_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    saved_files.append(filepath)
    plt.close(fig)
    
    # Generate pairwise comparison if available
    pairwise_fig = plot_test_pairwise_divergence(low_sample_data)
    if pairwise_fig:
        filename = "pairwise_test_divergence_low_sample.png"
        filepath = os.path.join(output_dir, filename)
        pairwise_fig.savefig(filepath, dpi=150, bbox_inches='tight')
        saved_files.append(filepath)
        plt.close(pairwise_fig)
    
    return saved_files

def main():
    """
    Main function to generate and save all plots.
    """
    print("Starting plot generation and saving process...")
    
    # Load data
    error_rates = load_error_rates("data/simulation/error_rates_summary.csv")
    thresholds = load_thresholds("data/simulation/thresholds.json")
    
    if not error_rates:
        print("Error: No error rate data found. Please run the simulation first.")
        return
    
    if not thresholds:
        print("Warning: No threshold data found. Thresholds will be skipped.")
    
    # Save individual plots
    print("Saving individual plots...")
    individual_files = save_individual_plots(error_rates, thresholds)
    print(f"Saved {len(individual_files)} individual plots.")
    
    # Save comparative plots
    print("Saving comparative plots...")
    comparative_files = save_comparative_plots()
    print(f"Saved {len(comparative_files)} comparative plots.")
    
    all_saved = individual_files + comparative_files
    print(f"\nTotal plots saved: {len(all_saved)}")
    for file_path in all_saved:
        print(f"  - {file_path}")
    
    print("\nPlot generation and saving completed successfully.")

if __name__ == "__main__":
    main()