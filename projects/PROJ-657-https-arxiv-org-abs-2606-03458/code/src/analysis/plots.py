"""
Plotting utilities for KVarN analysis.
Generates error accumulation divergence plots.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

def load_raw_mse_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load raw MSE data points from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file containing MSE data.
        
    Returns:
        List of dictionaries with keys: token_position, mse, quantizer_type.
    """
    data = []
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"MSE data file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                data.append(entry)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num}: {e}")
    return data

def aggregate_mse_by_position_and_quantizer(
    data: List[Dict[str, Any]]
) -> Dict[str, Dict[int, List[float]]]:
    """
    Aggregate MSE values by token position and quantizer type.
    
    Args:
        data: List of MSE data entries.
        
    Returns:
        Nested dict: {quantizer_type: {token_position: [mse_values]}}
    """
    aggregated: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    
    for entry in data:
        q_type = entry.get('quantizer_type', 'unknown')
        pos = entry.get('token_position')
        mse = entry.get('mse')
        
        if pos is None or mse is None:
            continue
            
        aggregated[q_type][pos].append(float(mse))
        
    return aggregated

def compute_cumulative_mse(
    aggregated: Dict[str, Dict[int, List[float]]]
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Compute cumulative MSE for each quantizer type.
    
    Args:
        aggregated: Aggregated MSE data by position and quantizer.
        
    Returns:
        Dict mapping quantizer type to (positions, cumulative_mse_array).
    """
    results = {}
    
    for q_type, position_data in aggregated.items():
        if not position_data:
            continue
            
        # Sort positions
        sorted_positions = sorted(position_data.keys())
        
        # Compute cumulative mean MSE for each position
        cumulative_values = []
        for pos in sorted_positions:
            mse_vals = position_data[pos]
            if mse_vals:
                cumulative_values.append(np.mean(mse_vals))
            else:
                cumulative_values.append(0.0)
                
        results[q_type] = (np.array(sorted_positions), np.array(cumulative_values))
        
    return results

def plot_error_accumulation_divergence(
    data_file: str,
    output_file: str,
    title: str = "Error Accumulation Divergence: KVarN vs Uniform",
    xlabel: str = "Token Position",
    ylabel: str = "Cumulative Mean MSE",
    figsize: Tuple[int, int] = (10, 6)
) -> None:
    """
    Generate a line plot of cumulative MSE vs token position for different quantizers.
    
    This visualizes the error accumulation hypothesis by showing how MSE grows
    as generation proceeds for KVarN vs Uniform quantization.
    
    Args:
        data_file: Path to the raw MSE JSONL file (data/processed/cumulative_mse_raw.jsonl).
        output_file: Path where the plot will be saved (data/processed/error_accumulation_plot.png).
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        figsize: Figure size (width, height) in inches.
    """
    # Load and process data
    raw_data = load_raw_mse_data(data_file)
    aggregated = aggregate_mse_by_position_and_quantizer(raw_data)
    cumulative_data = compute_cumulative_mse(aggregated)
    
    if not cumulative_data:
        raise ValueError("No valid data found to plot. Check input file format.")
    
    # Setup plot
    plt.figure(figsize=figsize)
    
    # Plot each quantizer type
    markers = ['o', 's', '^', 'd', 'v']
    colors = ['blue', 'red', 'green', 'purple', 'orange']
    
    for idx, (q_type, (positions, values)) in enumerate(cumulative_data.items()):
        marker = markers[idx % len(markers)]
        color = colors[idx % len(colors)]
        plt.plot(
            positions, 
            values, 
            label=q_type, 
            marker=marker, 
            color=color,
            linewidth=2,
            markersize=4
        )
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """
    Entry point for generating the error accumulation plot.
    Reads from data/processed/cumulative_mse_raw.jsonl and writes to data/processed/error_accumulation_plot.png.
    """
    # Define paths relative to project root (code/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    input_file = project_root / "data" / "processed" / "cumulative_mse_raw.jsonl"
    output_file = project_root / "data" / "processed" / "error_accumulation_plot.png"
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        print("Please ensure T014b has been completed to generate the raw MSE data.")
        return 1
        
    print(f"Generating error accumulation plot...")
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    
    try:
        plot_error_accumulation_divergence(
            data_file=str(input_file),
            output_file=str(output_file)
        )
        print(f"Success: Plot saved to {output_file}")
        return 0
    except Exception as e:
        print(f"Error generating plot: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
