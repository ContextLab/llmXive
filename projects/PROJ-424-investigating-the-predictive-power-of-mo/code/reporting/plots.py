import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PlotConfig:
    style: str = "seaborn-v0_8-whitegrid"
    font_size: int = 12
    dpi: int = 300
    color_map: str = "viridis"

def load_diffusion_results(results: List[Dict]) -> List[Dict]:
    """Ensure results are in the correct format."""
    return results

def calculate_uncertainty_bands(results: List[Dict]) -> Dict[str, List[float]]:
    """Calculate uncertainty bands (placeholder for bootstrap CI)."""
    # Placeholder: return empty bands or simple std dev if multiple runs existed
    return {"upper": [], "lower": []}

def generate_timescale_accuracy_plot(results: List[Dict], nist_refs: Dict[str, float], output_dir: str):
    """Generate the timescale-accuracy curve (MAE vs Duration)."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "timescale_accuracy.png"

    plt.figure(figsize=(10, 6))
    
    # Group by solvent
    solvents = set(r["solvent"] for r in results)
    
    for solvent in solvents:
        subset = [r for r in results if r["solvent"] == solvent]
        subset.sort(key=lambda x: x["timescale_ns"])
        
        times = [r["timescale_ns"] for r in subset]
        maes = []
        for r in subset:
            exp = nist_refs.get(solvent, 0)
            sim = r.get("diffusion_coefficient", 0)
            if exp > 0:
                maes.append(abs(sim - exp))
            else:
                maes.append(0)
        
        plt.plot(times, maes, marker='o', label=solvent.capitalize())

    plt.xlabel("Simulation Duration (ns)")
    plt.ylabel("Mean Absolute Error (m²/s)")
    plt.title("Timescale-Accuracy Curves: MAE vs. Simulation Duration")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved timescale accuracy plot to {output_path}")

def generate_multi_solvent_comparison(results: List[Dict], nist_refs: Dict[str, float], output_dir: str):
    """Generate a comparison plot for all solvents."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "solvent_comparison.png"

    plt.figure(figsize=(10, 6))

    # Prepare data for bar chart or line chart
    solvents = sorted(list(set(r["solvent"] for r in results)))
    # Use the longest timescale for comparison if available, else last
    comparison_data = {}
    for solvent in solvents:
        subset = [r for r in results if r["solvent"] == solvent]
        if subset:
            # Take the one with max timescale
            best = max(subset, key=lambda x: x["timescale_ns"])
            comparison_data[solvent] = best.get("diffusion_coefficient", 0)

    x = np.arange(len(solvents))
    width = 0.35

    exp_vals = [nist_refs.get(s, 0) for s in solvents]
    sim_vals = [comparison_data.get(s, 0) for s in solvents]

    plt.bar(x - width/2, exp_vals, width, label='Experimental (NIST)', alpha=0.8)
    plt.bar(x + width/2, sim_vals, width, label='Simulated (MD)', alpha=0.8)

    plt.xlabel("Solvent")
    plt.ylabel("Diffusion Coefficient (m²/s)")
    plt.title("Experimental vs. Simulated Diffusion Coefficients")
    plt.xticks(x, [s.capitalize() for s in solvents])
    plt.legend()
    plt.yscale('log') # Log scale often better for diffusion coeffs
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved solvent comparison plot to {output_path}")

def main():
    """Test plotting function."""
    # Mock data
    results = [
        {"solvent": "water", "timescale_ns": 1.0, "diffusion_coefficient": 2.2e-9},
        {"solvent": "water", "timescale_ns": 10.0, "diffusion_coefficient": 2.35e-9},
        {"solvent": "ethanol", "timescale_ns": 1.0, "diffusion_coefficient": 1.1e-9},
    ]
    refs = {"water": 2.30e-9, "ethanol": 1.24e-9}
    generate_timescale_accuracy_plot(results, refs, "figures")
    generate_multi_solvent_comparison(results, refs, "figures")

if __name__ == "__main__":
    main()
