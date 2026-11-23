"""
Funnel Plot Generator (Task T025).
Generates a funnel plot to assess publication bias.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from utils.config import get_project_root, ensure_directory

logger = logging.getLogger(__name__)

RESULTS_PATH = "data/derived/results.json"
OUTPUT_PATH = "data/derived/funnel_plot.png"
META_STATUS_PATH = "data/processed/meta_status.json"

def load_json(path: str) -> Optional[Dict[str, Any]]:
    full_path = get_project_root() / path
    if not full_path.exists():
        return None
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_funnel_plot(results: Dict[str, Any]) -> None:
    """
    Generate a funnel plot.
    X-axis: Effect Size (r)
    Y-axis: Standard Error (or Precision 1/SE)
    """
    if not results or "studies" not in results:
        logger.warning("No studies found. Generating empty funnel plot.")
        studies = []
    else:
        studies = results["studies"]

    r_values = [s.get("r", 0) for s in studies]
    se_values = [s.get("se", 0.1) for s in studies]

    fig, ax = plt.subplots(figsize=(8, 8))

    if studies:
        # Calculate pseudo 95% confidence limits
        # Using the pooled effect if available, otherwise 0
        pooled_effect = results.get("pooled_effect", 0)
        
        max_se = max(se_values) * 1.1 if se_values else 0.5
        
        # Generate lines for 95% CI
        se_range = np.linspace(0, max_se, 100)
        upper = pooled_effect + 1.96 * se_range
        lower = pooled_effect - 1.96 * se_range
        
        ax.fill_betweenx(se_range, lower, upper, color='gray', alpha=0.2, label='95% CI')
        ax.axhline(y=0, color='black', linewidth=1) # X-axis (SE=0)
        ax.axvline(x=pooled_effect, color='red', linestyle='--', linewidth=1, label='Pooled Effect')
        
        # Plot studies
        ax.scatter(r_values, se_values, color='blue', alpha=0.7, s=50, zorder=5)
        
        ax.set_xlabel("Effect Size (r)")
        ax.set_ylabel("Standard Error")
        ax.set_title("Funnel Plot")
        ax.legend(loc='upper right')
    else:
        ax.text(0.5, 0.5, "No studies available for funnel plot", 
                transform=ax.transAxes, ha='center', va='center', fontsize=14)
        ax.set_xlim(-1, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

    plt.tight_layout()
    output_file = get_project_root() / OUTPUT_PATH
    ensure_directory(output_file)
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Funnel plot saved to {output_file}")

def main() -> int:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    
    meta_status = load_json(META_STATUS_PATH)
    if not meta_status or meta_status.get("status") != "completed":
        logger.warning("Meta-analysis not completed. Skipping funnel plot.")
        generate_funnel_plot({})
        return 0

    results = load_json(RESULTS_PATH)
    generate_funnel_plot(results)
    return 0

if __name__ == "__main__":
    sys.exit(main())
