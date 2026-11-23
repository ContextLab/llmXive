"""
Generate convergence plots from training logs.

This module creates visualizations of success rate vs steps for different
curriculum strategies.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger

logger = get_logger("generate_plots")

def load_convergence_results(file_path: Path) -> Dict[str, Any]:
    """Load convergence results from JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Convergence results file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_plot_data(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract plot-ready data from convergence results."""
    plot_data = []
    
    for strategy, data in results.get("strategies", {}).items():
        steps = data.get("steps", [])
        success_rates = data.get("success_rates", [])
        
        if steps and success_rates:
            plot_data.append({
                "strategy": strategy,
                "steps": steps,
                "success_rates": success_rates
            })
    
    return plot_data

def create_success_rate_vs_steps_plot(
    plot_data: List[Dict[str, Any]],
    output_path: Path,
    title: str = "Success Rate vs Steps"
) -> Path:
    """Create success rate vs steps plot."""
    plt.figure(figsize=(10, 6))
    
    for item in plot_data:
        strategy = item["strategy"]
        steps = item["steps"]
        success_rates = item["success_rates"]
        
        plt.plot(steps, success_rates, marker='o', label=strategy, linewidth=2)
    
    plt.xlabel("Steps", fontsize=12)
    plt.ylabel("Success Rate", fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1.05)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")
    return output_path

def generate_convergence_plot(
    results_file: Path,
    output_dir: Path,
    filename: str = "convergence_plot.png"
) -> Path:
    """Generate convergence plot from results file."""
    output_path = output_dir / filename
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = load_convergence_results(results_file)
    plot_data = extract_plot_data(results)
    
    if not plot_data:
        logger.warning("No plot data found in results")
        return output_path
    
    create_success_rate_vs_steps_plot(plot_data, output_path)
    return output_path

def main():
    """Main entry point for plot generation."""
    # Default paths
    results_file = PROJECT_ROOT / "data" / "processed" / "convergence_results.json"
    output_dir = PROJECT_ROOT / "data" / "processed"
    
    if len(sys.argv) > 1:
        results_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])
    
    logger.info(f"Generating plots from {results_file}")
    
    try:
        output_path = generate_convergence_plot(results_file, output_dir)
        logger.info(f"Plot generation complete: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Plot generation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
