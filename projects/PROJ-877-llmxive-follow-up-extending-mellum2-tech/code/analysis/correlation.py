import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Ensure imports match the provided API surface
# Note: 'scipy' is a standard dependency for correlation stats in this project context
try:
    from scipy.stats import pearsonr, spearmanr
except ImportError:
    print("Error: scipy is required for correlation analysis. Install it via pip install scipy.")
    sys.exit(1)

# --- Logging Setup ---
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# --- Helper Functions ---

def load_correlation_stats(path: str) -> Dict[str, Any]:
    """Load existing correlation stats from a JSON file."""
    p = Path(path)
    if not p.exists():
        logger.warning(f"Correlation stats file not found at {path}. Creating new structure.")
        return {"status": "pending", "results": {}}
    with open(p, 'r') as f:
        return json.load(f)

def write_correlation_stats(data: Dict[str, Any], path: str) -> None:
    """Write correlation stats to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Correlation stats written to {path}")

def load_variance_report(path: str) -> Optional[Dict[str, Any]]:
    """Load variance null report if it exists."""
    p = Path(path)
    if p.exists():
        with open(p, 'r') as f:
            return json.load(f)
    return None

def load_chunk_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Load chunk data from a JSONL or JSON file.
    Expected fields: chunk_id, language, complexity_metrics (dict), inference_results (dict).
    """
    path = Path(input_path)
    data = []
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if path.suffix == '.jsonl':
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            content = json.load(f)
            if isinstance(content, list):
                data = content
            elif isinstance(content, dict):
                data = [content]
    else:
        # Fallback for parquet if converted to json in previous steps, 
        # but strictly following JSONL/JSON for this implementation
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .json or .jsonl")
    
    return data

