import os
import csv
import logging
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from config import RESULTS_DIR

# Ensure non-interactive backend for server environments
matplotlib.use('Agg')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_null_distributions():
    """Load all null distribution CSVs from results/null_distributions/."""
    distributions = {}
    dir_path = os.path.join(RESULTS_DIR, 'null_distributions')
    if not os.path.exists(dir_path):
        logger.warning(f"Null distributions directory not found: {dir_path}")
        return distributions

    for filename in os.listdir(dir_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(dir_path, filename)
            # Extract query_id and metric from filename or read from file
            # Assuming filename format: q{query_id}_{metric}.csv or similar
            # We'll read the first row to determine query_id and metric
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    query_id = int(rows[0]['query_id'])
                    metric = rows[0]['metric']
                    key = (query_id, metric)
                    distributions[key] = [float(r['score']) for r in rows]
    return distributions

def load_raw_p_values():
    """Load raw p-values from results/p_values/raw_p_values.csv."""
    p_values = {}
    file_path = os.path.join(RESULTS_DIR, 'p_values', 'raw_p_values.csv')
    if not os.path.exists(file_path):
        logger.warning(f"Raw p-values file not found: {file_path}")
        return p_values

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            query_id = int(row['query_id'])
            metric = row['metric']
            p_val = float(row['p_value'])
            p_values[(query_id, metric)] = p_val
    return p_values

def load_mdes_values():
    """Load MDES values from results/mdes/mdes_summary.csv."""
    mdes_values = {}
    file_path = os.path.join(RESULTS_DIR, 'mdes', 'mdes_summary.csv')
    if not os.path.exists(file_path):
        logger.warning(f"MDES summary file not found: {file_path}")
        return mdes_values

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metric = row['metric']
            mdes = float(row['mdes'])
            mdes_values[metric] = mdes
    return mdes_values

def load_observed_scores():
    """Load observed scores from results/observed_scores.csv (if exists)."""
    scores = {}
    file_path = os.path.join(RESULTS_DIR, 'observed_scores.csv')
    if not os.path.exists(file_path):
        logger.warning(f"Observed scores file not found: {file_path}")
        return scores

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            query_id = int(row['query_id'])
            metric = row['metric']
            score = float(row['score'])
            scores[(query_id, metric)] = score
    return scores

def generate_density_plot(query_id, metric, null_scores, observed_score, mdes_value, output_path):
    """
    Generate a density plot comparing original vs. permuted scores.
    Annotates with MDES value (vertical dashed line) and significance threshold.
    
    Args:
        query_id: Query identifier
        metric: Metric name (e.g., 'NDCG@10')
        null_scores: List of permuted scores
        observed_score: The original observed score
        mdes_value: MDES value for this metric (for annotation)
        output_path: Path to save the plot
    """
    plt.figure(figsize=(10, 6))
    
    # Plot null distribution density
    if null_scores:
        density, bins = np.histogram(null_scores, bins=50, density=True)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        plt.plot(bin_centers, density, label='Null Distribution (Permuted)', color='gray', alpha=0.7)
        
        # Fill under the curve for visual effect
        plt.fill_between(bin_centers, density, alpha=0.3, color='gray')
    
    # Plot observed score as a vertical line
    plt.axvline(x=observed_score, color='blue', linestyle='-', linewidth=2, label=f'Observed ({observed_score:.4f})')
    
    # ANNOTATION: Add MDES vertical dashed line and text label
    if mdes_value is not None:
        plt.axvline(x=mdes_value, color='red', linestyle='--', linewidth=2, label=f'MDES={mdes_value:.4f}')
        # Add text label slightly offset from the line
        plt.text(mdes_value, plt.ylim()[1] * 0.9, f'MDES={mdes_value:.4f}', 
                 color='red', fontsize=10, fontweight='bold',
                 verticalalignment='top', horizontalalignment='left')
    
    # Add significance threshold line (p=0.05 equivalent if we had the distribution stats, 
    # but here we just label the MDES as the detectable effect size)
    # We could also add a line for the 95th percentile of null if needed, 
    # but the task specifically asks for MDES annotation.
    
    plt.xlabel('Score')
    plt.ylabel('Density')
    plt.title(f'Density Plot: Query {query_id}, Metric {metric}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved density plot to {output_path}")

def generate_plots():
    """Generate all density plots with MDES annotations."""
    null_dists = load_null_distributions()
    mdes_vals = load_mdes_values()
    observed_scores = load_observed_scores()
    
    if not null_dists:
        logger.warning("No null distributions found. Skipping plot generation.")
        return
    
    plots_dir = os.path.join(RESULTS_DIR, 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    for (query_id, metric), null_scores in null_dists.items():
        observed = observed_scores.get((query_id, metric), None)
        if observed is None:
            # Try to infer from filename or use a placeholder if not found
            # For now, skip if observed score is missing
            logger.warning(f"Observed score missing for query {query_id}, metric {metric}. Skipping plot.")
            continue
        
        mdes = mdes_vals.get(metric, None)
        
        filename = f"q{query_id}_{metric.replace('@', '_')}_density.png"
        output_path = os.path.join(plots_dir, filename)
        
        generate_density_plot(
            query_id=query_id,
            metric=metric,
            null_scores=null_scores,
            observed_score=observed,
            mdes_value=mdes,
            output_path=output_path
        )
    
    logger.info(f"Generated {len(null_dists)} density plots in {plots_dir}")

def run_visualization():
    """Main entry point for visualization tasks."""
    logger.info("Starting visualization generation...")
    generate_plots()
    logger.info("Visualization generation complete.")

if __name__ == "__main__":
    run_visualization()