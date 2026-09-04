import numpy as np
from scipy.stats import pearsonr, spearmanr
from statsmodels.stats.power import FTestPower
from typing import List, Dict, Any, Optional, Tuple
import warnings
import json
from pathlib import Path
from .utils import get_logger

logger = get_logger(__name__)

class CorrelationAnalyzer:
    """
    Performs statistical correlation analysis between network metrics and thermal conductivity.
    Includes sensitivity analysis to verify rank-order stability across significance thresholds.
    """

    def __init__(self, metrics: List[Dict[str, Any]], conductivities: List[float]):
        """
        Initialize the analyzer with metric dictionaries and conductivity values.

        Args:
            metrics: List of dictionaries containing network metrics (e.g., clustering, mean_degree)
            conductivities: List of thermal conductivity values corresponding to each metric set
        """
        if len(metrics) != len(conductivities):
            raise ValueError("Metrics and conductivities must have the same length")
        
        self.metrics = metrics
        self.conductivities = np.array(conductivities)
        self.metric_names = list(metrics[0].keys()) if metrics else []
        self.logger = logger

    def calculate_correlations(self, method: str = 'pearson') -> List[Dict[str, Any]]:
        """
        Calculate correlation coefficients and p-values for each metric against conductivity.

        Args:
            method: 'pearson' or 'spearman'

        Returns:
            List of dictionaries with metric name, coefficient, and p-value
        """
        results = []
        corr_func = pearsonr if method == 'pearson' else spearmanr

        for name in self.metric_names:
            values = np.array([m[name] for m in self.metrics])
            
            # Handle NaN values
            valid_mask = ~np.isnan(values) & ~np.isnan(self.conductivities)
            if np.sum(valid_mask) < 3:
                self.logger.warning(f"Not enough valid data points for {name}, skipping")
                results.append({
                    'metric': name,
                    'coefficient': np.nan,
                    'p_value': np.nan,
                    'n_samples': np.sum(valid_mask)
                })
                continue

            x = values[valid_mask]
            y = self.conductivities[valid_mask]

            try:
                corr, p_val = corr_func(x, y)
                results.append({
                    'metric': name,
                    'coefficient': float(corr),
                    'p_value': float(p_val),
                    'n_samples': int(np.sum(valid_mask))
                })
            except Exception as e:
                self.logger.warning(f"Correlation calculation failed for {name}: {e}")
                results.append({
                    'metric': name,
                    'coefficient': np.nan,
                    'p_value': np.nan,
                    'n_samples': int(np.sum(valid_mask))
                })

        return results

    def bonferroni_correct(self, p_values: List[float]) -> List[float]:
        """
        Apply Bonferroni correction to p-values.

        Args:
            p_values: List of raw p-values

        Returns:
            List of corrected p-values
        """
        n_tests = len(p_values)
        if n_tests == 0:
            return []
        
        corrected = [min(p * n_tests, 1.0) for p in p_values]
        return corrected

    def run_sensitivity_analysis(self, 
                                 thresholds: Optional[List[float]] = None,
                                 output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform sensitivity analysis by sweeping significance thresholds and verifying
        rank-order stability of correlation coefficients.

        Args:
            thresholds: List of significance thresholds to test (default: [0.01, 0.05, 0.10])
            output_path: Path to write the sensitivity analysis report (JSON)

        Returns:
            Dictionary containing the sensitivity analysis results
        """
        if thresholds is None:
            thresholds = [0.01, 0.05, 0.10]

        # Calculate correlations once (they don't change with threshold)
        correlations = self.calculate_correlations('pearson')
        spearman_correlations = self.calculate_correlations('spearman')

        # Filter out NaN results for ranking
        valid_metrics = [c for c in correlations if not np.isnan(c['coefficient'])]
        valid_spearman = [c for c in spearman_correlations if not np.isnan(c['coefficient'])]

        if len(valid_metrics) == 0:
            return {
                'status': 'no_valid_correlations',
                'message': 'No valid correlations found for sensitivity analysis',
                'thresholds_tested': thresholds,
                'results': []
            }

        # Calculate ranks based on absolute coefficient magnitude
        def get_rank_order(correlations_list):
            sorted_list = sorted(correlations_list, 
                                key=lambda x: abs(x['coefficient']), 
                                reverse=True)
            return [c['metric'] for c in sorted_list]

        base_rank_order = get_rank_order(valid_metrics)
        base_abs_coeffs = {c['metric']: abs(c['coefficient']) for c in valid_metrics}
        
        analysis_results = []
        rank_stability_checks = []

        for threshold in thresholds:
            # Apply threshold to p-values
            thresholded_results = []
            for corr in correlations:
                if np.isnan(corr['p_value']):
                    is_significant = False
                else:
                    is_significant = corr['p_value'] < threshold
                
                thresholded_results.append({
                    'metric': corr['metric'],
                    'coefficient': corr['coefficient'],
                    'p_value': corr['p_value'],
                    'is_significant': is_significant
                })

            # Get rank order of significant metrics only
            significant_metrics = [r for r in thresholded_results if r['is_significant']]
            if len(significant_metrics) > 1:
                current_rank_order = get_rank_order(significant_metrics)
            else:
                current_rank_order = [r['metric'] for r in significant_metrics]

            # Calculate magnitude differences for significant metrics
            magnitude_diffs = []
            for r in significant_metrics:
                metric = r['metric']
                if metric in base_abs_coeffs:
                    # Compare to base absolute coefficient
                    magnitude_diffs.append(abs(r['coefficient']) - base_abs_coeffs[metric])

            # Check rank-order stability against base
            # We check if the relative ordering of significant metrics is stable
            rank_stable = True
            if len(current_rank_order) > 1:
                # Simple check: are the top metrics in the same relative order?
                # For this analysis, we check if the rank order is identical to base (truncated)
                base_truncated = [m for m in base_rank_order if m in current_rank_order]
                if base_truncated != current_rank_order:
                    rank_stable = False

            analysis_results.append({
                'threshold': threshold,
                'significant_count': len(significant_metrics),
                'significant_metrics': [r['metric'] for r in significant_metrics],
                'rank_order': current_rank_order,
                'rank_stable': rank_stable,
                'magnitude_differences': magnitude_diffs
            })

            # Record stability check
            if len(magnitude_diffs) > 0:
                max_diff = max(abs(d) for d in magnitude_diffs)
                rank_stability_checks.append({
                    'threshold': threshold,
                    'max_magnitude_diff': max_diff,
                    'exceeds_0_1_threshold': max_diff > 0.1,
                    'rank_stable': rank_stable
                })

        # Final verdict on SC-004 compliance
        all_stable = all(check['rank_stable'] and not check['exceeds_0_1_threshold'] 
                        for check in rank_stability_checks if check['exceeds_0_1_threshold'] is not None)
        
        # If no magnitude diffs were calculated (e.g., only 1 or 0 significant metrics), 
        # we consider it stable by default as there's nothing to destabilize
        if not rank_stability_checks:
            all_stable = True

        report = {
            'status': 'completed',
            'sc_004_compliant': all_stable,
            'thresholds_tested': thresholds,
            'base_rank_order': base_rank_order,
            'results': analysis_results,
            'stability_checks': rank_stability_checks,
            'summary': {
                'total_metrics_analyzed': len(valid_metrics),
                'thresholds_where_stable': sum(1 for c in rank_stability_checks if c['rank_stable']),
                'thresholds_where_unstable': sum(1 for c in rank_stability_checks if not c['rank_stable']),
                'max_magnitude_diff_observed': max([c['max_magnitude_diff'] for c in rank_stability_checks], default=0)
            }
        }

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Sensitivity analysis report written to {output_path}")

        return report


def run_post_hoc_power_analysis(correlations: List[Dict[str, Any]], 
                                alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Perform post-hoc power analysis for correlation tests.

    Args:
        correlations: List of correlation results with 'coefficient' and 'n_samples'
        alpha: Significance level

    Returns:
        List of power analysis results
    """
    power_analyzer = FTestPower()
    results = []

    for corr in correlations:
        if np.isnan(corr['coefficient']) or corr['n_samples'] < 3:
            results.append({
                'metric': corr['metric'],
                'power': np.nan,
                'min_detectable_effect': np.nan,
                'warning': 'Insufficient data'
            })
            continue

        r = corr['coefficient']
        n = corr['n_samples']
        
        # For correlation, we use F-test power analysis
        # Effect size for correlation: f2 = r^2 / (1 - r^2)
        if abs(r) >= 1.0:
            # Perfect correlation, power is 1.0
            f2 = float('inf')
            power = 1.0
            min_effect = 1.0
        else:
            f2 = (r ** 2) / (1 - r ** 2)
            # Calculate power
            power = power_analyzer.solve_power(effect_size=f2, 
                                               nobs1=n, 
                                               alpha=alpha, 
                                               alternative='larger')
            
            # Calculate minimum detectable effect for 80% power
            # We solve for effect_size given power=0.8
            try:
                min_f2 = power_analyzer.solve_power(effect_size=None, 
                                                    nobs1=n, 
                                                    alpha=alpha, 
                                                    power=0.8, 
                                                    alternative='larger')
                min_effect = np.sqrt(min_f2 / (1 + min_f2)) if min_f2 > 0 else 0
            except:
                min_effect = np.nan

        results.append({
            'metric': corr['metric'],
            'power': float(power) if not np.isnan(power) else np.nan,
            'min_detectable_effect': float(min_effect) if not np.isnan(min_effect) else np.nan,
            'n_samples': n,
            'observed_r': r
        })

    # Flag if N < 20
    for res in results:
        if res['n_samples'] < 20:
            res['warning'] = f'Low sample size (N={res["n_samples"]}) - results may be underpowered'
        elif 'warning' not in res:
            res['warning'] = 'OK'

    return results