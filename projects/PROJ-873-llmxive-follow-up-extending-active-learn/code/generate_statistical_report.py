import os
import json
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from metrics import wilcoxon_signed_rank_test, bonferroni_correction, StatisticalDegeneracyWarning
from config import get_config

logger = logging.getLogger(__name__)

@dataclass
class StatisticalSummary:
    ndcg_scores_baseline: List[float]
    ndcg_scores_clustering: List[float]
    wasted_ratios_baseline: List[float]
    wasted_ratios_clustering: List[float]
    wilcoxon_ndcg: Dict[str, Any]
    wilcoxon_wasted: Dict[str, Any]
    bonferroni_corrected: List[Dict[str, Any]]

@dataclass
class TestResult:
    test_name: str
    pvalue: float
    corrected_pvalue: float
    significant: bool

def load_experiment_results(baseline_path: str, clustering_path: str) -> Dict[str, Any]:
    """Load experiment results from JSON files."""
    with open(baseline_path, "r") as f:
        baseline_results = json.load(f)
    with open(clustering_path, "r") as f:
        clustering_results = json.load(f)
    return {
        "baseline": baseline_results,
        "clustering": clustering_results
    }

def calculate_statistics(results: Dict[str, Any]) -> StatisticalSummary:
    """Calculate statistical summaries from results."""
    ndcg_baseline = [r.get("ndcg_at_10", 0.0) for r in results["baseline"]]
    ndcg_clustering = [r.get("ndcg_at_10", 0.0) for r in results["clustering"]]
    wasted_baseline = [r.get("wasted_ratio", 0.0) for r in results["baseline"]]
    wasted_clustering = [r.get("wasted_ratio", 0.0) for r in results["clustering"]]

    wilcoxon_ndcg = wilcoxon_signed_rank_test(ndcg_baseline, ndcg_clustering)
    wilcoxon_wasted = wilcoxon_signed_rank_test(wasted_baseline, wasted_clustering)

    p_values = [wilcoxon_ndcg["pvalue"], wilcoxon_wasted["pvalue"]]
    bonferroni_corrected = bonferroni_correction(p_values)

    return StatisticalSummary(
        ndcg_scores_baseline=ndcg_baseline,
        ndcg_scores_clustering=ndcg_clustering,
        wasted_ratios_baseline=wasted_baseline,
        wasted_ratios_clustering=wasted_clustering,
        wilcoxon_ndcg=wilcoxon_ndcg,
        wilcoxon_wasted=wilcoxon_wasted,
        bonferroni_corrected=bonferroni_corrected
    )

def run_statistical_tests() -> Dict[str, Any]:
    """Run statistical tests on experiment results."""
    config = get_config()
    baseline_path = os.path.join(config.data_dir, "data/results/us1_baseline_metrics.json")
    clustering_path = os.path.join(config.data_dir, "data/results/us2_baseline_095.json")

    if not os.path.exists(baseline_path) or not os.path.exists(clustering_path):
        logger.warning("Experiment results not found. Skipping statistical tests.")
        return {}

    results = load_experiment_results(baseline_path, clustering_path)
    summary = calculate_statistics(results)

    return asdict(summary)

def generate_markdown_report(summary: StatisticalSummary) -> str:
    """Generate a markdown report from statistical summary."""
    report = f"""
# Statistical Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## NDCG@10 Scores

- Baseline: {summary.ndcg_scores_baseline}
- Clustering-Aided: {summary.ndcg_scores_clustering}

## Wasted Call Ratios

- Baseline: {summary.wasted_ratios_baseline}
- Clustering-Aided: {summary.wasted_ratios_clustering}

## Wilcoxon Signed-Rank Test

### NDCG@10
- Statistic: {summary.wilcoxon_ndcg.get('statistic', 'N/A')}
- P-value: {summary.wilcoxon_ndcg.get('pvalue', 'N/A')}
- Degeneracy Warning: {summary.wilcoxon_ndcg.get('degeneracy_warning', False)}

### Wasted Ratio
- Statistic: {summary.wilcoxon_wasted.get('statistic', 'N/A')}
- P-value: {summary.wilcoxon_wasted.get('pvalue', 'N/A')}
- Degeneracy Warning: {summary.wilcoxon_wasted.get('degeneracy_warning', False)}

## Bonferroni-Corrected P-values

"""
    for i, corrected in enumerate(summary.bonferroni_corrected):
        test_name = "NDCG@10" if i == 0 else "Wasted Ratio"
        report += f"- {test_name}: {corrected['corrected_pvalue']} (Significant: {corrected['significant']})\n"

    return report

def main():
    config = get_config()
    output_path = os.path.join(config.data_dir, "data/results/statistical_report.md")

    summary = run_statistical_tests()
    if not summary:
        logger.warning("No statistical summary generated. Skipping report.")
        return

    report = generate_markdown_report(asdict(summary))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)

    logger.info(f"Statistical report saved to {output_path}")

if __name__ == "__main__":
    main()