import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

from src.utils.config import get_config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class StatisticalAnalyzer:
    """
    Handles statistical analysis of experimental results, including:
    - Paired t-tests
    - Bonferroni/FDR correction
    - Ablation comparisons (Dialogue vs. Ablation vs. Static)
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.logger = logger

    def load_metrics_from_jsonl(
        self, file_path: Path, condition_name: str
    ) -> List[Dict[str, Any]]:
        """
        Load metrics from a JSONL file produced by training/evaluation.
        Expects each line to be a JSON object with at least 'accuracy' or 'score'.
        """
        metrics = []
        if not file_path.exists():
            self.logger.error(f"Metrics file not found: {file_path}")
            return metrics

        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    # Normalize key: look for 'accuracy', 'score', or 'metric'
                    value = record.get("accuracy") or record.get("score") or record.get("metric")
                    if value is None:
                        self.logger.warning(
                            f"No numeric metric found in {file_path} line {line_num}: {record}"
                        )
                        continue
                    metrics.append({"condition": condition_name, "value": float(value)})
                except json.JSONDecodeError as e:
                    self.logger.warning(
                        f"Invalid JSON in {file_path} line {line_num}: {e}"
                    )
        return metrics

    def perform_paired_ttest(
        self, group_a: List[float], group_b: List[float], alternative: str = "two-sided"
    ) -> Dict[str, Any]:
        """
        Perform a paired t-test between two groups of equal length.
        Returns dict with t-statistic, p-value, and confidence interval info.
        """
        if len(group_a) != len(group_b):
            raise ValueError(
                f"Group lengths must match for paired t-test: {len(group_a)} vs {len(group_b)}"
            )
        if len(group_a) < 2:
            raise ValueError("Need at least 2 samples for t-test")

        t_stat, p_val = stats.ttest_rel(group_a, group_b, alternative=alternative)
        mean_a = np.mean(group_a)
        mean_b = np.mean(group_b)
        diff = mean_a - mean_b

        return {
            "method": "paired_t_test",
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "mean_group_a": float(mean_a),
            "mean_group_b": float(mean_b),
            "mean_difference": float(diff),
            "sample_size": len(group_a),
        }

    def bonferroni_correction(self, p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
        """
        Apply Bonferroni correction to a list of p-values.
        Returns adjusted p-values and whether any are significant after correction.
        """
        n_tests = len(p_values)
        if n_tests == 0:
            return {
                "method": "bonferroni",
                "original_p_values": [],
                "adjusted_p_values": [],
                "corrected_alpha": alpha / 1 if n_tests == 0 else alpha / n_tests,
                "significant_count": 0,
            }

        corrected_alpha = alpha / n_tests
        adjusted = [min(p * n_tests, 1.0) for p in p_values]
        significant = [p < corrected_alpha for p in adjusted]

        return {
            "method": "bonferroni",
            "original_p_values": [float(p) for p in p_values],
            "adjusted_p_values": [float(p) for p in adjusted],
            "corrected_alpha": float(corrected_alpha),
            "significant_count": int(sum(significant)),
        }

    def fdr_correction(self, p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
        """
        Apply Benjamini-Hochberg FDR correction.
        """
        n_tests = len(p_values)
        if n_tests == 0:
            return {
                "method": "fdr_bh",
                "original_p_values": [],
                "adjusted_p_values": [],
                "corrected_alpha": alpha,
                "significant_count": 0,
            }

        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]
        ranks = np.arange(1, n_tests + 1)
        # BH adjusted p-values
        adjusted = np.minimum.accumulate((sorted_p * n_tests / ranks))[::-1]
        adjusted = np.minimum(adjusted, 1.0)

        # Restore original order
        final_adjusted = np.empty(n_tests)
        final_adjusted[sorted_indices] = adjusted

        significant = final_adjusted < alpha

        return {
            "method": "fdr_bh",
            "original_p_values": [float(p) for p in p_values],
            "adjusted_p_values": [float(p) for p in final_adjusted],
            "corrected_alpha": float(alpha),
            "significant_count": int(sum(significant)),
        }

    def compare_conditions(
        self,
        dialogue_metrics: List[float],
        ablation_metrics: List[float],
        static_metrics: List[float],
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Compare three conditions: Dialogue vs. Ablation vs. Static.
        Performs pairwise paired t-tests (assuming same seeds/indices) and
        applies Bonferroni correction for multiple comparisons.

        Returns a comprehensive result dictionary.
        """
        if not (
            len(dialogue_metrics) == len(ablation_metrics) == len(static_metrics)
        ):
            raise ValueError(
                "All condition metric lists must have equal length (paired design)."
            )
        if len(dialogue_metrics) < 2:
            raise ValueError("Need at least 2 samples per condition for t-test.")

        # Pairwise comparisons
        dialogue_vs_ablation = self.perform_paired_ttest(
            dialogue_metrics, ablation_metrics
        )
        dialogue_vs_static = self.perform_paired_ttest(
            dialogue_metrics, static_metrics
        )
        ablation_vs_static = self.perform_paired_ttest(
            ablation_metrics, static_metrics
        )

        p_values = [
            dialogue_vs_ablation["p_value"],
            dialogue_vs_static["p_value"],
            ablation_vs_static["p_value"],
        ]

        # Multiple comparison correction
        bonf_result = self.bonferroni_correction(p_values, alpha=alpha)
        fdr_result = self.fdr_correction(p_values, alpha=alpha)

        # Determine significance after Bonferroni
        dialogue_vs_ablation_sig = (
            dialogue_vs_ablation["p_value"] < bonf_result["corrected_alpha"]
        )
        dialogue_vs_static_sig = (
            dialogue_vs_static["p_value"] < bonf_result["corrected_alpha"]
        )
        ablation_vs_static_sig = (
            ablation_vs_static["p_value"] < bonf_result["corrected_alpha"]
        )

        return {
            "pairwise_tests": {
                "dialogue_vs_ablation": {
                    **dialogue_vs_ablation,
                    "significant_after_bonferroni": dialogue_vs_ablation_sig,
                },
                "dialogue_vs_static": {
                    **dialogue_vs_static,
                    "significant_after_bonferroni": dialogue_vs_static_sig,
                },
                "ablation_vs_static": {
                    **ablation_vs_static,
                    "significant_after_bonferroni": ablation_vs_static_sig,
                },
            },
            "multiple_comparison_correction": {
                "bonferroni": bonf_result,
                "fdr_bh": fdr_result,
            },
            "summary": {
                "n_seeds": len(dialogue_metrics),
                "mean_dialogue": float(np.mean(dialogue_metrics)),
                "mean_ablation": float(np.mean(ablation_metrics)),
                "mean_static": float(np.mean(static_metrics)),
                "std_dialogue": float(np.std(dialogue_metrics)),
                "std_ablation": float(np.std(ablation_metrics)),
                "std_static": float(np.std(static_metrics)),
            },
        }

    def run_ablation_comparison(
        self,
        dialogue_file: Path,
        ablation_file: Path,
        static_file: Path,
        output_file: Path,
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Main entry point for T031:
        Load metrics from three JSONL files (Dialogue, Ablation, Static),
        perform statistical comparison, and write results to output_file.

        Assumes each file contains one result per seed (paired design).
        """
        self.logger.info(f"Loading metrics from: {dialogue_file}, {ablation_file}, {static_file}")

        dialogue_data = self.load_metrics_from_jsonl(dialogue_file, "dialogue")
        ablation_data = self.load_metrics_from_jsonl(ablation_file, "ablation")
        static_data = self.load_metrics_from_jsonl(static_file, "static")

        if not dialogue_data or not ablation_data or not static_data:
            raise RuntimeError(
                "One or more metric files are empty or missing required fields."
            )

        # Extract values (assume same ordering/seeds)
        dialogue_vals = [d["value"] for d in dialogue_data]
        ablation_vals = [a["value"] for a in ablation_data]
        static_vals = [s["value"] for s in static_data]

        result = self.compare_conditions(
            dialogue_vals, ablation_vals, static_vals, alpha=alpha
        )

        # Write output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        self.logger.info(f"Statistical comparison results written to: {output_file}")
        return result


def main():
    """
    CLI entry point for ablation comparison (T031).
    Usage:
      python -m src.analyze.stats \
        --dialogue data/results/dialogue_metrics.jsonl \
        --ablation data/results/ablation_metrics.jsonl \
        --static data/results/static_metrics.jsonl \
        --output data/results/ablation_comparison.json
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run ablation comparison: Dialogue vs. Ablation vs. Static"
    )
    parser.add_argument(
        "--dialogue", type=Path, required=True, help="Path to Dialogue metrics JSONL"
    )
    parser.add_argument(
        "--ablation", type=Path, required=True, help="Path to Ablation metrics JSONL"
    )
    parser.add_argument(
        "--static", type=Path, required=True, help="Path to Static metrics JSONL"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results/ablation_comparison.json"),
        help="Output JSON path",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for multiple comparison correction",
    )

    args = parser.parse_args()

    analyzer = StatisticalAnalyzer()

    try:
        result = analyzer.run_ablation_comparison(
            dialogue_file=args.dialogue,
            ablation_file=args.ablation,
            static_file=args.static,
            output_file=args.output,
            alpha=args.alpha,
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.exception("Ablation comparison failed")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()