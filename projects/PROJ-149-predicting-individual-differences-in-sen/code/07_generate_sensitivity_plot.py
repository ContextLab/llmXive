import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_path, get_seed

def load_sensitivity_results():
    """Load results from T028 sensitivity analysis."""
    input_path = get_path("sensitivity_results.json")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        return json.load(f)

def find_critical_threshold(results):
    """
    Identify the exact p-value threshold where results transition from 
    significant to non-significant.
    
    Returns:
        dict: Contains critical_threshold, significant_below, non_significant_above
    """
    # Sort by p-value threshold
    sorted_results = sorted(results, key=lambda x: x['threshold'])
    
    significant_below = None
    non_significant_above = None
    critical_threshold = None
    
    for i, row in enumerate(sorted_results):
        is_sig = row['is_significant']
        threshold = row['threshold']
        
        if is_sig:
            significant_below = threshold
        else:
            non_significant_above = threshold
            # If we found a significant result before this, this is the transition
            if significant_below is not None:
                critical_threshold = threshold
                break
    
    # If all were significant, critical is max threshold
    if critical_threshold is None and significant_below is not None:
        critical_threshold = sorted_results[-1]['threshold']
        
    return {
        'critical_threshold': critical_threshold,
        'significant_below': significant_below,
        'non_significant_above': non_significant_above
    }

def generate_sensitivity_plot(results, output_path):
    """
    Generate a plot showing model R² and significance status across 
    p-value thresholds.
    """
    df = pd.DataFrame(results)
    
    # Ensure threshold is numeric
    df['threshold'] = pd.to_numeric(df['threshold'], errors='coerce')
    df = df.dropna(subset=['threshold']).sort_values('threshold')
    
    if df.empty:
        raise ValueError("No valid sensitivity results to plot")
    
    plt.figure(figsize=(10, 6))
    
    # Plot R² values
    plt.subplot(1, 2, 1)
    sns.lineplot(data=df, x='threshold', y='r_squared', marker='o', linewidth=2)
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.title('Model R² vs P-value Threshold')
    plt.xlabel('P-value Threshold')
    plt.ylabel('R²')
    plt.grid(True, alpha=0.3)
    
    # Plot significance status
    plt.subplot(1, 2, 2)
    df['is_significant_numeric'] = df['is_significant'].astype(int)
    sns.scatterplot(data=df, x='threshold', y='is_significant_numeric', 
                   hue='is_significant', s=100, palette={True: 'green', False: 'red'})
    plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    plt.title('Significance Status vs P-value Threshold')
    plt.xlabel('P-value Threshold')
    plt.ylabel('Significant (1) / Not Significant (0)')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.legend(['Significant', 'Not Significant'])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Sensitivity plot saved to: {output_path}")

def generate_report(critical_info, output_path):
    """Generate a text report summarizing the sensitivity analysis findings."""
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        "## Overview",
        "This report summarizes the sensitivity of model results to varying p-value thresholds.",
        "",
        "## Critical Threshold Analysis",
        "",
    ]
    
    if critical_info['critical_threshold']:
        report_lines.append(f"- **Critical Threshold**: {critical_info['critical_threshold']:.4f}")
        report_lines.append(f"- Results are significant for thresholds **above** this value.")
        report_lines.append(f"- Results become non-significant for thresholds **below** this value.")
    else:
        report_lines.append("- **No clear transition point found** in the tested range.")
    
    report_lines.extend([
        "",
        "## Detailed Findings",
        "",
        f"- Highest threshold tested: {critical_info['non_significant_above']} (if applicable)",
        f"- Lowest threshold tested: {critical_info['significant_below']} (if applicable)",
        "",
        "## Conclusion",
        "The model's significance is sensitive to p-value threshold selection. "
        "Researchers should report results at multiple thresholds or use the identified "
        "critical threshold as a reference point for interpretation.",
        ""
    ])
    
    report_content = "\n".join(report_lines)
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    print(f"Sensitivity report saved to: {output_path}")
    return report_content

def main():
    parser = argparse.ArgumentParser(description="Generate sensitivity plot and report")
    parser.add_argument('--output-dir', type=str, default=None, 
                      help='Output directory for plot and report')
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    seed = get_seed()
    np.random.seed(seed)
    
    try:
        # Load sensitivity results from T028
        results = load_sensitivity_results()
        
        if not results:
            raise ValueError("Sensitivity results are empty")
        
        # Find critical threshold
        critical_info = find_critical_threshold(results)
        
        # Determine output paths
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            output_dir = get_path("processed_dir")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        plot_path = output_dir / "sensitivity_plot.png"
        report_path = output_dir / "sensitivity_threshold_report.md"
        
        # Generate plot
        generate_sensitivity_plot(results, plot_path)
        
        # Generate report
        generate_report(critical_info, report_path)
        
        # Also update the main sensitivity results file with critical info
        results['critical_threshold_info'] = critical_info
        results_path = get_path("sensitivity_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("T029 completed successfully.")
        print(f"  - Plot: {plot_path}")
        print(f"  - Report: {report_path}")
        print(f"  - Critical threshold: {critical_info['critical_threshold']}")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Ensure T028 (sensitivity_analysis.py) has completed successfully.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()