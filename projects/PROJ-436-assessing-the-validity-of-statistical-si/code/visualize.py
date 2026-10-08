import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_sensitivity_results(file_path: str) -> List[Dict[str, Any]]:
    """
    Load sensitivity analysis results from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing results.
        
    Returns:
        List of dictionaries containing result data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Handle if data is a dict with a 'results' key or a direct list
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        logger.warning("Unexpected JSON structure, attempting to parse as is.")
        return [data] if isinstance(data, dict) else data

def load_comparison_results(file_path: str) -> List[Dict[str, Any]]:
    """
    Load method comparison results (CC, MI, IPW) from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing comparison results.
        
    Returns:
        List of dictionaries containing result data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Comparison results file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        return [data] if isinstance(data, dict) else data

def identify_tipping_points(results: List[Dict[str, Any]], threshold: float = 0.055) -> List[Dict[str, Any]]:
    """
    Identify tipping points where error rate exceeds the threshold.
    
    Args:
        results: List of result dictionaries.
        threshold: The error rate threshold for tipping point detection.
        
    Returns:
        List of dictionaries containing tipping point information.
    """
    tipping_points = []
    
    # Group results by mechanism and method to find trends
    grouped = {}
    for res in results:
        key = (res.get('mechanism'), res.get('method'))
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(res)
    
    for (mechanism, method), items in grouped.items():
        # Sort by missing rate
        sorted_items = sorted(items, key=lambda x: x.get('missing_rate', 0))
        
        for item in sorted_items:
            if item.get('error_rate', 0) > threshold:
                tipping_points.append({
                    'mechanism': mechanism,
                    'method': method,
                    'missing_rate': item.get('missing_rate'),
                    'error_rate': item.get('error_rate'),
                    'threshold': threshold
                })
                break  # Only the first tipping point per mechanism/method
    
    return tipping_points

def plot_error_rate_curves(results: List[Dict[str, Any]], output_path: str, title: str = "Error Rate Curves"):
    """
    Plot error rate curves for different methods (CC, MI, IPW) against missingness rate.
    
    Args:
        results: List of result dictionaries.
        output_path: Path to save the plot.
        title: Title for the plot.
    """
    plt.figure(figsize=(12, 8))
    
    # Extract unique methods and mechanisms
    methods = set()
    mechanisms = set()
    for res in results:
        if res.get('method'):
            methods.add(res.get('method'))
        if res.get('mechanism'):
            mechanisms.add(res.get('mechanism'))
    
    if not methods:
        logger.error("No methods found in results.")
        return
    
    # Create a grid of plots if multiple mechanisms exist, otherwise one plot
    n_mechanisms = len(mechanisms) if mechanisms else 1
    if n_mechanisms > 1:
        fig, axes = plt.subplots(1, n_mechanisms, figsize=(5 * n_mechanisms, 5))
        if n_mechanisms == 1:
            axes = [axes]
    else:
        fig, axes = plt.subplots(1, 1, figsize=(12, 8))
        axes = [axes]
    
    colors = {'CC': 'red', 'MI': 'blue', 'IPW': 'green'}
    linestyles = {'CC': '--', 'MI': '-', 'IPW': '-.'}
    
    for idx, mechanism in enumerate(sorted(mechanisms) if mechanisms else ['All']):
        ax = axes[idx]
        
        for method in sorted(methods):
            # Filter results for this mechanism and method
            filtered = [
                r for r in results 
                if r.get('method') == method and (not mechanism or r.get('mechanism') == mechanism)
            ]
            
            if not filtered:
                continue
            
            # Sort by missing rate
            filtered = sorted(filtered, key=lambda x: x.get('missing_rate', 0))
            
            rates = [r.get('missing_rate', 0) for r in filtered]
            errors = [r.get('error_rate', 0) for r in filtered]
            
            color = colors.get(method, 'black')
            linestyle = linestyles.get(method, '-')
            
            ax.plot(rates, errors, marker='o', label=f'{method}', 
                    color=color, linestyle=linestyle, linewidth=2, markersize=6)
        
        # Add nominal level line
        ax.axhline(y=0.05, color='gray', linestyle=':', label='Nominal (0.05)', linewidth=1.5)
        
        # Add threshold line for tipping point
        tipping_threshold = 0.055
        ax.axhline(y=tipping_threshold, color='orange', linestyle='-.', 
                   label=f'Tipping Point ({tipping_threshold})', linewidth=1.5)
        
        ax.set_xlabel('Missingness Rate', fontsize=12)
        ax.set_ylabel('Empirical Type I Error Rate', fontsize=12)
        ax.set_title(f'Error Rate Curves - {mechanism}', fontsize=14)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, max(0.2, max([r.get('error_rate', 0) for r in results] + [0.2])))
    
    plt.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Plot saved to {output_path}")
    plt.close()

