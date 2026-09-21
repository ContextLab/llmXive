import os
import csv
import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for serverless/CPU environments
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Any

from utils.stats import aggregate_benchmark_results

logger = logging.getLogger(__name__)

def load_benchmark_data(csv_path: str) -> List[Dict[str, Any]]:
    """
    Loads benchmark data from the generated CSV file.
    Expects columns: view_count, latency, chamfer_distance, psnr, baseline_latency
    """
    data = []
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Benchmark CSV not found at {csv_path}. "
                                "Ensure T033 (generate_benchmark_csv) has run successfully.")
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data.append({
                    'view_count': int(row['view_count']),
                    'latency': float(row['latency']),
                    'chamfer_distance': float(row['chamfer_distance']),
                    'psnr': float(row['psnr']),
                    'baseline_latency': float(row.get('baseline_latency', 'nan')) if row.get('baseline_latency') and row['baseline_latency'] != 'nan' else None
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed row in {csv_path}: {row} due to {e}")
                continue
    
    if not data:
        raise ValueError(f"No valid data rows found in {csv_path}")
        
    return data

def plot_tradeoff(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generates a trade-off curve plot: Latency (x-axis) vs Chamfer Distance (y-axis).
    Different view counts are represented by different markers/colors.
    Saves the plot to output_path.
    """
    # Prepare data for plotting
    # We group by view_count to create distinct series
    view_counts = sorted(list(set(d['view_count'] for d in data)))
    
    if not view_counts:
        raise ValueError("No view counts found in data to plot.")

    # Setup plot
    plt.figure(figsize=(10, 7))
    
    # Define a color palette
    colors = plt.cm.viridis_r(np.linspace(0, 1, len(view_counts)))
    
    for i, vc in enumerate(view_counts):
        subset = [d for d in data if d['view_count'] == vc]
        if not subset:
            continue
        
        latencies = [d['latency'] for d in subset]
        chamfers = [d['chamfer_distance'] for d in subset]
        
        # Sort by latency to connect points logically if desired, 
        # but scatter is often better for variability visualization.
        # We will use scatter with a trend line or just scatter to show distribution.
        plt.scatter(
            latencies, 
            chamfers, 
            label=f'{vc} Views', 
            color=colors[i], 
            s=60, 
            alpha=0.7, 
            edgecolors='black', 
            linewidth=0.5
        )
        
        # Calculate mean latency and mean chamfer for this view count to show the "center"
        mean_lat = sum(latencies) / len(latencies)
        mean_cham = sum(chamfers) / len(chamfers)
        plt.plot(mean_lat, mean_cham, marker='X', markersize=12, color=colors[i], markeredgecolor='black', markeredgewidth=1.5)

    plt.xlabel('Latency (seconds)', fontsize=12)
    plt.ylabel('Chamfer Distance (lower is better)', fontsize=12)
    plt.title('Latency vs. Geometric Fidelity (Chamfer Distance) by View Count', fontsize=14)
    plt.legend(title='Input Views', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Ensure low chamfer is at the top (better performance) or standard?
    # Standard is lower is better. Usually we want to see the trade-off:
    # Lower latency (faster) often means higher error (worse).
    # So we expect a curve going from bottom-right (slow, accurate) to top-left (fast, inaccurate)?
    # Actually, fewer views -> faster (lower latency) but worse (higher chamfer).
    # So 2-views should be bottom-left (fast) but high Y (bad). 
    # 5-views should be top-right (slow) but low Y (good).
    # Wait: Fewer views = faster inference? Yes. Fewer views = worse reconstruction? Yes.
    # So:
    # Low Latency (Fast) -> High Chamfer (Bad)
    # High Latency (Slow) -> Low Chamfer (Good)
    # The curve should slope downwards from left to right?
    # Left (Fast) = High Y. Right (Slow) = Low Y.
    # Yes, a negative slope is expected.
    
    # Invert Y-axis? No, standard is lower is better. We keep standard axis.
    # Just ensure the legend and labels are clear.

    plt.tight_layout()
    
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Trade-off plot saved to {output_path}")

def main():
    """
    Entry point to generate the benchmark trade-off plot.
    Reads from data/processed/benchmark_tradeoff.csv and writes to data/processed/benchmark_tradeoff_plot.png
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    project_root = Path(__file__).resolve().parent.parent.parent
    csv_path = project_root / "data" / "processed" / "benchmark_tradeoff.csv"
    output_path = project_root / "data" / "processed" / "benchmark_tradeoff_plot.png"
    
    logger.info(f"Loading benchmark data from {csv_path}")
    try:
        data = load_benchmark_data(str(csv_path))
    except FileNotFoundError as e:
        logger.error(str(e))
        raise SystemExit(1)
    
    logger.info(f"Loaded {len(data)} data points. Generating plot...")
    
    try:
        plot_tradeoff(data, str(output_path))
        logger.info("Trade-off plot generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate plot: {e}")
        raise

if __name__ == "__main__":
    main()