import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from config import get_processed_dir, get_figures_dir

logger = logging.getLogger(__name__)

def load_processed_data(filename: str = "responses.json") -> List[Dict[str, Any]]:
    """Load processed response data from JSON."""
    data_path = get_processed_dir() / filename
    if not data_path.exists():
        logger.warning(f"Data file not found: {data_path}")
        return []
    with open(data_path, 'r') as f:
        return json.load(f)

def calculate_false_memory_rates(data: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate false memory rates per condition."""
    rates = {}
    for item in data:
        cond = item.get("condition", "unknown")
        if cond not in rates:
            rates[cond] = {"true": 0, "false": 0, "total": 0}
        if item.get("is_lure", False):
            rates[cond]["false"] += 1
        rates[cond]["total"] += 1
    
    result = {}
    for cond, counts in rates.items():
        if counts["total"] > 0:
            result[cond] = counts["false"] / counts["total"]
        else:
            result[cond] = 0.0
    return result

def plot_false_memory_rates(rates: Dict[str, float], output_path: Optional[Path] = None):
    """Plot false memory rates with confidence intervals."""
    if output_path is None:
        output_path = get_figures_dir() / "false_memory_rates.png"
    
    plt.figure(figsize=(10, 6))
    conditions = list(rates.keys())
    values = [rates[c] for c in conditions]
    plt.bar(conditions, values, alpha=0.7)
    plt.ylabel("False Memory Rate")
    plt.title("False Memory Rates by Condition")
    plt.ylim(0, 1)
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Visualization saved to {output_path}")

def generate_visualization(data: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """Generate full visualization from data."""
    rates = calculate_false_memory_rates(data)
    plot_false_memory_rates(rates, output_path)

def main():
    """Main entry point for visualization."""
    data = load_processed_data()
    if not data:
        logger.warning("No data to visualize. Run analysis first.")
        return
    generate_visualization(data)
    print("Visualization generated.")

if __name__ == "__main__":
    main()