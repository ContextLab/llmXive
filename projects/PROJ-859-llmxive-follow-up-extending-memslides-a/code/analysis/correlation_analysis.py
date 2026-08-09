import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Try to import scipy for Spearman correlation
try:
    import scipy.stats as stats
except ImportError:
    raise ImportError("scipy is required for correlation analysis. Install it via pip.")

class CorrelationAnalysisError(Exception):
    """Raised when correlation analysis fails."""
    pass

def load_correlation_data(features_path: Path, scores_path: Path) -> List[Dict[str, Any]]:
    if not features_path.exists():
        raise CorrelationAnalysisError(f"Feature matrix not found: {features_path}")
    if not scores_path.exists():
        raise CorrelationAnalysisError(f"Compressibility scores not found: {scores_path}")

    # Load features
    features = {}
    with open(features_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            features[row['trace_id']] = {
                'sequence_entropy': float(row['sequence_entropy']),
                'tool_repetition_freq': float(row['tool_repetition_freq']),
                'arg_semantic_variance': float(row['arg_semantic_variance'])
            }

    # Load scores (assuming per_trace_scores.csv from T023)
    scores = {}
    with open(scores_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores[row['trace_id']] = float(row['score'])

    # Merge
    merged = []
    for tid in features:
        if tid in scores:
            merged.append({
                'trace_id': tid,
                'score': scores[tid],
                **features[tid]
            })
        else:
            print(f"Warning: Trace {tid} in features but not in scores.")
    
    return merged

def spearman_correlation(data: List[Dict], x_key: str, y_key: str) -> Tuple[float, float]:
    x = [d[x_key] for d in data]
    y = [d[y_key] for d in data]
    return stats.spearmanr(x, y)

def run_correlation_analysis(data: List[Dict], target_key: str = 'score') -> Dict[str, Any]:
    metrics = ['sequence_entropy', 'tool_repetition_freq', 'arg_semantic_variance']
    results = {}
    
    for metric in metrics:
        corr, p_val = spearman_correlation(data, metric, target_key)
        results[metric] = {
            'correlation': corr,
            'p_value': p_val
        }
    
    return results

def interpret_correlation(results: Dict[str, Any]) -> str:
    summary = []
    for metric, res in results.items():
        corr = res['correlation']
        p = res['p_value']
        strength = "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
        direction = "positive" if corr > 0 else "negative"
        sig = "significant" if p < 0.05 else "not significant"
        summary.append(f"{metric}: {strength} {direction} correlation ({corr:.3f}), {sig} (p={p:.3f})")
    return "\n".join(summary)

def main():
    """
    Main entry point for T036.
    Implements Spearman correlation analysis between structural metrics and per-trace Compressibility Score.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_root = project_root / "data"
    
    features_path = data_root / "processed" / "feature_matrix.csv"
    scores_path = data_root / "processed" / "per_trace_scores.csv"
    output_path = data_root / "processed" / "correlation_analysis.json"

    if not features_path.exists():
        raise CorrelationAnalysisError(f"Feature matrix not found at {features_path}.")
    if not scores_path.exists():
        raise CorrelationAnalysisError(f"Per-trace scores not found at {scores_path}. "
                                       "Please ensure rule_induction.py has generated per_trace_scores.csv.")

    print("Loading data for correlation analysis...")
    try:
        data = load_correlation_data(features_path, scores_path)
    except Exception as e:
        raise CorrelationAnalysisError(f"Failed to load data: {e}")

    print(f"Loaded {len(data)} records.")
    
    results = run_correlation_analysis(data)
    interpretation = interpret_correlation(results)
    
    output = {
        'correlations': results,
        'interpretation': interpretation
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"Correlation analysis saved to {output_path}")
    print("\nInterpretation:\n", interpretation)
    
    return 0

if __name__ == "__main__":
    import csv
    sys.exit(main())
