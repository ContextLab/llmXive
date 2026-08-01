import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import scipy.stats as stats

# Import existing utilities from the project
from config import get_project_root, load_environment, ensure_dirs
from utils.logging import get_logger

logger = get_logger(__name__)

# --- Existing API Surface (Preserved) ---

def load_correlation_stats(path: Optional[str] = None) -> Dict[str, Any]:
    """Load existing correlation statistics from JSON."""
    project_root = get_project_root()
    if path is None:
        path = str(project_root / "data" / "results" / "us1_correlation_stats.json")
    
    p = Path(path)
    if not p.exists():
        logger.warning(f"Correlation stats file not found at {path}. Returning empty dict.")
        return {}
    
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_variance_report(path: Optional[str] = None) -> Dict[str, Any]:
    """Load variance null report if it exists."""
    project_root = get_project_root()
    if path is None:
        path = str(project_root / "data" / "results" / "variance_null_report.json")
    
    p = Path(path)
    if not p.exists():
        return {}
    
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_correlation_plot(data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Generate scatter plot with regression lines."""
    # Implementation details omitted as per task scope (T020 handles this)
    # This stub ensures the function signature matches the API surface.
    if output_path is None:
        project_root = get_project_root()
        output_path = str(project_root / "data" / "results" / "us1_correlation_plot.png")
    return output_path

def update_correlation_stats_with_plot(stats: Dict[str, Any], plot_path: str) -> Dict[str, Any]:
    """Update stats dict with plot path."""
    stats['plot_path'] = plot_path
    return stats

def run_visualization_analysis(stats_path: Optional[str] = None, plot_path: Optional[str] = None) -> Dict[str, Any]:
    """Orchestrate loading, checking variance, and plotting."""
    # Implementation details omitted as per task scope (T020 handles this)
    return {}

def main() -> None:
    """Entry point for correlation analysis."""
    # Implementation details omitted as per task scope (T019/T020 handle this)
    pass

# --- New Functionality for T022: Cross-Language Validation ---

def load_chunk_data(language: str) -> List[Dict[str, Any]]:
    """
    Load annotated and inference results for a specific language.
    Expects data to be in data/processed/annotated_<lang>.jsonl 
    and data/processed/inference_results_<lang>.jsonl
    """
    project_root = get_project_root()
    
    annotated_path = project_root / "data" / "processed" / f"annotated_{language}.jsonl"
    inference_path = project_root / "data" / "processed" / f"inference_results_{language}.jsonl"
    
    if not annotated_path.exists() or not inference_path.exists():
        logger.warning(f"Data files missing for {language}. Skipping cross-language comparison for this language.")
        return []
    
    # Load annotated data (complexity metrics)
    annotated_data = {}
    with open(annotated_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                # Assume chunk_id is unique
                chunk_id = entry.get('chunk_id') or entry.get('id')
                if chunk_id:
                    annotated_data[chunk_id] = entry
            except json.JSONDecodeError:
                continue
    
    # Load inference data (loss metrics)
    inference_data = {}
    with open(inference_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                chunk_id = entry.get('chunk_id') or entry.get('id')
                if chunk_id:
                    inference_data[chunk_id] = entry
            except json.JSONDecodeError:
                continue
    
    # Merge data
    merged = []
    for chunk_id in annotated_data:
        if chunk_id in inference_data:
            entry = {
                **annotated_data[chunk_id],
                **inference_data[chunk_id]
            }
            merged.append(entry)
    
    return merged

def compute_cross_language_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare Pearson/Spearman coefficients between Python and Java subsets.
    Appends comparison stats to the provided stats dictionary.
    """
    languages = ['python', 'java']
    results = {}
    
    for lang in languages:
        data = load_chunk_data(lang)
        if not data:
            logger.info(f"No data available for {lang}. Skipping.")
            continue
        
        # Extract complexity and normalized_loss
        # Assuming 'cyclomatic_complexity' and 'normalized_loss' are the keys
        complexity = [d.get('cyclomatic_complexity') for d in data if d.get('cyclomatic_complexity') is not None]
        loss = [d.get('normalized_loss') for d in data if d.get('normalized_loss') is not None]
        
        # Ensure we have matching lengths (should be true if logic above is correct)
        min_len = min(len(complexity), len(loss))
        complexity = complexity[:min_len]
        loss = loss[:min_len]
        
        if len(complexity) < 2:
            logger.warning(f"Not enough data points for {lang} to compute correlation.")
            continue
        
        # Compute correlations
        pearson_r, pearson_p = stats.pearsonr(complexity, loss)
        spearman_r, spearman_p = stats.spearmanr(complexity, loss)
        
        results[lang] = {
            'n_samples': len(complexity),
            'pearson_r': float(pearson_r),
            'pearson_p': float(pearson_p),
            'spearman_r': float(spearman_r),
            'spearman_p': float(spearman_p)
        }
    
    # If we have both languages, compute comparison stats
    if 'python' in results and 'java' in results:
        python_r = results['python']['pearson_r']
        java_r = results['java']['pearson_r']
        
        # Simple difference in coefficients (Fisher's Z-transformation is more rigorous but difference is a start)
        # For a more robust test, one would use a Z-test for independent correlations
        # Here we compute the absolute difference and relative difference
        abs_diff = abs(python_r - java_r)
        rel_diff = abs_diff / (abs(python_r) + 1e-9) # Avoid division by zero
        
        comparison = {
            'pearson_difference': float(abs_diff),
            'pearson_relative_difference': float(rel_diff),
            'python_pearson': results['python']['pearson_r'],
            'java_pearson': results['java']['pearson_r'],
            'interpretation': "Similar" if abs_diff < 0.1 else "Different"
        }
        
        # If we have Spearman, compare those too
        python_s = results['python']['spearman_r']
        java_s = results['java']['spearman_r']
        comparison['spearman_difference'] = float(abs(python_s - java_s))
        comparison['python_spearman'] = python_s
        comparison['java_spearman'] = java_s
        
        results['comparison'] = comparison
    
    return results

def write_cross_language_report(stats: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Compute cross-language stats, update the main stats dict, and write to file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = str(project_root / "data" / "results" / "us1_correlation_stats.json")
    
    # Compute new stats
    cross_lang_stats = compute_cross_language_stats(stats)
    
    # Update the main stats dict
    stats['cross_language_validation'] = cross_lang_stats
    stats['cross_language_status'] = "completed"
    
    # Write back to file
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Cross-language validation results written to {output_path}")
    return output_path

def run_cross_language_validation(stats_path: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for T022.
    1. Load existing US1 correlation stats.
    2. Compute cross-language comparison.
    3. Update and save stats.
    """
    # Load existing stats
    current_stats = load_correlation_stats(stats_path)
    
    # Check if we have data to work with
    if not current_stats:
        logger.error("No existing correlation stats found. Cannot perform cross-language validation.")
        return {}
    
    # Run validation
    final_stats = write_cross_language_report(current_stats, output_path)
    
    # Return the final stats dict
    return load_correlation_stats(final_stats)

# Extend main to optionally run T022 if called with specific flag
if __name__ == "__main__":
    # If this script is run directly, we can check for args or just run the standard flow
    # For T022, we assume it's called as a dependency after T019
    if len(sys.argv) > 1 and sys.argv[1] == "--cross-language":
        result = run_cross_language_validation()
        print(json.dumps(result, indent=2))
    else:
        main()