def plot_tipping_points(tipping_points: List[Dict[str, Any]], output_path: str):
    """
    Plot a bar chart of tipping points for different methods and mechanisms.
    
    Args:
        tipping_points: List of tipping point dictionaries.
        output_path: Path to save the plot.
    """
    if not tipping_points:
        logger.warning("No tipping points to plot.")
        return
    
    plt.figure(figsize=(12, 8))
    
    # Prepare data for plotting
    methods = sorted(list(set([tp['method'] for tp in tipping_points])))
    mechanisms = sorted(list(set([tp['mechanism'] for tp in tipping_points])))
    
    x = np.arange(len(mechanisms))
    width = 0.25
    
    for i, method in enumerate(methods):
        rates = [tp['missing_rate'] for tp in tipping_points if tp['method'] == method]
        # Pad with 0 if not all mechanisms are present for this method
        while len(rates) < len(mechanisms):
            rates.append(0)
        
        plt.bar(x + i * width, rates, width, label=method)
    
    plt.xlabel('Mechanism', fontsize=12)
    plt.ylabel('Missingness Rate at Tipping Point', fontsize=12)
    plt.title('Tipping Points by Mechanism and Method', fontsize=14)
    plt.xticks(x + width, mechanisms)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Tipping points plot saved to {output_path}")
    plt.close()

def plot_method_comparison(results: List[Dict[str, Any]], output_path: str, title: str = "Method Comparison"):
    """
    Plot a comparison of error rates for CC, MI, and IPW methods across missingness rates.
    This function specifically overlays CC, MI, and IPW curves as requested in T035.
    
    Args:
        results: List of result dictionaries containing method, missing_rate, and error_rate.
        output_path: Path to save the plot.
        title: Title for the plot.
    """
    plt.figure(figsize=(14, 8))
    
    # Define methods to plot
    target_methods = ['CC', 'MI', 'IPW']
    colors = {'CC': 'red', 'MI': 'blue', 'IPW': 'green'}
    markers = {'CC': 's', 'MI': 'o', 'IPW': '^'}
    linestyles = {'CC': '--', 'MI': '-', 'IPW': '-.'}
    
    # Group results by mechanism to create subplots or a single plot
    mechanisms = set(r.get('mechanism') for r in results if r.get('mechanism'))
    
    # If multiple mechanisms, create subplots; otherwise single plot
    if len(mechanisms) > 1:
        fig, axes = plt.subplots(1, len(mechanisms), figsize=(6 * len(mechanisms), 6))
        if len(mechanisms) == 1:
            axes = [axes]
    else:
        fig, axes = plt.subplots(1, 1, figsize=(14, 8))
        axes = [axes]
    
    for idx, mechanism in enumerate(sorted(mechanisms) if mechanisms else ['All']):
        ax = axes[idx]
        
        for method in target_methods:
            # Filter results
            filtered = [
                r for r in results 
                if r.get('method') == method and (not mechanism or r.get('mechanism') == mechanism)
            ]
            
            if not filtered:
                continue
            
            # Sort by missing rate
            filtered = sorted(filtered, key=lambda x: x.get('missing_rate', 0))
            
            rates = [r.get('missing_rate', 0) for r in filtered]
            errors = [r.get('error_rate', 0) for r in filtered]
            
            color = colors.get(method, 'black')
            marker = markers.get(method, 'o')
            linestyle = linestyles.get(method, '-')
            
            ax.plot(rates, errors, label=f'{method} ({mechanism})', 
                    color=color, marker=marker, linestyle=linestyle, 
                    linewidth=2, markersize=7)
        
        # Add reference lines
        ax.axhline(y=0.05, color='gray', linestyle=':', label='Nominal (0.05)', linewidth=1.5)
        ax.axhline(y=0.055, color='orange', linestyle='-.', label='Tipping (0.055)', linewidth=1.5)
        
        ax.set_xlabel('Missingness Rate', fontsize=12)
        ax.set_ylabel('Empirical Type I Error Rate', fontsize=12)
        ax.set_title(f'Method Comparison - {mechanism}', fontsize=14)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, max(0.2, max([r.get('error_rate', 0) for r in results] + [0.2])))
    
    plt.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Method comparison plot saved to {output_path}")
    plt.close()

def main():
    """
    Main function to execute visualization tasks.
    This function is designed to be run as a script to generate plots.
    """
    # Example usage (to be overridden by actual data paths in production)
    # In a real execution, these paths would be passed via arguments or config
    comparison_file = "data/processed/comparison_results.json"
    output_plot = "figures/method_comparison_overlay.png"
    
    if not Path(comparison_file).exists():
        logger.error(f"Comparison results file not found: {comparison_file}")
        logger.info("Skipping plot generation. Please ensure data/processed/comparison_results.json exists.")
        return
    
    try:
        results = load_comparison_results(comparison_file)
        logger.info(f"Loaded {len(results)} results for comparison.")
        
        plot_method_comparison(results, output_plot, "Type I Error Rates: CC vs MI vs IPW")
        
        # Also generate the general sensitivity curves if sensitivity results exist
        sensitivity_file = "data/processed/sensitivity_results.json"
        if Path(sensitivity_file).exists():
            sens_results = load_sensitivity_results(sensitivity_file)
            sens_plot = "figures/sensitivity_curves.png"
            plot_error_rate_curves(sens_results, sens_plot, "Sensitivity Analysis: Error Rate Curves")
            
            tips = identify_tipping_points(sens_results)
            if tips:
                tip_plot = "figures/tipping_points.png"
                plot_tipping_points(tips, tip_plot)
        
        logger.info("Visualization completed successfully.")
    except Exception as e:
        logger.error(f"Error during visualization: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()