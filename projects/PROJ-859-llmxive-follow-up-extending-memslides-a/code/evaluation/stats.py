import os
import sys
import json
import warnings
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Try to import statsmodels, if not available, we might need to implement a simple fallback
# or raise a clear error. For this task, we assume statsmodels is in requirements.txt.
try:
    import statsmodels.api as sm
    from statsmodels.stats.weightstats import DescrStatsW
except ImportError:
    raise ImportError("statsmodels is required for statistical analysis. Install it via pip.")

class StatisticalAnalysisError(Exception):
    """Raised when statistical analysis fails."""
    pass

def load_data_for_analysis(deltas_path: Path, features_path: Path) -> Tuple[List[Dict], List[Dict]]:
    if not deltas_path.exists():
        raise StatisticalAnalysisError(f"Deltas file not found: {deltas_path}")
    if not features_path.exists():
        raise StatisticalAnalysisError(f"Feature matrix not found: {features_path}")

    # Load deltas
    deltas = []
    with open(deltas_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            deltas.append({
                'trace_id': row['trace_id'],
                'baseline_acc': float(row['baseline_acc']),
                'compressed_acc': float(row['compressed_acc']),
                'delta_acc': float(row['delta_acc']),
                'fidelity_loss': float(row['fidelity_loss'])
            })

    # Load features
    features = []
    with open(features_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            features.append({
                'trace_id': row['trace_id'],
                'sequence_entropy': float(row['sequence_entropy']),
                'tool_repetition_freq': float(row['tool_repetition_freq']),
                'arg_semantic_variance': float(row['arg_semantic_variance'])
            })

    # Merge by trace_id
    features_dict = {f['trace_id']: f for f in features}
    merged = []
    for d in deltas:
        if d['trace_id'] in features_dict:
            merged.append({**d, **features_dict[d['trace_id']]})
        else:
            warnings.warn(f"Trace ID {d['trace_id']} found in deltas but not in features. Skipping.")
    
    # Check for NaNs
    for i, row in enumerate(merged):
        for key, val in row.items():
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                raise StatisticalAnalysisError(f"Invalid value (NaN/Inf) found in merged data at index {i}, key {key}. "
                                               f"Please ensure input data is clean.")
    
    return merged

def run_beta_regression(data: List[Dict], dependent: str = 'fidelity_loss', 
                        independent: List[str] = ['sequence_entropy', 'tool_repetition_freq', 'arg_semantic_variance']) -> Dict[str, Any]:
    """
    Perform Beta regression of Fidelity Loss on Structural Metrics.
    """
    if not data:
        raise StatisticalAnalysisError("No data for beta regression.")

    y = [d[dependent] for d in data]
    # Ensure y is in (0, 1) for Beta regression. If 0 or 1, transform slightly.
    y = [max(0.001, min(0.999, val)) for val in y]
    
    X = [[d[k] for k in independent] for d in data]
    X = sm.add_constant(X)
    
    # Fit Beta regression model
    try:
        model = sm.GLM(y, X, family=sm.families.Beta())
        results = model.fit()
    except Exception as e:
        raise StatisticalAnalysisError(f"Beta regression failed: {e}")

    return {
        'method': 'beta_regression',
        'coefficients': dict(zip(['const'] + independent, results.params.tolist())),
        'p_values': dict(zip(['const'] + independent, results.pvalues.tolist())),
        'aic': results.aic,
        'bic': results.bic
    }

def run_logistic_regression(data: List[Dict], dependent: str = 'fidelity_loss', 
                            independent: List[str] = ['sequence_entropy', 'tool_repetition_freq', 'arg_semantic_variance']) -> Dict[str, Any]:
    """
    Perform Logistic Regression on log-odds of Fidelity Loss.
    """
    if not data:
        raise StatisticalAnalysisError("No data for logistic regression.")

    y = [d[dependent] for d in data]
    # Transform to log-odds
    y = [math.log(val / (1 - val)) if 0 < val < 1 else 0 for val in y]
    
    X = [[d[k] for k in independent] for d in data]
    X = sm.add_constant(X)
    
    try:
        model = sm.GLM(y, X, family=sm.families.Gaussian()) # Approximating logit with Gaussian on log-odds
        results = model.fit()
    except Exception as e:
        raise StatisticalAnalysisError(f"Logistic regression failed: {e}")

    return {
        'method': 'logistic_regression',
        'coefficients': dict(zip(['const'] + independent, results.params.tolist())),
        'p_values': dict(zip(['const'] + independent, results.pvalues.tolist())),
        'aic': results.aic
    }

def run_spearman_correlation(data: List[Dict], target: str = 'delta_acc', 
                             independent: List[str] = ['sequence_entropy', 'tool_repetition_freq', 'arg_semantic_variance']) -> Dict[str, Any]:
    """
    Perform Spearman correlation between structural metrics and target.
    """
    import scipy.stats as stats
    
    correlations = {}
    p_values = {}
    
    y = [d[target] for d in data]
    
    for var in independent:
        x = [d[var] for d in data]
        corr, p = stats.spearmanr(x, y)
        correlations[var] = corr
        p_values[var] = p

    return {
        'method': 'spearman_correlation',
        'target': target,
        'correlations': correlations,
        'p_values': p_values
    }

def main():
    """
    Main entry point for T035.
    Performs Beta regression, Logistic regression, and Spearman correlation.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    data_root = project_root / "data"
    
    deltas_path = data_root / "processed" / "accuracy_deltas.csv"
    features_path = data_root / "processed" / "feature_matrix.csv"
    output_path = data_root / "processed" / "statistical_analysis.json"

    print("Loading data for statistical analysis...")
    try:
        data = load_data_for_analysis(deltas_path, features_path)
    except Exception as e:
        raise StatisticalAnalysisError(f"Failed to load data: {e}")

    print(f"Loaded {len(data)} records.")
    
    results = {}
    
    try:
        print("Running Beta Regression...")
        results['beta_regression'] = run_beta_regression(data)
    except Exception as e:
        results['beta_regression'] = {'error': str(e)}
    
    try:
        print("Running Logistic Regression...")
        results['logistic_regression'] = run_logistic_regression(data)
    except Exception as e:
        results['logistic_regression'] = {'error': str(e)}
    
    try:
        print("Running Spearman Correlation...")
        results['spearman_correlation'] = run_spearman_correlation(data)
    except Exception as e:
        results['spearman_correlation'] = {'error': str(e)}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Statistical analysis saved to {output_path}")
    return 0

if __name__ == "__main__":
    import csv
    sys.exit(main())
