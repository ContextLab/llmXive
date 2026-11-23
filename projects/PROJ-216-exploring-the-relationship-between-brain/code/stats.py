import os
import sys
import csv
import json
import math
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats as scipy_stats
from statsmodels.stats.power import tt_solve_power, FTestPower, FTestAnovaPower

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
CORRELATION_RESULTS_PATH = "data/processed/correlation_results.csv"
LIMITATIONS_TEXT = (
    "This study utilizes a sample size of N=10 subjects, which provides low statistical power "
    "for detecting small effect sizes. Results should be interpreted as exploratory and require validation in larger cohorts."
)

def load_graph_metrics(metrics_path: str) -> List[Dict[str, Any]]:
    """Load graph metrics from CSV."""
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Graph metrics file not found: {metrics_path}")
    
    data = []
    with open(metrics_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for field in ['value', 'fluid_intelligence_score', 'age']:
                if field in row and row[field] is not None and row[field] != '':
                    try:
                        row[field] = float(row[field])
                    except ValueError:
                        row[field] = None
            data.append(row)
    return data

def load_behavioral_scores(behavioral_path: str) -> List[Dict[str, Any]]:
    """Load behavioral scores from CSV."""
    if not os.path.exists(behavioral_path):
        raise FileNotFoundError(f"Behavioral scores file not found: {behavioral_path}")
    
    data = []
    with open(behavioral_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in ['score_value', 'fluid_intelligence_score', 'age']:
                if field in row and row[field] is not None and row[field] != '':
                    try:
                        row[field] = float(row[field])
                    except ValueError:
                        row[field] = None
            data.append(row)
    return data

def merge_metrics_with_scores(metrics: List[Dict], scores: List[Dict]) -> List[Dict]:
    """Merge graph metrics with behavioral scores by subject_id."""
    score_map = {s['subject_id']: s for s in scores}
    merged = []
    for m in metrics:
        sid = m.get('subject_id')
        if sid in score_map:
            s = score_map[sid]
            merged.append({
                'subject_id': sid,
                'metric_name': m.get('metric_name'),
                'value': m.get('value'),
                'fluid_intelligence_score': m.get('fluid_intelligence_score') or s.get('fluid_intelligence_score'),
                'age': m.get('age') or s.get('age'),
                'gender': m.get('gender') or s.get('gender')
            })
    return merged

def bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    corrected = []
    for p in p_values:
        if p is None:
            corrected.append(None)
        else:
            adj = p * n_tests
            corrected.append(min(adj, 1.0))
    return corrected

def compute_correlation(x: List[float], y: List[float], method: str = 'pearson') -> Tuple[Optional[float], Optional[float]]:
    """Compute correlation coefficient and p-value."""
    # Filter out None values
    pairs = [(xi, yi) for xi, yi in zip(x, y) if xi is not None and yi is not None]
    if len(pairs) < 3:
        logger.warning(f"Insufficient data points ({len(pairs)}) for correlation. Returning None.")
        return None, None
    
    x_clean = [p[0] for p in pairs]
    y_clean = [p[1] for p in pairs]
    
    try:
        if method == 'pearson':
            corr, p_val = scipy_stats.pearsonr(x_clean, y_clean)
        elif method == 'spearman':
            corr, p_val = scipy_stats.spearmanr(x_clean, y_clean)
        else:
            raise ValueError(f"Unknown correlation method: {method}")
        
        return float(corr), float(p_val)
    except Exception as e:
        logger.error(f"Correlation computation failed: {e}")
        return None, None

def analyze_correlations(metrics_data: List[Dict], metric_name: str) -> Dict[str, Any]:
    """Analyze correlation between a specific metric and Fluid Intelligence."""
    # Filter for the specific metric
    subset = [d for d in metrics_data if d.get('metric_name') == metric_name]
    
    if not subset:
        logger.warning(f"No data found for metric: {metric_name}")
        return {
            'metric_name': metric_name,
            'n': 0,
            'correlation': None,
            'p_value': None,
            'method': 'pearson'
        }
    
    x = [d['value'] for d in subset]
    y = [d['fluid_intelligence_score'] for d in subset]
    
    corr, p_val = compute_correlation(x, y, method='pearson')
    
    return {
        'metric_name': metric_name,
        'n': len(subset),
        'correlation': corr,
        'p_value': p_val,
        'method': 'pearson'
    }

def run_multiple_linear_regression(metrics_data: List[Dict], metric_name: str) -> Dict[str, Any]:
    """Run multiple linear regression with age and gender as covariates."""
    subset = [d for d in metrics_data if d.get('metric_name') == metric_name]
    
    # Filter out rows with missing covariates
    valid_subset = [d for d in subset if d.get('age') is not None and d.get('gender') is not None]
    
    if len(valid_subset) < 4:
        logger.warning(f"Insufficient data for regression (n={len(valid_subset)}). Skipping.")
        return {
            'metric_name': metric_name,
            'n': len(subset),
            'n_valid': len(valid_subset),
            'coefficients': None,
            'r_squared': None,
            'p_value': None
        }
    
    y = np.array([d['fluid_intelligence_score'] for d in valid_subset])
    X_age = np.array([d['age'] for d in valid_subset])
    
    # Encode gender (M=0, F=1)
    X_gender = np.array([1 if d['gender'] in ['F', 'Female', 'female'] else 0 for d in valid_subset])
    X_const = np.ones(len(valid_subset))
    
    X = np.column_stack((X_const, X_age, X_gender))
    
    try:
        # OLS regression manually
        # beta = (X'X)^-1 X'y
        XtX = X.T @ X
        XtX_inv = np.linalg.inv(XtX)
        beta = XtX_inv @ (X.T @ y)
        
        y_pred = X @ beta
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Simple p-value approximation for the model (F-test)
        # F = (R^2 / k) / ((1 - R^2) / (n - k - 1))
        n = len(valid_subset)
        k = 2 # age, gender
        if r_squared < 1.0 and (n - k - 1) > 0:
            f_stat = (r_squared / k) / ((1 - r_squared) / (n - k - 1))
            # Approximate p-value using scipy
            from scipy.stats import f
            p_val = 1 - f.cdf(f_stat, k, n - k - 1)
        else:
            p_val = 1.0
        
        return {
            'metric_name': metric_name,
            'n': len(subset),
            'n_valid': len(valid_subset),
            'coefficients': {
                'intercept': float(beta[0]),
                'age': float(beta[1]),
                'gender': float(beta[2])
            },
            'r_squared': float(r_squared),
            'p_value': float(p_val)
        }
    except Exception as e:
        logger.error(f"Regression failed: {e}")
        return {
            'metric_name': metric_name,
            'n': len(subset),
            'n_valid': len(valid_subset),
            'coefficients': None,
            'r_squared': None,
            'p_value': None
        }

def calculate_power(n: int, effect_size: float, alpha: float = 0.05) -> float:
    """Calculate statistical power for a correlation test."""
    # Using t-test approximation for correlation
    # t = r * sqrt((n-2) / (1-r^2))
    # We use statsmodels for a more robust calculation if available, 
    # otherwise approximate.
    try:
        # Solve for power given n, effect_size (r), alpha
        # statsmodels tt_solve_power expects effect size for mean difference, 
        # but for correlation we can approximate or use a custom function.
        # Here we use a direct approximation:
        # Power = 1 - Beta. 
        # Using the non-central t-distribution is complex without full statsmodels integration.
        # We will use a simplified approximation:
        # Power ~ Phi( sqrt(n-3) * 0.5 * ln((1+r)/(1-r)) - 1.96 )
        if n <= 3:
            return 0.0
        
        z_r = 0.5 * math.log((1 + effect_size) / (1 - effect_size))
        se = 1 / math.sqrt(n - 3)
        z_beta = z_r / se - 1.96 # 1.96 for alpha=0.05 two-tailed
        
        from scipy.stats import norm
        power = norm.cdf(z_beta)
        return float(power)
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}")
        return 0.0

def generate_power_analysis_table(results: List[Dict]) -> List[Dict]:
    """Generate power analysis for each result."""
    table = []
    for res in results:
        if res.get('correlation') is not None:
            r = abs(res['correlation'])
            power = calculate_power(res['n'], r)
            table.append({
                'metric_name': res['metric_name'],
                'n': res['n'],
                'observed_r': res['correlation'],
                'power_at_observed_r': power
            })
    return table

def create_limitations_text() -> str:
    """Return the standard limitations text."""
    return LIMITATIONS_TEXT

def generate_power_summary_table(power_table: List[Dict]) -> str:
    """Generate a text summary of power analysis."""
    lines = ["## Power Analysis Summary", ""]
    for row in power_table:
        lines.append(f"- {row['metric_name']}: N={row['n']}, r={row['observed_r']:.3f}, Power={row['power_at_observed_r']:.2f}")
    lines.append("")
    lines.append(create_limitations_text())
    return "\n".join(lines)

def append_limitations_section(report_content: str) -> str:
    """Append limitations section to report content."""
    return report_content + "\n\n" + create_limitations_text()

def main():
    """Main entry point for correlation analysis."""
    parser = argparse.ArgumentParser(description="Analyze correlation between graph metrics and Fluid Intelligence.")
    parser.add_argument("--metrics", type=str, default="data/processed/graph_metrics.csv", help="Path to graph metrics CSV")
    parser.add_argument("--behavioral", type=str, default="data/processed/behavioral.csv", help="Path to behavioral scores CSV")
    parser.add_argument("--output", type=str, default=CORRELATION_RESULTS_PATH, help="Path to output CSV")
    args = parser.parse_args()

    logger.info(f"Loading graph metrics from {args.metrics}")
    metrics_data = load_graph_metrics(args.metrics)
    
    logger.info(f"Loading behavioral scores from {args.behavioral}")
    # Note: In this pipeline, behavioral scores are often merged into graph_metrics.csv
    # If a separate file is provided, we merge them. Otherwise, we assume metrics_data has the scores.
    # For robustness, we check if 'fluid_intelligence_score' exists in metrics_data.
    has_scores = all('fluid_intelligence_score' in m and m['fluid_intelligence_score'] is not None for m in metrics_data if 'metric_name' in m)
    
    if not has_scores:
        logger.warning("Fluid Intelligence scores not found in metrics file. Attempting to load from separate file.")
        if os.path.exists(args.behavioral):
            scores_data = load_behavioral_scores(args.behavioral)
            metrics_data = merge_metrics_with_scores(metrics_data, scores_data)
        else:
            logger.error("Behavioral file not found and scores missing in metrics file. Cannot proceed.")
            sys.exit(1)

    # Validate data
    valid_metrics = [m for m in metrics_data if m.get('fluid_intelligence_score') is not None]
    if not valid_metrics:
        logger.error("No valid Fluid Intelligence scores found for correlation analysis.")
        sys.exit(1)
    
    # Identify unique metrics
    unique_metrics = list(set(m['metric_name'] for m in valid_metrics))
    logger.info(f"Found {len(unique_metrics)} unique metrics to analyze: {unique_metrics}")

    results = []
    for metric in unique_metrics:
        logger.info(f"Analyzing {metric}...")
        corr_res = analyze_correlations(valid_metrics, metric)
        reg_res = run_multiple_linear_regression(valid_metrics, metric)
        
        results.append({
            'metric_name': metric,
            'n': corr_res['n'],
            'correlation': corr_res['correlation'],
            'p_value': corr_res['p_value'],
            'regression_n': reg_res['n_valid'],
            'regression_r_squared': reg_res['r_squared'],
            'regression_p_value': reg_res['p_value']
        })

    # Apply Bonferroni correction
    n_tests = len(results)
    raw_p_values = [r['p_value'] for r in results if r['p_value'] is not None]
    if raw_p_values:
        corrected_p_values = bonferroni_correction(raw_p_values, n_tests)
        # Map back
        idx = 0
        for r in results:
            if r['p_value'] is not None:
                r['p_value_bonferroni'] = corrected_p_values[idx]
                idx += 1
            else:
                r['p_value_bonferroni'] = None
    else:
        for r in results:
            r['p_value_bonferroni'] = None

    # Write results
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(args.output, 'w', newline='') as f:
        fieldnames = ['metric_name', 'n', 'correlation', 'p_value', 'p_value_bonferroni', 'regression_n', 'regression_r_squared', 'regression_p_value']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    
    logger.info(f"Results written to {args.output}")
    logger.info("Correlation analysis completed.")

if __name__ == "__main__":
    main()
