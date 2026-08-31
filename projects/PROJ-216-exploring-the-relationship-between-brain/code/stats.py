import os
import sys
import csv
import json
import math
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np

try:
    from statsmodels.stats.power import TTestIndPower, TTestPower
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logging.warning("statsmodels not installed. Power analysis will be skipped.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

def load_graph_metrics(filepath: str) -> List[Dict[str, Any]]:
    """Load graph metrics from CSV."""
    metrics = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Graph metrics file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append({
                'subject_id': row['subject_id'],
                'metric_name': row['metric_name'],
                'value': float(row['value']),
                'fluid_intelligence_score': float(row.get('fluid_intelligence_score', 0)),
                'age': int(row.get('age', 0)),
                'gender': row.get('gender', '')
            })
    return metrics

def load_behavioral_scores(filepath: str) -> List[Dict[str, Any]]:
    """Load behavioral scores from CSV."""
    scores = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Behavioral scores file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append({
                'subject_id': row['subject_id'],
                'score_value': float(row['score_value']),
                'source_type': row.get('source_type', 'unknown')
            })
    return scores

def merge_metrics_with_scores(metrics: List[Dict], scores: List[Dict]) -> List[Dict]:
    """Merge graph metrics with behavioral scores."""
    score_map = {s['subject_id']: s['score_value'] for s in scores}
    merged = []
    for m in metrics:
        if m['subject_id'] in score_map:
            m['behavioral_score'] = score_map[m['subject_id']]
            merged.append(m)
    return merged

def bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """Apply Bonferroni correction to p-values."""
    corrected = []
    for p in p_values:
        corrected_p = min(p * n_tests, 1.0)
        corrected.append(corrected_p)
    return corrected

def compute_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Compute Pearson correlation coefficient and p-value."""
    if len(x) != len(y) or len(x) < 3:
        return 0.0, 1.0
    
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denom_x = math.sqrt(sum((x[i] - mean_x)**2 for i in range(n)))
    denom_y = math.sqrt(sum((y[i] - mean_y)**2 for i in range(n)))
    
    if denom_x == 0 or denom_y == 0:
        return 0.0, 1.0
    
    r = numerator / (denom_x * denom_y)
    
    # Approximate p-value for Pearson correlation
    # t = r * sqrt((n-2) / (1-r^2))
    if abs(r) >= 1.0:
        p_value = 0.0
    else:
        t_stat = r * math.sqrt((n - 2) / (1 - r**2))
        # Two-tailed p-value approximation using t-distribution
        # For simplicity, we use a standard normal approximation for large n
        # A more accurate implementation would use scipy.stats.t.sf
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    
    return r, p_value

def analyze_correlations(merged_data: List[Dict], metric_name: str) -> Dict[str, Any]:
    """Analyze correlations for a specific metric."""
    values = [d['value'] for d in merged_data if d['metric_name'] == metric_name]
    scores = [d['fluid_intelligence_score'] for d in merged_data if d['metric_name'] == metric_name]
    
    if len(values) < 3:
        return {
            'metric': metric_name,
            'n': len(values),
            'correlation': 0.0,
            'p_value': 1.0,
            'significant': False
        }
    
    r, p = compute_correlation(values, scores)
    return {
        'metric': metric_name,
        'n': len(values),
        'correlation': r,
        'p_value': p,
        'significant': p < 0.05
    }

def run_multiple_linear_regression(data: List[Dict]) -> Dict[str, Any]:
    """Run multiple linear regression (placeholder for statsmodels)."""
    if not HAS_STATSMODELS:
        logger.warning("statsmodels not available. Returning placeholder regression results.")
        return {
            'coefficients': {'intercept': 0.0, 'metric': 0.0, 'age': 0.0, 'gender': 0.0},
            'r_squared': 0.0,
            'p_values': {'metric': 1.0, 'age': 1.0, 'gender': 1.0}
        }
    
    # Placeholder implementation
    return {
        'coefficients': {'intercept': 0.0, 'metric': 0.0, 'age': 0.0, 'gender': 0.0},
        'r_squared': 0.0,
        'p_values': {'metric': 1.0, 'age': 1.0, 'gender': 1.0}
    }

def calculate_power(n_subjects: int, effect_sizes: Optional[List[float]] = None) -> List[Dict[str, float]]:
    """
    Calculate statistical power for correlation tests given sample size and effect sizes.
    
    Args:
        n_subjects: Number of subjects (N)
        effect_sizes: List of effect sizes (Cohen's d or r) to evaluate. Defaults to [0.2, 0.5, 0.8]
    
    Returns:
        List of dicts containing effect_size, power, and alpha
    """
    if not HAS_STATSMODELS:
        logger.warning("statsmodels not installed. Cannot calculate power. Returning dummy results.")
        if effect_sizes is None:
            effect_sizes = [0.2, 0.5, 0.8]
        return [
            {'effect_size': es, 'power': 0.0, 'alpha': 0.05, 'note': 'statsmodels not installed'}
            for es in effect_sizes
        ]
    
    if effect_sizes is None:
        effect_sizes = [0.2, 0.5, 0.8]  # Small, medium, large effects
    
    results = []
    alpha = 0.05
    
    # For correlation, we can use TTestPower as an approximation or calculate manually
    # A more accurate approach for Pearson correlation power uses the non-central t-distribution
    # Here we use a standard approximation: power = 1 - beta
    
    power_calc = TTestIndPower()
    
    for es in effect_sizes:
        # For correlation, effect size r can be converted to Cohen's d: d = 2r / sqrt(1-r^2)
        # But TTestIndPower expects Cohen's d for two independent groups.
        # For a correlation test with continuous variables, we approximate power using the
        # non-centrality parameter lambda = r * sqrt(n-1)
        
        try:
            # Using TTestPower for one-sample or paired test as approximation
            # This is a simplification; ideally we'd use TTestPower with appropriate parameters
            # or statsmodels.stats.correlation_power
            power = power_calc.solve_power(effect_size=es, nobs1=n_subjects, alpha=alpha, ratio=1.0)
            # Clamp power to [0, 1]
            power = max(0.0, min(1.0, power))
        except Exception:
            # Fallback: manual approximation for correlation power
            # Power ~ Phi( sqrt(n-3) * 0.5 * ln((1+r)/(1-r)) - z_alpha )
            # where Phi is standard normal CDF, z_alpha is critical value
            if abs(es) < 1.0:
                z_alpha = 1.96  # for alpha=0.05 two-tailed
                # Fisher's z transformation
                z_r = 0.5 * math.log((1 + abs(es)) / (1 - abs(es)))
                se = 1.0 / math.sqrt(n_subjects - 3) if n_subjects > 3 else 1.0
                z_stat = z_r / se
                # Approximate power using normal CDF
                power = 0.5 * (1 + math.erf((z_stat - z_alpha) / math.sqrt(2)))
                power = max(0.0, min(1.0, power))
            else:
                power = 0.0
        
        results.append({
            'effect_size': es,
            'power': float(power),
            'alpha': alpha,
            'n_subjects': n_subjects
        })
    
    return results

def generate_power_analysis_table(power_results: List[Dict[str, float]]) -> str:
    """Generate a text table of power analysis results."""
    lines = []
    lines.append("Power Analysis Results (N=10):")
    lines.append("-" * 40)
    lines.append(f"{'Effect Size':<15} {'Power':<10} {'Alpha':<10}")
    lines.append("-" * 40)
    for res in power_results:
        lines.append(f"{res['effect_size']:<15.3f} {res['power']:<10.3f} {res['alpha']:<10.3f}")
    lines.append("-" * 40)
    return "\n".join(lines)

def create_limitations_text(n_subjects: int, power_results: List[Dict[str, float]]) -> str:
    """
    Create the mandatory limitations section text.
    
    Required text: "This study utilizes a sample size of N=10 subjects, which provides 
    low statistical power for detecting small effect sizes. Results should be interpreted 
    as exploratory and require validation in larger cohorts."
    """
    base_text = "This study utilizes a sample size of N=10 subjects, which provides low statistical power for detecting small effect sizes. Results should be interpreted as exploratory and require validation in larger cohorts."
    
    # Append power analysis summary
    summary_lines = ["", "Power Analysis Summary:", ""]
    for res in power_results:
        summary_lines.append(f"- Effect size {res['effect_size']:.2f}: Power = {res['power']:.2f}")
    
    return base_text + "\n" + "\n".join(summary_lines)

def generate_power_summary_table(power_results: List[Dict[str, float]]) -> str:
    """Generate a formatted summary table for the report."""
    lines = []
    lines.append("Statistical Power Analysis (Sample Size N=10)")
    lines.append("=" * 50)
    lines.append("")
    lines.append(generate_power_analysis_table(power_results))
    lines.append("")
    lines.append("Limitations:")
    lines.append("-" * 50)
    lines.append(create_limitations_text(10, power_results))
    return "\n".join(lines)

def append_limitations_section(report_path: str, limitations_text: str):
    """Append limitations section to the summary report (PDF or text)."""
    # If it's a PDF, we would need to use reportlab or similar to append
    # For this implementation, we assume the report is text-based or we append to a text file
    # In a real scenario, we'd modify the PDF generation in generate_summary_report.py
    
    # For now, we write to a separate text file that can be included in the PDF
    limitations_file = str(report_path).replace('.pdf', '_limitations.txt')
    with open(limitations_file, 'w') as f:
        f.write(limitations_text)
    
    logger.info(f"Limitations section written to {limitations_file}")
    
    # If the main report is text, append directly
    if report_path.endswith('.txt'):
        with open(report_path, 'a') as f:
            f.write("\n\n" + limitations_text)

def main():
    """Main entry point for stats analysis."""
    parser = argparse.ArgumentParser(description='Statistical analysis for brain network dynamics')
    parser.add_argument('--metrics', type=str, default='data/processed/graph_metrics.csv',
                      help='Path to graph metrics CSV')
    parser.add_argument('--behavioral', type=str, default='data/processed/behavioral.csv',
                      help='Path to behavioral scores CSV')
    parser.add_argument('--output', type=str, default='reports/',
                      help='Output directory for results')
    parser.add_argument('--n-subjects', type=int, default=10,
                      help='Number of subjects for power analysis')
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    try:
        # Load data
        metrics = load_graph_metrics(args.metrics)
        scores = load_behavioral_scores(args.behavioral)
        merged = merge_metrics_with_scores(metrics, scores)
        
        if not merged:
            logger.error("No valid data found for analysis. Check input files.")
            sys.exit(1)
        
        # Perform power analysis
        logger.info(f"Running power analysis for N={args.n_subjects} subjects...")
        power_results = calculate_power(args.n_subjects)
        
        # Generate power summary
        power_summary = generate_power_summary_table(power_results)
        power_file = os.path.join(args.output, 'power_analysis.txt')
        with open(power_file, 'w') as f:
            f.write(power_summary)
        logger.info(f"Power analysis saved to {power_file}")
        
        # Create limitations text
        limitations_text = create_limitations_text(args.n_subjects, power_results)
        
        # Append to summary report if it exists
        summary_report = os.path.join(args.output, 'summary.pdf')
        if os.path.exists(summary_report):
            # For PDF, we write to a separate file to be included
            limitations_pdf = os.path.join(args.output, 'summary_limitations.txt')
            with open(limitations_pdf, 'w') as f:
                f.write(limitations_text)
            logger.info(f"Limitations section written to {limitations_pdf}")
        else:
            # If no summary report yet, write limitations to a text file
            limitations_txt = os.path.join(args.output, 'limitations.txt')
            with open(limitations_txt, 'w') as f:
                f.write(limitations_text)
            logger.info(f"Limitations section written to {limitations_txt}")
        
        logger.info("Statistical analysis and power analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()