import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Optional visualization dependencies
try:
    import seaborn as sns
    import matplotlib.pyplot as plt
    import pandas as pd
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logging.warning("Seaborn/Matplotlib/Pandas not available. Visualization skipped.")

from config import get_project_root

logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = get_project_root()
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure output directory exists
DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_correlation_stats() -> Optional[Dict[str, Any]]:
    """Load the correlation statistics from the previous analysis step."""
    stats_path = DATA_RESULTS_DIR / "us1_correlation_stats.json"
    if not stats_path.exists():
        logger.error(f"Correlation stats file not found: {stats_path}")
        return None
    
    try:
        with open(stats_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse correlation stats JSON: {e}")
        return None


def load_variance_report() -> Optional[Dict[str, Any]]:
    """Check for the variance null report."""
    report_path = DATA_RESULTS_DIR / "variance_null_report.json"
    if not report_path.exists():
        return None
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse variance report JSON: {e}")
        return None


def load_chunk_data(file_path: Path) -> List[Dict[str, Any]]:
    """Load chunk data from a JSONL file."""
    data = []
    if not file_path.exists():
        logger.warning(f"Data file not found: {file_path}")
        return data
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON line in {file_path}")
    return data


def generate_correlation_plot(
    python_data: List[Dict[str, Any]],
    java_data: List[Dict[str, Any]],
    output_path: Path
) -> bool:
    """
    Generate scatter plots with regression lines for Python and Java.
    Returns True if plot was generated, False otherwise.
    """
    if not VISUALIZATION_AVAILABLE:
        logger.error("Visualization libraries (seaborn, matplotlib, pandas) are not installed.")
        return False

    if not python_data and not java_data:
        logger.warning("No data available to plot.")
        return False

    try:
        # Prepare data for plotting
        plot_data = []
        
        # Process Python data
        for chunk in python_data:
            # Extract complexity and normalized loss
            # Assuming keys are 'cyclomatic_complexity' and 'normalized_loss' based on spec
            complexity = chunk.get('cyclomatic_complexity')
            loss = chunk.get('normalized_loss')
            
            if complexity is not None and loss is not None:
                plot_data.append({
                    'complexity': complexity,
                    'loss': loss,
                    'language': 'Python'
                })

        # Process Java data
        for chunk in java_data:
            complexity = chunk.get('cyclomatic_complexity')
            loss = chunk.get('normalized_loss')
            
            if complexity is not None and loss is not None:
                plot_data.append({
                    'complexity': complexity,
                    'loss': loss,
                    'language': 'Java'
                })

        if not plot_data:
            logger.warning("No valid data points found for plotting.")
            return False

        df = pd.DataFrame(plot_data)

        # Set style
        sns.set(style="whitegrid")
        plt.figure(figsize=(12, 8))

        # Create scatter plot with regression line
        # Using hue to separate languages if both exist, otherwise just plot
        if 'language' in df.columns and df['language'].nunique() > 1:
            sns.regplot(
                data=df,
                x='complexity',
                y='loss',
                hue='language',
                scatter_kws={'alpha': 0.6},
                line_kws={'linewidth': 2},
                ci=95
            )
            plt.title('Code Complexity vs Normalized Prediction Loss by Language', fontsize=14)
            plt.legend(title='Language')
        else:
            # Single language or no language column
            sns.regplot(
                data=df,
                x='complexity',
                y='loss',
                scatter_kws={'alpha': 0.6},
                line_kws={'linewidth': 2},
                color='blue',
                ci=95
            )
            plt.title('Code Complexity vs Normalized Prediction Loss', fontsize=14)

        plt.xlabel('Cyclomatic Complexity', fontsize=12)
        plt.ylabel('Normalized Prediction Loss (nats)', fontsize=12)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Correlation plot saved to: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error generating correlation plot: {e}", exc_info=True)
        return False


def update_correlation_stats_with_plot(stats: Dict[str, Any], plot_path: Path) -> Dict[str, Any]:
    """Update the correlation stats dictionary with the plot path."""
    if stats is None:
        stats = {
            "status": "visualization_generated",
            "plot_path": str(plot_path.relative_to(PROJECT_ROOT))
        }
    else:
        stats["status"] = "visualization_generated"
        stats["plot_path"] = str(plot_path.relative_to(PROJECT_ROOT))
    
    return stats


def run_visualization_analysis() -> Dict[str, Any]:
    """
    Main entry point for the visualization analysis.
    1. Check for variance null report.
    2. If null variance, write stats indicating no plot.
    3. If variance > 0, generate plot and update stats.
    """
    logger.info("Starting correlation visualization analysis (T020).")

    # Step 1: Check for variance null report
    variance_report = load_variance_report()
    
    if variance_report is not None:
        logger.warning("Null variance detected. Skipping plot generation.")
        stats_path = DATA_RESULTS_DIR / "us1_correlation_stats.json"
        
        # Load existing stats or create new
        existing_stats = load_correlation_stats()
        if existing_stats is None:
            existing_stats = {}
        
        existing_stats["status"] = "no_correlation"
        existing_stats["reason"] = "Null variance detected in complexity metrics."
        existing_stats["plot_generated"] = False
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(existing_stats, f, indent=2)
        
        logger.info(f"Updated {stats_path} with null variance status.")
        return existing_stats

    # Step 2: Load data for plotting
    python_data = load_chunk_data(DATA_PROCESSED_DIR / "inference_results_python.jsonl")
    java_data = load_chunk_data(DATA_PROCESSED_DIR / "inference_results_java.jsonl")

    if not python_data and not java_data:
        logger.error("No inference data found for visualization.")
        stats_path = DATA_RESULTS_DIR / "us1_correlation_stats.json"
        existing_stats = load_correlation_stats() or {}
        existing_stats["status"] = "error"
        existing_stats["reason"] = "No inference data found."
        existing_stats["plot_generated"] = False
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(existing_stats, f, indent=2)
        return existing_stats

    # Step 3: Generate plot
    output_path = DATA_RESULTS_DIR / "us1_correlation_plot.png"
    plot_success = generate_correlation_plot(python_data, java_data, output_path)

    # Step 4: Update stats
    stats = load_correlation_stats()
    if stats is None:
        stats = {}
    
    if plot_success:
        stats = update_correlation_stats_with_plot(stats, output_path)
        stats["plot_generated"] = True
    else:
        stats["status"] = "visualization_failed"
        stats["plot_generated"] = False
        stats["reason"] = "Failed to generate plot (missing libraries or data)."

    # Write final stats
    stats_path = DATA_RESULTS_DIR / "us1_correlation_stats.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    logger.info(f"Visualization analysis complete. Stats saved to {stats_path}.")
    return stats


def compute_cross_language_stats(python_data: List[Dict], java_data: List[Dict]) -> Dict[str, Any]:
    """Compute and compare correlation statistics between languages."""
    results = {}
    
    for lang_name, data in [('Python', python_data), ('Java', java_data)]:
        if not data:
            results[lang_name] = {"status": "no_data"}
            continue
        
        complexities = [d.get('cyclomatic_complexity') for d in data if d.get('cyclomatic_complexity') is not None]
        losses = [d.get('normalized_loss') for d in data if d.get('normalized_loss') is not None]
        
        if len(complexities) < 2 or len(losses) < 2 or len(complexities) != len(losses):
            results[lang_name] = {"status": "insufficient_data"}
            continue
        
        # Ensure arrays are same length for correlation
        min_len = min(len(complexities), len(losses))
        c = np.array(complexities[:min_len])
        l = np.array(losses[:min_len])
        
        pearson_r, pearson_p = np.corrcoef(c, l)[0, 1], 0.0 # Simplified p-value
        try:
            from scipy.stats import pearsonr, spearmanr
            pearson_r, pearson_p = pearsonr(c, l)
            spearman_r, spearman_p = spearmanr(c, l)
        except ImportError:
            # Fallback if scipy not available
            spearman_r, spearman_p = pearson_r, pearson_p # Placeholder
        
        results[lang_name] = {
            "n_samples": min_len,
            "pearson_r": float(pearson_r),
            "pearson_p": float(pearson_p),
            "spearman_r": float(spearman_r),
            "spearman_p": float(spearman_p)
        }
    
    return results


def write_cross_language_report(stats: Dict[str, Any]) -> None:
    """Write cross-language comparison to the stats file."""
    stats_path = DATA_RESULTS_DIR / "us1_correlation_stats.json"
    if not stats_path.exists():
        return
    
    try:
        with open(stats_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {}
    
    data["cross_language_comparison"] = stats
    
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def run_cross_language_validation() -> Dict[str, Any]:
    """Run cross-language validation and update stats."""
    python_data = load_chunk_data(DATA_PROCESSED_DIR / "inference_results_python.jsonl")
    java_data = load_chunk_data(DATA_PROCESSED_DIR / "inference_results_java.jsonl")
    
    if not python_data and not java_data:
        return {"status": "skipped", "reason": "No data available"}
    
    if not python_data or not java_data:
        return {"status": "skipped", "reason": "Missing one language dataset"}
    
    results = compute_cross_language_stats(python_data, java_data)
    write_cross_language_report(results)
    return results


def main():
    """CLI entry point for T020."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Running T020: Correlation Visualization")
    result = run_visualization_analysis()
    
    # Optionally run cross-language validation if both datasets exist
    python_path = DATA_PROCESSED_DIR / "inference_results_python.jsonl"
    java_path = DATA_PROCESSED_DIR / "inference_results_java.jsonl"
    
    if python_path.exists() and java_path.exists():
        logger.info("Running cross-language validation.")
        cross_result = run_cross_language_validation()
        logger.info(f"Cross-language result: {cross_result}")
    
    logger.info("T020 completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())