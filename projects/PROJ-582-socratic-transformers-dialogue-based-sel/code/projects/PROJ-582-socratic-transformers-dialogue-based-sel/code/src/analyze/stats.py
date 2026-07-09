"""
Statistical analysis module for Socratic Transformers project.

This module implements paired t-tests and multiple comparison corrections
to analyze performance differences between dialogue-based self-teaching
conditions and baseline methods.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats


class StatisticalAnalyzer:
    """Performs statistical analysis on benchmark results across multiple seeds."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the statistical analyzer.

        Args:
            config: Optional configuration dictionary. If None, uses defaults.
        """
        self.config = config or {}
        self.alpha = self.config.get('alpha', 0.05)
        self.correction_method = self.config.get('correction_method', 'bonferroni')

    def load_results_from_jsonl(
        self,
        file_path: str,
        condition_field: str = 'condition',
        metric_field: str = 'accuracy'
    ) -> Dict[str, List[float]]:
        """
        Load benchmark results from a JSONL file.

        Args:
            file_path: Path to the JSONL file containing results.
            condition_field: Field name for the experimental condition.
            metric_field: Field name for the metric value.

        Returns:
            Dictionary mapping condition names to lists of metric values.
        """
        results: Dict[str, List[float]] = {}

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                condition = record.get(condition_field, 'unknown')
                metric_value = record.get(metric_field)

                if metric_value is not None:
                    if condition not in results:
                        results[condition] = []
                    results[condition].append(float(metric_value))

        return results

    def paired_ttest(
        self,
        condition_a: List[float],
        condition_b: List[float]
    ) -> Dict[str, Any]:
        """
        Perform a paired t-test between two conditions.

        Args:
            condition_a: List of metric values for condition A.
            condition_b: List of metric values for condition B.

        Returns:
            Dictionary containing t-statistic, p-value, and effect size.
        """
        if len(condition_a) != len(condition_b):
            raise ValueError(
                f"Paired t-test requires equal sample sizes. "
                f"Got {len(condition_a)} for condition A and {len(condition_b)} for condition B."
            )

        if len(condition_a) < 2:
            raise ValueError(
                f"Paired t-test requires at least 2 samples per condition. "
                f"Got {len(condition_a)}."
            )

        # Convert to numpy arrays for calculation
        a = np.array(condition_a)
        b = np.array(condition_b)

        # Calculate paired differences
        differences = a - b

        # Perform paired t-test
        t_statistic, p_value = stats.ttest_rel(a, b)

        # Calculate effect size (Cohen's d for paired samples)
        mean_diff = np.mean(differences)
        std_diff = np.std(differences, ddof=1)
        cohens_d = mean_diff / std_diff if std_diff != 0 else 0.0

        return {
            't_statistic': float(t_statistic),
            'p_value': float(p_value),
            'mean_difference': float(mean_diff),
            'std_difference': float(std_diff),
            'cohens_d': float(cohens_d),
            'n_samples': len(condition_a),
            'method': 'paired_ttest'
        }

    def bonferroni_correction(
        self,
        p_values: List[float],
        num_tests: Optional[int] = None
    ) -> List[float]:
        """
        Apply Bonferroni correction to multiple p-values.

        Args:
            p_values: List of raw p-values.
            num_tests: Number of tests being corrected for. If None, uses len(p_values).

        Returns:
            List of corrected p-values.
        """
        if num_tests is None:
            num_tests = len(p_values)

        if num_tests == 0:
            return p_values

        corrected = [min(p * num_tests, 1.0) for p in p_values]
        return corrected

    def fdr_correction(
        self,
        p_values: List[float]
    ) -> List[float]:
        """
        Apply Benjamini-Hochberg FDR correction to multiple p-values.

        Args:
            p_values: List of raw p-values.

        Returns:
            List of corrected p-values.
        """
        n = len(p_values)
        if n == 0:
            return p_values

        # Sort p-values with their original indices
        sorted_indices = np.argsort(p_values)
        sorted_pvalues = np.array([p_values[i] for i in sorted_indices])

        # Calculate corrected p-values
        corrected = np.zeros(n)
        for i in range(n):
            rank = i + 1
            corrected[i] = min(sorted_pvalues[i] * n / rank, 1.0)

        # Ensure monotonicity (corrected p-values should be non-decreasing)
        for i in range(n - 2, -1, -1):
            corrected[i] = min(corrected[i], corrected[i + 1])

        # Restore original order
        final_corrected = np.zeros(n)
        for i, idx in enumerate(sorted_indices):
            final_corrected[idx] = corrected[i]

        return final_corrected.tolist()

    def run_analysis(
        self,
        results_file: str,
        benchmark_name: str,
        conditions: List[str],
        metric_field: str = 'accuracy'
    ) -> Dict[str, Any]:
        """
        Run statistical analysis on benchmark results.

        Args:
            results_file: Path to the JSONL file containing results.
            benchmark_name: Name of the benchmark being analyzed.
            conditions: List of condition names to compare (must be >= 2).
            metric_field: Field name for the metric value.

        Returns:
            Dictionary containing analysis results.
        """
        if len(conditions) < 2:
            raise ValueError("At least 2 conditions are required for comparison.")

        # Load results
        results = self.load_results_from_jsonl(
            results_file,
            condition_field='condition',
            metric_field=metric_field
        )

        # Validate all conditions are present
        for condition in conditions:
            if condition not in results:
                raise ValueError(f"Condition '{condition}' not found in results file.")
            if len(results[condition]) < 2:
                raise ValueError(
                    f"Condition '{condition}' has fewer than 2 samples "
                    f"(got {len(results[condition])})."
                )

        # Perform pairwise comparisons
        comparisons = []
        raw_p_values = []

        for i in range(len(conditions)):
            for j in range(i + 1, len(conditions)):
                cond_a = conditions[i]
                cond_b = conditions[j]

                result = self.paired_ttest(
                    results[cond_a],
                    results[cond_b]
                )
                result['condition_a'] = cond_a
                result['condition_b'] = cond_b

                comparisons.append(result)
                raw_p_values.append(result['p_value'])

        # Apply multiple comparison correction
        if self.correction_method == 'bonferroni':
            corrected_p_values = self.bonferroni_correction(raw_p_values)
        elif self.correction_method == 'fdr':
            corrected_p_values = self.fdr_correction(raw_p_values)
        else:
            corrected_p_values = raw_p_values

        # Update comparisons with corrected p-values
        for idx, comparison in enumerate(comparisons):
            comparison['corrected_p_value'] = corrected_p_values[idx]
            comparison['is_significant'] = corrected_p_values[idx] < self.alpha

        return {
            'benchmark': benchmark_name,
            'alpha': self.alpha,
            'correction_method': self.correction_method,
            'corrected_alpha': self.alpha / len(raw_p_values) if self.correction_method == 'bonferroni' else self.alpha,
            'num_comparisons': len(comparisons),
            'comparisons': comparisons,
            'conditions': conditions,
            'sample_sizes': {cond: len(results[cond]) for cond in conditions}
        }


def main():
    """
    Main entry point for the statistical analysis script.

    This script loads benchmark results from JSONL files and performs
    paired t-tests with multiple comparison correction.
    """
    # Default paths
    results_dir = Path(__file__).parent.parent.parent / 'data' / 'results'
    results_file = results_dir / 'benchmark_results.jsonl'

    # Check if results file exists
    if not results_file.exists():
        print(f"Error: Results file not found at {results_file}")
        print("Please run the benchmark script first to generate results.")
        sys.exit(1)

    # Initialize analyzer
    analyzer = StatisticalAnalyzer({
        'alpha': 0.05,
        'correction_method': 'bonferroni'
    })

    # Define conditions to compare
    # These should match the conditions generated by the data generation and training pipelines
    conditions = ['dialogue', 'static', 'ablation']

    # Run analysis for each benchmark
    benchmarks = ['gsm8k', 'mmlu_stem']
    all_results = {}

    for benchmark in benchmarks:
        print(f"\n{'='*60}")
        print(f"Analyzing {benchmark.upper()} benchmark")
        print(f"{'='*60}")

        try:
            # For this implementation, we assume a single results file contains
            # all benchmarks. In a real scenario, you might have separate files
            # or filter by a benchmark field.
            analysis_result = analyzer.run_analysis(
                results_file=str(results_file),
                benchmark_name=benchmark,
                conditions=conditions
            )

            all_results[benchmark] = analysis_result

            # Print results
            print(f"\nBenchmark: {benchmark}")
            print(f"Conditions: {', '.join(conditions)}")
            print(f"Alpha: {analysis_result['alpha']}")
            print(f"Correction method: {analysis_result['correction_method']}")
            print(f"Corrected alpha: {analysis_result['corrected_alpha']:.4f}")
            print(f"Number of comparisons: {analysis_result['num_comparisons']}")

            for comp in analysis_result['comparisons']:
                print(f"\n  {comp['condition_a']} vs {comp['condition_b']}:")
                print(f"    T-statistic: {comp['t_statistic']:.4f}")
                print(f"    Raw p-value: {comp['p_value']:.4f}")
                print(f"    Corrected p-value: {comp['corrected_p_value']:.4f}")
                print(f"    Mean difference: {comp['mean_difference']:.4f}")
                print(f"    Cohen's d: {comp['cohens_d']:.4f}")
                print(f"    Significant (α={analysis_result['alpha']}): {comp['is_significant']}")

        except ValueError as e:
            print(f"Warning: Could not analyze {benchmark}: {e}")
            all_results[benchmark] = {'error': str(e)}

    # Save results to JSON
    output_file = results_dir / 'statistical_analysis_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Analysis complete. Results saved to {output_file}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()