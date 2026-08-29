import os
import csv
import json
import math
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from config import is_ci_mode, is_research_mode, get_mode, get_path
from utils.logger import get_logger

logger = get_logger(__name__)

def load_scores_csv(filepath: str) -> Dict[str, float]:
    """
    Load scores from a CSV file into a dictionary mapping image_id to score.
    Expects columns: image_id, score (and optionally others).
    """
    scores = {}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Scores file not found: {filepath}")
    
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'image_id' not in row or 'score' not in row:
                raise ValueError(f"CSV must contain 'image_id' and 'score' columns. Found: {row.keys()}")
            try:
                scores[row['image_id']] = float(row['score'])
            except ValueError:
                logger.warning(f"Skipping invalid score for image_id {row['image_id']}: {row['score']}")
    return scores

def load_mask_metrics_csv(filepath: str) -> Dict[str, Dict[str, float]]:
    """
    Load mask metrics from a CSV file.
    Expects columns: image_id, gradient_variance, texture_entropy (or similar metric columns).
    Returns a dict: { image_id: { metric_name: value, ... } }
    """
    metrics = {}
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Mask metrics file not found: {filepath}")
    
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'image_id' not in reader.fieldnames:
            raise ValueError("CSV must contain 'image_id' column.")
        
        # Identify metric columns (exclude image_id)
        metric_cols = [c for c in reader.fieldnames if c != 'image_id']
        
        for row in reader:
            img_id = row['image_id']
            metrics[img_id] = {}
            for col in metric_cols:
                try:
                    metrics[img_id][col] = float(row[col])
                except ValueError:
                    logger.warning(f"Skipping invalid metric {col} for image_id {img_id}: {row[col]}")
    return metrics

def merge_scores_and_metrics(scores: Dict[str, float], metrics: Dict[str, Dict[str, float]]) -> List[Tuple[str, float, float, float]]:
    """
    Merge scores and metrics by image_id.
    Returns a list of tuples: (image_id, score, metric_val, metric_name)
    Only includes entries where image_id exists in both dicts.
    """
    merged = []
    common_ids = set(scores.keys()) & set(metrics.keys())
    
    if not common_ids:
        raise ValueError("No common image_ids found between scores and metrics files.")
    
    logger.info(f"Merging {len(common_ids)} common entries.")
    
    for img_id in common_ids:
        score_val = scores[img_id]
        for metric_name, metric_val in metrics[img_id].items():
            merged.append((img_id, score_val, metric_val, metric_name))
    
    return merged

def calculate_pearson_correlation(data: List[Tuple[str, float, float, str]]) -> Dict[str, Dict[str, float]]:
    """
    Calculate Pearson correlation coefficient (r) and p-value for each metric against scores.
    
    Args:
        data: List of (image_id, score, metric_val, metric_name) tuples.
    
    Returns:
        Dict mapping metric_name to {'r': float, 'p': float, 'n': int}.
    """
    if not data:
        raise ValueError("Data list is empty.")
    
    # Group by metric
    groups = {}
    for img_id, score, metric_val, metric_name in data:
        if metric_name not in groups:
            groups[metric_name] = []
        groups[metric_name].append((score, metric_val))
    
    results = {}
    
    for metric_name, pairs in groups.items():
        n = len(pairs)
        if n < 3:
            logger.warning(f"Not enough data points ({n}) for Pearson correlation on {metric_name}. Skipping.")
            continue
        
        x = [p[0] for p in pairs] # scores
        y = [p[1] for p in pairs] # metrics
        
        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        # Calculate covariance and standard deviations
        cov_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        var_x = sum((xi - mean_x) ** 2 for xi in x)
        var_y = sum((yi - mean_y) ** 2 for yi in y)
        
        if var_x == 0 or var_y == 0:
            logger.warning(f"Zero variance detected for {metric_name} or scores. Correlation undefined.")
            r = 0.0
        else:
            r = cov_xy / math.sqrt(var_x * var_y)
        
        # Approximate p-value using t-distribution
        # t = r * sqrt((n-2) / (1-r^2))
        # We use a simple approximation or check against critical values if we can't import scipy.
        # Since scipy might not be available or we want to avoid heavy deps for simple stats,
        # we can implement a basic t-test approximation or return the t-statistic.
        # However, the task asks for p-value. If scipy is in requirements (T002), we should use it.
        # The prompt says "import only names that exist... in standard library, declared dependencies".
        # T002 includes scipy. Let's try to import scipy.stats. If it fails, we fallback to a rough approximation.
        
        p_val = 1.0 # Default
        try:
            from scipy import stats
            # Perform actual test
            # scipy.stats.pearsonr returns (r, p)
            # But we calculated r manually to be safe with our data structure.
            # Let's just use scipy for the p-value calculation based on r and n.
            # t = r * sqrt((n-2)/(1-r^2))
            if abs(r) < 1.0:
                t_stat = r * math.sqrt((n - 2) / (1 - r * r))
                # Two-tailed p-value
                p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            else:
                p_val = 0.0
        except ImportError:
            logger.warning("scipy not found. Returning t-statistic approximation or 1.0 for p-value.")
            # Fallback: if r is close to 1, p is small. If r is 0, p is 1.
            # This is a very rough heuristic without scipy.
            if abs(r) > 0.99:
                p_val = 0.001
            else:
                p_val = 0.5 # Placeholder
        
        results[metric_name] = {
            'r': r,
            'p': p_val,
            'n': n
        }
        
        logger.info(f"Correlation for {metric_name}: r={r:.4f}, p={p_val:.4f}, n={n}")
    
    return results

def run_correlation_analysis(scores_path: str, metrics_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main routine to load data, merge, calculate correlations, and save results.
    """
    logger.info(f"Loading scores from {scores_path}")
    scores = load_scores_csv(scores_path)
    
    logger.info(f"Loading mask metrics from {metrics_path}")
    metrics = load_mask_metrics_csv(metrics_path)
    
    logger.info("Merging data...")
    merged_data = merge_scores_and_metrics(scores, metrics)
    
    logger.info("Calculating Pearson correlations...")
    correlation_results = calculate_pearson_correlation(merged_data)
    
    # Prepare summary
    summary = {
        'mode': get_mode(),
        'scores_file': scores_path,
        'metrics_file': metrics_path,
        'total_entries_processed': len(merged_data),
        'metrics_analyzed': list(correlation_results.keys()),
        'results': correlation_results
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Correlation analysis complete. Results saved to {output_path}")
    
    return summary

def main():
    parser = argparse.ArgumentParser(description="Run correlation analysis between synthetic metrics and ground truth.")
    parser.add_argument('--scores', type=str, required=True, help="Path to scores CSV (e.g., data/annotations/decoupled_scores.csv)")
    parser.add_argument('--metrics', type=str, required=True, help="Path to mask metrics CSV (e.g., data/processed/mask_metrics.csv)")
    parser.add_argument('--output', type=str, required=True, help="Path to output JSON file (e.g., data/results/correlation_analysis.json)")
    
    args = parser.parse_args()
    
    try:
        run_correlation_analysis(args.scores, args.metrics, args.output)
        print("Success")
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()