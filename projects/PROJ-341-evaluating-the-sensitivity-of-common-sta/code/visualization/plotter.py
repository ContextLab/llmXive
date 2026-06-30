import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt

# Constants for paths
DATA_DIR = "data/simulation"
VIS_DIR = "data/visualization"
THRESHOLDS_FILE = os.path.join(DATA_DIR, "thresholds.json")
ERROR_RATES_FILE = os.path.join(DATA_DIR, "error_rates_summary.csv")

def load_thresholds(filepath: str = THRESHOLDS_FILE) -> Dict[str, Any]:
    """Load threshold metrics from JSON file."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_error_rates(filepath: str = ERROR_RATES_FILE) -> List[Dict[str, Any]]:
    """Load aggregated error rates from CSV file."""
    if not os.path.exists(filepath):
        return []
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to float
            numeric_fields = ['sample_size', 'effect_size', 'type_i_error_rate', 
                              'type_i_error_lower_ci', 'type_i_error_upper_ci',
                              'type_ii_error_rate', 'power', 'power_lower_ci', 'power_upper_ci']
            for field in numeric_fields:
                if field in row:
                    try:
                        row[field] = float(row[field])
                    except (ValueError, TypeError):
                        pass
            data.append(row)
    return data

def plot_error_rate_vs_sample_size(
    test_type: str,
    effect_size: float,
    thresholds: Dict[str, Any],
    output_path: str
) -> None:
    """
    Plot error rates vs sample size with annotations for thresholds and nominal lines.
    
    Args:
        test_type: The statistical test type (e.g., 't-test', 'anova', 'chi-squared')
        effect_size: The effect size used in the simulation
        thresholds: Dictionary containing threshold data
        output_path: Path to save the plot
    """
    # Load data
    all_data = load_error_rates()
    
    # Filter for specific test type and effect size
    filtered_data = [
        row for row in all_data 
        if row.get('test_type') == test_type and abs(float(row.get('effect_size', 0)) - effect_size) < 1e-6
    ]
    
    if not filtered_data:
        print(f"No data found for test_type={test_type}, effect_size={effect_size}")
        return

    # Sort by sample size
    filtered_data.sort(key=lambda x: float(x['sample_size']))
    
    sample_sizes = [float(row['sample_size']) for row in filtered_data]
    type_i_rates = [float(row['type_i_error_rate']) for row in filtered_data]
    type_i_lower = [float(row['type_i_error_lower_ci']) for row in filtered_data]
    type_i_upper = [float(row['type_i_error_upper_ci']) for row in filtered_data]
    
    power_rates = [float(row['power']) for row in filtered_data]
    power_lower = [float(row['power_lower_ci']) for row in filtered_data]
    power_upper = [float(row['power_upper_ci']) for row in filtered_data]

    # Create figure with two subplots (Type I error and Power)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle(f'Statistical Test Sensitivity: {test_type} (Effect Size = {effect_size})', fontsize=14)

    # Plot Type I Error
    ax1.plot(sample_sizes, type_i_rates, 'b-', label='Type I Error Rate', linewidth=2)
    ax1.fill_between(sample_sizes, type_i_lower, type_i_upper, color='blue', alpha=0.2, label='95% CI')
    ax1.axhline(y=0.05, color='r', linestyle='--', label='Nominal Alpha (0.05)')
    ax1.set_ylabel('Type I Error Rate')
    ax1.set_title('Type I Error Rate vs Sample Size')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)

    # Annotate Type I Threshold
    if test_type in thresholds:
        for es_key, es_data in thresholds[test_type].items():
            # Check if this effect size matches (key might be string representation of float)
            try:
                if abs(float(es_key) - effect_size) < 1e-6:
                    threshold_n = es_data.get('type_i_threshold_n')
                    if threshold_n:
                        ax1.axvline(x=threshold_n, color='green', linestyle=':', linewidth=2, 
                                  label=f'Type I Threshold (n={threshold_n})')
                        ax1.text(threshold_n, 0.08, f'Threshold\nn={threshold_n}', 
                               color='green', ha='center', va='bottom', fontsize=10,
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
            except (ValueError, TypeError):
                continue

    # Plot Power
    ax2.plot(sample_sizes, power_rates, 'g-', label='Power (1 - Type II Error)', linewidth=2)
    ax2.fill_between(sample_sizes, power_lower, power_upper, color='green', alpha=0.2, label='95% CI')
    ax2.axhline(y=0.80, color='orange', linestyle='--', label='Target Power (0.80)')
    ax2.set_xlabel('Sample Size (n)')
    ax2.set_ylabel('Power')
    ax2.set_title('Power vs Sample Size')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)

    # Annotate Power Threshold
    if test_type in thresholds:
        for es_key, es_data in thresholds[test_type].items():
            try:
                if abs(float(es_key) - effect_size) < 1e-6:
                    power_threshold_n = es_data.get('power_threshold_n')
                    if power_threshold_n:
                        ax2.axvline(x=power_threshold_n, color='purple', linestyle=':', linewidth=2, 
                                  label=f'Power Threshold (n={power_threshold_n})')
                        ax2.text(power_threshold_n, 0.85, f'Power Threshold\nn={power_threshold_n}', 
                               color='purple', ha='center', va='bottom', fontsize=10,
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='plum', alpha=0.7))
            except (ValueError, TypeError):
                continue

    plt.tight_layout()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_all_tests_comparison(
    test_types: List[str],
    effect_size: float,
    thresholds: Dict[str, Any],
    output_path: str
) -> None:
    """
    Compare error rates across different test types for a fixed effect size.
    
    Args:
        test_types: List of test types to compare
        effect_size: The effect size to use for comparison
        thresholds: Dictionary containing threshold data
        output_path: Path to save the plot
    """
    all_data = load_error_rates()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle(f'Test Type Comparison at Effect Size = {effect_size}', fontsize=14)

    colors = {'t-test': 'blue', 'anova': 'green', 'chi-squared': 'red'}

    for test_type in test_types:
        filtered_data = [
            row for row in all_data 
            if row.get('test_type') == test_type and abs(float(row.get('effect_size', 0)) - effect_size) < 1e-6
        ]
        
        if not filtered_data:
            continue

        filtered_data.sort(key=lambda x: float(x['sample_size']))
        sample_sizes = [float(row['sample_size']) for row in filtered_data]
        type_i_rates = [float(row['type_i_error_rate']) for row in filtered_data]
        
        color = colors.get(test_type, 'black')
        ax1.plot(sample_sizes, type_i_rates, color=color, label=test_type, linewidth=2)

        # Add threshold annotation for Type I
        if test_type in thresholds:
            for es_key, es_data in thresholds[test_type].items():
                try:
                    if abs(float(es_key) - effect_size) < 1e-6:
                        threshold_n = es_data.get('type_i_threshold_n')
                        if threshold_n:
                            ax1.axvline(x=threshold_n, color=color, linestyle=':', alpha=0.5)
                except (ValueError, TypeError):
                    continue

    ax1.axhline(y=0.05, color='gray', linestyle='--', label='Nominal Alpha (0.05)')
    ax1.set_ylabel('Type I Error Rate')
    ax1.set_title('Type I Error Rate Comparison')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)

    # Power comparison
    for test_type in test_types:
        filtered_data = [
            row for row in all_data 
            if row.get('test_type') == test_type and abs(float(row.get('effect_size', 0)) - effect_size) < 1e-6
        ]
        
        if not filtered_data:
            continue

        filtered_data.sort(key=lambda x: float(x['sample_size']))
        sample_sizes = [float(row['sample_size']) for row in filtered_data]
        power_rates = [float(row['power']) for row in filtered_data]
        
        color = colors.get(test_type, 'black')
        ax2.plot(sample_sizes, power_rates, color=color, label=test_type, linewidth=2)

        # Add threshold annotation for Power
        if test_type in thresholds:
            for es_key, es_data in thresholds[test_type].items():
                try:
                    if abs(float(es_key) - effect_size) < 1e-6:
                        power_threshold_n = es_data.get('power_threshold_n')
                        if power_threshold_n:
                            ax2.axvline(x=power_threshold_n, color=color, linestyle=':', alpha=0.5)
                except (ValueError, TypeError):
                    continue

    ax2.axhline(y=0.80, color='gray', linestyle='--', label='Target Power (0.80)')
    ax2.set_xlabel('Sample Size (n)')
    ax2.set_ylabel('Power')
    ax2.set_title('Power Comparison')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_all_plots() -> None:
    """Generate all visualization plots with annotations."""
    os.makedirs(VIS_DIR, exist_ok=True)
    
    # Load thresholds once
    thresholds = load_thresholds()
    
    # Define test types and effect sizes based on typical simulation runs
    test_types = ['t-test', 'anova', 'chi-squared']
    effect_sizes = [0.2, 0.5, 0.8]  # Small, Medium, Large

    for test_type in test_types:
        for effect_size in effect_sizes:
            # Check if we have data for this combination
            all_data = load_error_rates()
            has_data = any(
                row.get('test_type') == test_type and abs(float(row.get('effect_size', 0)) - effect_size) < 1e-6
                for row in all_data
            )
            
            if not has_data:
                continue

            filename = f"{test_type}_effect_{effect_size:.1f}_annotated.png"
            output_path = os.path.join(VIS_DIR, filename)
            
            try:
                plot_error_rate_vs_sample_size(
                    test_type=test_type,
                    effect_size=effect_size,
                    thresholds=thresholds,
                    output_path=output_path
                )
                print(f"Generated: {output_path}")
            except Exception as e:
                print(f"Error generating plot for {test_type} at effect_size={effect_size}: {e}")

    # Generate comparison plot for a representative effect size
    if thresholds:
        comparison_path = os.path.join(VIS_DIR, "test_comparison_effect_0.5_annotated.png")
        try:
            plot_all_tests_comparison(
                test_types=test_types,
                effect_size=0.5,
                thresholds=thresholds,
                output_path=comparison_path
            )
            print(f"Generated: {comparison_path}")
        except Exception as e:
            print(f"Error generating comparison plot: {e}")

def main():
    """Main entry point for visualization generation."""
    print("Generating annotated plots...")
    generate_all_plots()
    print("Visualization generation complete.")

if __name__ == "__main__":
    main()