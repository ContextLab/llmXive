"""
Visualization module for continuous and binned accuracy plots.
"""
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_raw_annotated_data(data_path: Path) -> List[Dict[str, Any]]:
    """Load raw annotated data from CSV."""
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def calculate_mean_accuracy_by_hop(data: List[Dict[str, Any]]) -> Dict[int, Dict[str, int]]:
    """Calculate mean accuracy by hop count."""
    hop_stats = defaultdict(lambda: {"correct": 0, "total": 0})

    for record in data:
        chain_length = record.get("chain_length")
        if chain_length and chain_length != "unresolvable":
            hop = int(chain_length)
            hop_stats[hop]["total"] += 1
            if record.get("correctness", False):
                hop_stats[hop]["correct"] += 1

    return dict(hop_stats)

def generate_plot_data_csv(hop_stats: Dict[int, Dict[str, int]], output_path: Path):
    """Generate CSV for plot data."""
    ensure_dir(output_path.parent)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["hop", "accuracy", "count"])

        for hop in sorted(hop_stats.keys()):
            stats = hop_stats[hop]
            accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
            writer.writerow([hop, accuracy, stats["total"]])

def plot_continuous_accuracy(data: List[Dict[str, Any]], output_path: Path):
    """Generate continuous accuracy plot."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib not installed. Skipping plot generation.")
        return

    hop_stats = calculate_mean_accuracy_by_hop(data)

    hops = sorted(hop_stats.keys())
    accuracies = [hop_stats[h]["correct"] / hop_stats[h]["total"] if hop_stats[h]["total"] > 0 else 0.0 for h in hops]

    plt.figure(figsize=(10, 6))
    plt.scatter(hops, accuracies, label="Data points", alpha=0.6)

    # LOESS trend line (simplified)
    if len(hops) > 1:
        plt.plot(hops, accuracies, 'b-', alpha=0.5, label="Trend")

    plt.xlabel("Chain Length (Hops)")
    plt.ylabel("Accuracy")
    plt.title("Accuracy vs. Chain Length")
    plt.legend()
    plt.grid(True, alpha=0.3)

    ensure_dir(output_path.parent)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved continuous plot to {output_path}")

def plot_binned_accuracy(data: List[Dict[str, Any]], output_path: Path):
    """Generate binned accuracy plot."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib not installed. Skipping plot generation.")
        return

    bin_stats = defaultdict(lambda: {"correct": 0, "total": 0})

    for record in data:
        chain_length = record.get("chain_length")
        if chain_length and chain_length != "unresolvable":
            hop = int(chain_length)
            bin_name = str(hop) if hop <= 2 else "3+"
            bin_stats[bin_name]["total"] += 1
            if record.get("correctness", False):
                bin_stats[bin_name]["correct"] += 1

    bins = sorted(bin_stats.keys(), key=lambda x: int(x) if x != "3+" else 999)
    accuracies = [bin_stats[b]["correct"] / bin_stats[b]["total"] if bin_stats[b]["total"] > 0 else 0.0 for b in bins]

    plt.figure(figsize=(10, 6))
    plt.bar(bins, accuracies, color='skyblue', edgecolor='black')

    plt.xlabel("Chain Length Bin")
    plt.ylabel("Accuracy")
    plt.title("Accuracy by Chain Length Bin")
    plt.ylim(0, 1.0)
    plt.grid(True, alpha=0.3, axis='y')

    ensure_dir(output_path.parent)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved binned plot to {output_path}")

def main():
    """Main entry point for visualization."""
    project_root = get_project_root()
    processed_dir = get_path(project_root, "processed_data")

    data_path = processed_dir / "annotated_videokr.csv"
    raw_csv_path = processed_dir / "accuracy_vs_hop_raw.csv"
    raw_plot_path = processed_dir / "accuracy_vs_hop_raw.png"
    binned_plot_path = processed_dir / "accuracy_binned.png"

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)

    logger.info("Loading data...")
    data = load_raw_annotated_data(data_path)

    logger.info("Generating plot data CSV...")
    hop_stats = calculate_mean_accuracy_by_hop(data)
    generate_plot_data_csv(hop_stats, raw_csv_path)

    logger.info("Generating continuous plot...")
    plot_continuous_accuracy(data, raw_plot_path)

    logger.info("Generating binned plot...")
    plot_binned_accuracy(data, binned_plot_path)

if __name__ == "__main__":
    main()