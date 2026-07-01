"""
Task T039: Regenerate Figures from Real Execution Logs.

This script reads the parsed SDAR training results from data/sdar_results.csv
and generates visualizations of the training dynamics, specifically:
1. Gate Loss vs KL Divergence (scatter plot)
2. RL Loss over Steps (line plot)

It relies on the real data produced by T038b (parse_logs.py).
"""
import os
import csv
import matplotlib
# Use non-interactive backend for headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants based on project structure
DATA_DIR = Path("data")
FIGURES_DIR = Path("figures")
RESULTS_CSV = DATA_DIR / "sdar_results.csv"
GATE_KL_PNG = FIGURES_DIR / "gate_vs_kl.png"
RL_LOSS_PNG = FIGURES_DIR / "rl_loss_over_steps.png"

# Metrics expected from parse_logs.py (T038b)
METRICS = {
    "step": "step",
    "sdar_gate_loss": "SDAR Gate Loss",
    "rl_loss": "RL Loss",
    "kl_divergence": "kl_divergence",
    "gate_activation_rate": "gate_activation_rate"
}

def load_results(csv_path: Path) -> List[Dict[str, Any]]:
    """Load parsed results from CSV into a list of dictionaries."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Required data file not found: {csv_path}. "
                                "Ensure T038b (parse_logs.py) has been executed.")
    
    data = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats where appropriate
            parsed_row = {}
            for key, value in row.items():
                try:
                    parsed_row[key] = float(value)
                except (ValueError, TypeError):
                    parsed_row[key] = value
            data.append(parsed_row)
    return data

def ensure_directories():
    """Create output directories if they don't exist."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def plot_gate_vs_kl(data: List[Dict[str, Any]], output_path: Path):
    """
    Generate a scatter plot of SDAR Gate Loss vs KL Divergence.
    This visualizes the trade-off or correlation between the gating mechanism
    and the distillation penalty.
    """
    if not data:
        print("Warning: No data points to plot for gate_vs_kl.")
        return

    steps = [d['step'] for d in data]
    gate_losses = [d['SDAR Gate Loss'] for d in data]
    kl_divs = [d['kl_divergence'] for d in data]

    plt.figure(figsize=(10, 6))
    # Use step index as a third dimension (color) if desired, or just scatter
    scatter = plt.scatter(gate_losses, kl_divs, c=steps, cmap='viridis', 
                          edgecolors='k', s=100, alpha=0.7)
    
    plt.xlabel('SDAR Gate Loss', fontsize=12)
    plt.ylabel('KL Divergence', fontsize=12)
    plt.title('SDAR: Gate Loss vs KL Divergence (Training Steps)', fontsize=14)
    
    # Add a colorbar to indicate step progression
    cbar = plt.colorbar(scatter)
    cbar.set_label('Training Step', fontsize=10)
    
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Generated: {output_path}")

def plot_rl_loss_over_steps(data: List[Dict[str, Any]], output_path: Path):
    """
    Generate a line plot of RL Loss over training steps.
    """
    if not data:
        print("Warning: No data points to plot for rl_loss_over_steps.")
        return

    steps = [d['step'] for d in data]
    rl_losses = [d['RL Loss'] for d in data]

    plt.figure(figsize=(10, 6))
    plt.plot(steps, rl_losses, marker='o', linestyle='-', color='tab:blue', label='RL Loss')
    
    plt.xlabel('Training Step', fontsize=12)
    plt.ylabel('RL Loss', fontsize=12)
    plt.title('SDAR: RL Loss Over Training Steps', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Generated: {output_path}")

def main():
    """Main entry point for figure generation."""
    print(f"Task T039: Regenerating figures from {RESULTS_CSV}...")
    
    try:
        ensure_directories()
        data = load_results(RESULTS_CSV)
        
        if len(data) == 0:
            print("Error: CSV file is empty. Cannot generate figures.")
            return 1

        # Generate required plots
        plot_gate_vs_kl(data, GATE_KL_PNG)
        plot_rl_loss_over_steps(data, RL_LOSS_PNG)
        
        print("Figure generation completed successfully.")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error during figure generation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())