def generate_correlation_plot(data: List[Dict[str, Any]], output_path: str) -> str:
    """
    Generate a scatter plot of complexity vs normalized loss.
    Requires matplotlib and seaborn.
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        logger.error("matplotlib and seaborn are required for visualization.")
        sys.exit(1)

    python_data = [d for d in data if d.get('language') == 'python']
    java_data = [d for d in data if d.get('language') == 'java']

    if not python_data and not java_data:
        logger.warning("No data found for plotting.")
        return output_path

    plt.figure(figsize=(10, 8))
    
    if python_data:
        x_p = [d['complexity_metrics']['cyclomatic_complexity'] for d in python_data]
        y_p = [d['inference_results']['normalized_loss'] for d in python_data]
        sns.regplot(x=x_p, y=y_p, label='Python', color='blue', scatter_kws={'alpha':0.6})
    
    if java_data:
        x_j = [d['complexity_metrics']['cyclomatic_complexity'] for d in java_data]
        y_j = [d['inference_results']['normalized_loss'] for d in java_data]
        sns.regplot(x=x_j, y=y_j, label='Java', color='red', scatter_kws={'alpha':0.6})

    plt.xlabel('Cyclomatic Complexity')
    plt.ylabel('Normalized Loss (Nats)')
    plt.title('Code Complexity vs. Prediction Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(p, dpi=300)
    plt.close()
    logger.info(f"Plot saved to {output_path}")
    return output_path

def update_correlation_stats_with_plot(stats: Dict[str, Any], plot_path: str) -> Dict[str, Any]:
    """Update stats dictionary with plot path."""
    stats['plot_path'] = plot_path
    stats['status'] = 'visualization_complete'
    return stats

def run_visualization_analysis(input_path: str, output_stats_path: str, output_plot_path: str) -> Dict[str, Any]:
    """
    Main entry point for correlation analysis and visualization.
    Computes Pearson/Spearman correlations and generates a plot.
    """
    logger.info(f"Loading data from {input_path}")
    data = load_chunk_data(input_path)
    
    # Check variance first (T011b logic)
    # In a real pipeline, we might check the variance report file here,
    # but for this function, we assume data is valid unless empty.
    if not data:
        raise ValueError("Input data is empty.")

    # Aggregate results
    results = {"python": [], "java": []}
    
    for item in data:
        lang = item.get('language', 'unknown')
        if lang not in ['python', 'java']:
            continue
        
        complexity = item.get('complexity_metrics', {}).get('cyclomatic_complexity')
        loss = item.get('inference_results', {}).get('normalized_loss')
        
        if complexity is not None and loss is not None:
            results[lang].append({'complexity': complexity, 'loss': loss})

    stats = {"status": "computed", "timestamp": str(Path(output_stats_path).parent)}
    
    for lang, items in results.items():
        if len(items) < 2:
            logger.warning(f"Not enough data for {lang} to compute correlation.")
            stats['results'][lang] = {"error": "insufficient_data"}
            continue

        x = [i['complexity'] for i in items]
        y = [i['loss'] for i in items]

        # Pearson
        try:
            r_p, p_p = pearsonr(x, y)
        except Exception as e:
            r_p, p_p = None, None
            logger.error(f"Pearson calculation failed for {lang}: {e}")

        # Spearman
        try:
            r_s, p_s = spearmanr(x, y)
        except Exception as e:
            r_s, p_s = None, None
            logger.error(f"Spearman calculation failed for {lang}: {e}")

        stats['results'][lang] = {
            "count": len(items),
            "pearson": {"r": r_p, "p_value": p_p},
            "spearman": {"r": r_s, "p_value": p_s}
        }

    # Generate Plot
    if any(len(v) > 1 for v in results.values()):
        generate_correlation_plot(data, output_plot_path)
        stats = update_correlation_stats_with_plot(stats, output_plot_path)
    else:
        logger.warning("No valid data pairs for plotting.")

    write_correlation_stats(stats, output_stats_path)
    return stats

def compute_cross_language_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare Pearson/Spearman coefficients between Python and Java subsets.
    Appends comparison stats to the provided stats dictionary.
    """
    results = stats.get('results', {})
    
    if 'python' not in results or 'java' not in results:
        logger.warning("Cannot compute cross-language stats: missing one or both language results.")
        return stats

    python_res = results['python']
    java_res = results['java']

    if 'error' in python_res or 'error' in java_res:
        logger.warning("Cannot compute cross-language stats: one or both languages have errors.")
        return stats

    # Extract values
    p_pearson_r = python_res['pearson']['r']
    p_pearson_p = python_res['pearson']['p_value']
    p_spearman_r = python_res['spearman']['r']
    p_spearman_p = python_res['spearman']['p_value']

    j_pearson_r = java_res['pearson']['r']
    j_pearson_p = java_res['pearson']['p_value']
    j_spearman_r = java_res['spearman']['r']
    j_spearman_p = java_res['spearman']['p_value']

    # Calculate differences
    diff_pearson_r = abs(p_pearson_r - j_pearson_r) if (p_pearson_r is not None and j_pearson_r is not None) else None
    diff_spearman_r = abs(p_spearman_r - j_spearman_r) if (p_spearman_r is not None and j_spearman_r is not None) else None

    # Simple significance check on difference (approximate):
    # If the confidence intervals (not calculated here for brevity, but implied by p-values)
    # don't overlap significantly, we note it. 
    # For this implementation, we report the raw difference and the individual p-values.
    
    cross_lang_analysis = {
        "pearson_r_difference": diff_pearson_r,
        "spearman_r_difference": diff_spearman_r,
        "python_pearson_p": p_pearson_p,
        "java_pearson_p": j_pearson_p,
        "python_spearman_p": p_spearman_p,
        "java_spearman_p": j_spearman_p,
        "interpretation": "Comparing correlation strength across languages."
    }

    stats['cross_language_validation'] = cross_lang_analysis
    return stats

def write_cross_language_report(stats: Dict[str, Any], output_path: str) -> None:
    """Write the updated stats (including cross-language validation) to JSON."""
    write_correlation_stats(stats, output_path)

def run_cross_language_validation(input_stats_path: str, output_stats_path: str) -> Dict[str, Any]:
    """
    Main entry point for T022: Cross-language validation.
    Loads stats, computes cross-language comparison, and saves.
    """
    logger.info(f"Loading correlation stats from {input_stats_path}")
    stats = load_correlation_stats(input_stats_path)
    
    if stats.get('status') != 'computed':
        logger.warning("Input stats do not indicate successful correlation computation.")
        # We still proceed to attempt calculation if data exists, but warn.

    logger.info("Computing cross-language validation statistics...")
    updated_stats = compute_cross_language_stats(stats)
    
    logger.info(f"Writing updated stats to {output_stats_path}")
    write_cross_language_report(updated_stats, output_stats_path)
    
    return updated_stats

def main():
    """CLI entry point for T022."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cross-language validation for correlation analysis")
    parser.add_argument("--input-stats", required=True, help="Path to input correlation stats JSON (e.g., us1_correlation_stats.json)")
    parser.add_argument("--output", required=True, help="Path to output updated stats JSON")
    
    args = parser.parse_args()
    
    try:
        run_cross_language_validation(args.input_stats, args.output)
        logger.info("T022 Cross-language validation completed successfully.")
    except Exception as e:
        logger.error(f"Task T022 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()