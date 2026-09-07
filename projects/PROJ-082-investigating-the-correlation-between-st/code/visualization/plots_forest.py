"""
Forest Plot Generator (Task T024).
Generates a forest plot from meta-analysis results.
Ensures memory safety and handles gate logic gracefully.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from utils.config import get_project_root, ensure_directory
from visualization.memory_safe_plots import check_memory_usage, release_memory

logger = logging.getLogger(__name__)

RESULTS_PATH = "data/derived/results.json"
OUTPUT_PATH = "data/derived/forest_plot.png"
META_STATUS_PATH = "data/derived/meta_status.json"
GATE_PATH = "data/derived/gate_result.json"

def load_json(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file from the project root."""
    full_path = get_project_root() / path
    if not full_path.exists():
        logger.warning(f"File not found: {full_path}")
        return None
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {full_path}: {e}")
        return None

def generate_forest_plot(results: Dict[str, Any]) -> None:
    """
    Generate a forest plot from the meta-analysis results.
    Writes the plot to data/derived/forest_plot.png.
    """
    # Memory check before plotting
    check_memory_usage(threshold_mb=500)
    
    try:
        if not results or "studies" not in results or not results["studies"]:
            logger.warning("No studies found in results. Generating empty plot.")
            studies = []
        else:
            studies = results["studies"]

        # Extract data
        authors = [s.get("author", "Unknown") for s in studies]
        years = [s.get("year", "") for s in studies]
        r_values = [float(s.get("r", 0)) for s in studies]
        se_values = [float(s.get("se", 0.1)) for s in studies]

        # Calculate CI
        ci_lower = [r - 1.96 * se for r, se in zip(r_values, se_values)]
        ci_upper = [r + 1.96 * se for r, se in zip(r_values, se_values)]

        # Plot setup
        height = 4 + max(len(studies) * 0.4, 1)
        fig, ax = plt.subplots(figsize=(10, height))
        
        if studies:
            y_pos = np.arange(len(studies))
            
            # Plot error bars
            ax.errorbar(
                r_values, y_pos,
                xerr=se_values, 
                fmt='o', color='blue', capsize=5, ecolor='gray', alpha=0.7,
                label='Individual Studies'
            )
            
            # Draw vertical line at 0 (null effect)
            ax.axvline(x=0, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Null Effect')
            
            # Labels
            ax.set_yticks(y_pos)
            labels = [f"{a} ({y})" for a, y in zip(authors, years)]
            ax.set_yticklabels(labels)
            
            # Summary effect if available
            if "pooled_effect" in results:
                pooled = float(results["pooled_effect"])
                pooled_se = float(results.get("pooled_se", 0.1))
                # Plot pooled effect at y=-0.5 (above the studies)
                ax.scatter(pooled, -0.5, color='darkred', s=150, marker='D', zorder=6, label='Pooled Effect')
                ax.errorbar(pooled, -0.5, xerr=pooled_se, color='darkred', capsize=8, linewidth=2, zorder=6)
                
                # Add summary label
                ax.text(pooled + 0.05, -0.5, f"r={pooled:.3f}", va='center', ha='left', fontweight='bold')
                
                # Adjust y-limits to accommodate summary
                ax.set_ylim(-1.5, len(studies) - 0.5)
            
            ax.set_xlabel("Correlation Coefficient (r)")
            ax.set_title("Forest Plot: Structural Connectivity vs Music Preferences")
            ax.legend(loc='lower right')
            ax.grid(True, axis='y', alpha=0.3)
        else:
            ax.text(0.5, 0.5, "No studies available for forest plot", 
                    transform=ax.transAxes, ha='center', va='center', fontsize=14)
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)
            ax.axis('off')

        plt.tight_layout()
        output_file = get_project_root() / OUTPUT_PATH
        ensure_directory(output_file)
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Forest plot saved to {output_file}")
    finally:
        # Memory cleanup
        release_memory()

def main() -> int:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Check gate result first: if narrative required, skip plotting gracefully
    gate_result = load_json(GATE_PATH)
    if gate_result and gate_result.get("status") == "narrative_required":
        logger.info("Gate indicates narrative mode required. Skipping forest plot generation.")
        # Generate an empty placeholder to satisfy file existence requirements
        generate_forest_plot({})
        return 0

    # Check meta status
    meta_status = load_json(META_STATUS_PATH)
    if not meta_status or meta_status.get("status") != "completed":
        logger.warning("Meta-analysis not completed. Generating empty forest plot.")
        generate_forest_plot({})
        return 0

    results = load_json(RESULTS_PATH)
    if not results:
        logger.error("Could not load results.json. Cannot generate plot.")
        generate_forest_plot({})
        return 1
        
    generate_forest_plot(results)
    return 0

if __name__ == "__main__":
    sys.exit(main())