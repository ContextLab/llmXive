"""
Correlation Summary Plot Generator (Task T026).
Visualizes the distribution of correlation coefficients by tract.
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
EXTRACTED_PATH = "data/processed/extracted_studies.csv"
OUTPUT_PATH = "data/derived/correlation_summary.png"
META_STATUS_PATH = "data/processed/meta_status.json"

def load_json(path: str) -> Optional[Dict[str, Any]]:
    full_path = get_project_root() / path
    if not full_path.exists():
        return None
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_csv(path: str) -> List[Dict[str, Any]]:
    import csv
    full_path = get_project_root() / path
    if not full_path.exists():
        return []
    with open(full_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def generate_correlation_summary(results: Dict[str, Any], studies: List[Dict[str, Any]]) -> None:
    """
    Generate a summary plot of correlations by tract.
    """
    # Group by tract
    tract_data = {}
    for study in studies:
        tract = study.get("tract", "Unknown")
        r_val = study.get("r")
        if r_val is not None:
            try:
                r_val = float(r_val)
                if tract not in tract_data:
                    tract_data[tract] = []
                tract_data[tract].append(r_val)
            except (ValueError, TypeError):
                continue

    fig, ax = plt.subplots(figsize=(10, 6))

    if tract_data:
        tracts = list(tract_data.keys())
        means = []
        errors = []
        
        for tract in tracts:
            vals = tract_data[tract]
            means.append(np.mean(vals))
            errors.append(np.std(vals) / np.sqrt(len(vals)) if len(vals) > 1 else 0.1)
        
        y_pos = np.arange(len(tracts))
        ax.barh(y_pos, means, xerr=errors, align='center', alpha=0.7, ecolor='black', capsize=3)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(tracts)
        ax.set_xlabel("Mean Correlation Coefficient (r)")
        ax.set_title("Correlation Summary by Brain Tract")
        ax.axvline(x=0, color='red', linestyle='--', linewidth=1)
        
        # Add count labels
        for i, (tract, vals) in enumerate(tract_data.items()):
            ax.text(max(means) + 0.05, i, f"n={len(vals)}", va='center', fontsize=9)
    else:
        ax.text(0.5, 0.5, "No valid correlation data found", 
                transform=ax.transAxes, ha='center', va='center', fontsize=14)
        ax.set_xlim(-1, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

    plt.tight_layout()
    output_file = get_project_root() / OUTPUT_PATH
    ensure_directory(output_file)
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Correlation summary plot saved to {output_file}")

def main() -> int:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    
    meta_status = load_json(META_STATUS_PATH)
    if not meta_status or meta_status.get("status") != "completed":
        logger.warning("Meta-analysis not completed. Skipping correlation plot.")
        generate_correlation_summary({}, [])
        return 0

    results = load_json(RESULTS_PATH)
    studies = load_csv(EXTRACTED_PATH)
    generate_correlation_summary(results, studies)
    return 0

if __name__ == "__main__":
    sys.exit(main())