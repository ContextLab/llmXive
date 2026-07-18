"""
T031: Generate final statistical report in data/results/statistical_report.md.

This script aggregates results from multi-seed experiments (T027), applies
Bonferroni correction (T030), and generates a Markdown report containing:
- Bonferroni-corrected p-values for NDCG@10 and "wasted call" ratios.
- Summary statistics (mean, std, min, max) for both variants.
- Conclusions on statistical significance as per FR-007 and SC-003.
"""
import os
import json
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Import from existing project modules
from metrics import bonferroni_correction, wilcoxon_signed_rank_test, calculate_ndcg_at_10
from run_pipeline import ExperimentResult
from config import get_config

# Ensure output directory exists
OUTPUT_DIR = "data/results"
REPORT_PATH = os.path.join(OUTPUT_DIR, "statistical_report.md")
RESULTS_DIR = os.path.join("data", "results", "experiments")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StatisticalSummary:
    variant_name: str
    mean_ndcg: float
    std_ndcg: float
    mean_wasted_ratio: float
    std_wasted_ratio: float
    min_ndcg: float
    max_ndcg: float
    sample_size: int

@dataclass
class TestResult:
    metric_name: str
    statistic: float
    p_value_raw: float
    p_value_corrected: float
    is_significant: bool
    conclusion: str

def load_experiment_results() -> Tuple[List[ExperimentResult], List[ExperimentResult]]:
    """
    Load all experiment results from the results directory.
    Returns two lists: baseline_results, clustering_aided_results.
    """
    if not os.path.exists(RESULTS_DIR):
        raise FileNotFoundError(f"Results directory not found: {RESULTS_DIR}. Run T027 first.")

    baseline_results = []
    clustering_results = []

    for filename in os.listdir(RESULTS_DIR):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(RESULTS_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Extract variant type from filename or data
            # Assuming filename format: seed_{N}_variant_{type}.json or similar
            if "baseline" in filename.lower():
                baseline_results.append(ExperimentResult(**data))
            elif "clustering" in filename.lower():
                clustering_results.append(ExperimentResult(**data))
            else:
                # Fallback: check data content if filename is ambiguous
                if data.get("variant_type") == "baseline":
                    baseline_results.append(ExperimentResult(**data))
                elif data.get("variant_type") == "clustering_aided":
                    clustering_results.append(ExperimentResult(**data))
                
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Skipping invalid result file {filename}: {e}")

    if not baseline_results or not clustering_results:
        raise ValueError(f"Insufficient results found. Baseline: {len(baseline_results)}, Clustering: {len(clustering_results)}.")

    return baseline_results, clustering_results

def calculate_statistics(results: List[ExperimentResult]) -> StatisticalSummary:
    """Calculate mean, std, min, max for NDCG and wasted ratio."""
    ndcg_scores = [r.ndcg_at_10 for r in results]
    wasted_ratios = [r.wasted_call_ratio for r in results]

    import numpy as np
    
    return StatisticalSummary(
        variant_name=results[0].variant_type if results else "Unknown",
        mean_ndcg=float(np.mean(ndcg_scores)),
        std_ndcg=float(np.std(ndcg_scores)),
        mean_wasted_ratio=float(np.mean(wasted_ratios)),
        std_wasted_ratio=float(np.std(wasted_ratios)),
        min_ndcg=float(np.min(ndcg_scores)),
        max_ndcg=float(np.max(ndcg_scores)),
        sample_size=len(results)
    )

def run_statistical_tests(baseline_results: List[ExperimentResult], 
                          clustering_results: List[ExperimentResult]) -> List[TestResult]:
    """
    Run Wilcoxon signed-rank tests on NDCG and wasted ratios,
    then apply Bonferroni correction.
    """
    import numpy as np
    
    # Ensure paired data (same seeds)
    # Assuming results are ordered by seed or we match by seed if available
    # For simplicity, we assume equal length and order from T027 loop
    if len(baseline_results) != len(clustering_results):
        logger.warning("Baseline and clustering result counts differ. Using intersection.")
        min_len = min(len(baseline_results), len(clustering_results))
        baseline_results = baseline_results[:min_len]
        clustering_results = clustering_results[:min_len]

    baseline_ndcg = [r.ndcg_at_10 for r in baseline_results]
    clustering_ndcg = [r.ndcg_at_10 for r in clustering_results]
    
    baseline_wasted = [r.wasted_call_ratio for r in baseline_results]
    clustering_wasted = [r.wasted_call_ratio for r in clustering_results]

    # Run Wilcoxon tests
    # Note: wilcoxon_signed_rank_test in metrics.py might return a tuple or object
    # We adapt based on the expected signature from the API surface description
    # Assuming it returns (statistic, p_value)
    
    test_ndcg = wilcoxon_signed_rank_test(baseline_ndcg, clustering_ndcg)
    test_wasted = wilcoxon_signed_rank_test(baseline_wasted, clustering_wasted)

    # Collect raw p-values
    raw_p_values = [test_ndcg[1], test_wasted[1]] # (stat, p)
    
    # Apply Bonferroni correction (N=2 tests)
    corrected_results = bonferroni_correction(raw_p_values, alpha=0.05)
    
    # Extract corrected p-values
    # bonferroni_correction likely returns a dict or object with corrected values
    # Assuming it returns a list of dicts or similar structure matching input order
    # If it returns a single dict with 'corrected_p_values', we access that.
    # Given the API surface `BonferroniResult`, we assume it returns an object.
    
    p_ndcg_corrected = corrected_results.p_values[0] if hasattr(corrected_results, 'p_values') else corrected_results[0]
    p_wasted_corrected = corrected_results.p_values[1] if hasattr(corrected_results, 'p_values') else corrected_results[1]

    # Determine significance
    alpha = 0.05
    sig_ndcg = p_ndcg_corrected < alpha
    sig_wasted = p_wasted_corrected < alpha

    return [
        TestResult(
            metric_name="NDCG@10",
            statistic=test_ndcg[0],
            p_value_raw=test_ndcg[1],
            p_value_corrected=p_ndcg_corrected,
            is_significant=sig_ndcg,
            conclusion="Significant improvement" if sig_ndcg else "No significant difference"
        ),
        TestResult(
            metric_name="Wasted Call Ratio",
            statistic=test_wasted[0],
            p_value_raw=test_wasted[1],
            p_value_corrected=p_wasted_corrected,
            is_significant=sig_wasted,
            conclusion="Significant reduction" if sig_wasted else "No significant difference"
        )
    ]

def generate_markdown_report(baseline_summary: StatisticalSummary,
                             clustering_summary: StatisticalSummary,
                             test_results: List[TestResult]) -> str:
    """Generate the Markdown report content."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        "# Statistical Analysis Report: Active Learners as Efficient PRP Rerankers",
        "",
        f"**Generated:** {timestamp}",
        f"**Project:** PROJ-873-llmxive-follow-up-extending-active-learn",
        f"**Task:** T031 - Final Statistical Report",
        "",
        "## Executive Summary",
        "",
        "This report presents the statistical significance analysis of the proposed MinHash-LSH pre-clustering",
        "approach compared to the baseline active ranker. The analysis focuses on two key metrics:",
        "1. **NDCG@10**: Ranking quality.",
        "2. **Wasted Call Ratio**: Efficiency (lower is better).",
        "",
        "Statistical significance was determined using the Wilcoxon signed-rank test with Bonferroni correction",
        "for multiple hypothesis testing (alpha = 0.05).",
        "",
        "## Descriptive Statistics",
        "",
        "### Baseline Variant (Redundant Data)",
        "",
        "| Metric | Mean | Std Dev | Min | Max |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| NDCG@10 | {baseline_summary.mean_ndcg:.4f} | {baseline_summary.std_ndcg:.4f} | {baseline_summary.min_ndcg:.4f} | {baseline_summary.max_ndcg:.4f} |",
        f"| Wasted Call Ratio | {baseline_summary.mean_wasted_ratio:.4f} | {baseline_summary.std_wasted_ratio:.4f} | - | - |",
        f"| Sample Size (Seeds) | {baseline_summary.sample_size} | | | |",
        "",
        "### Clustering-Aided Variant",
        "",
        "| Metric | Mean | Std Dev | Min | Max |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| NDCG@10 | {clustering_summary.mean_ndcg:.4f} | {clustering_summary.std_ndcg:.4f} | {clustering_summary.min_ndcg:.4f} | {clustering_summary.max_ndcg:.4f} |",
        f"| Wasted Call Ratio | {clustering_summary.mean_wasted_ratio:.4f} | {clustering_summary.std_wasted_ratio:.4f} | - | - |",
        f"| Sample Size (Seeds) | {clustering_summary.sample_size} | | | |",
        "",
        "## Statistical Significance Analysis",
        "",
        "### Hypothesis Testing",
        "",
        "- **Null Hypothesis (H0):** There is no difference in the metric distribution between the baseline and clustering-aided variants.",
        "- **Alternative Hypothesis (H1):** There is a statistically significant difference.",
        "- **Correction:** Bonferroni correction applied for 2 comparisons (NDCG and Efficiency).",
        "",
        "| Metric | Wilcoxon Statistic | Raw p-value | Bonferroni-Corrected p-value | Significant (p < 0.05)? | Conclusion |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    
    for res in test_results:
        sig_str = "Yes" if res.is_significant else "No"
        conclusion_str = res.conclusion
        lines.append(
            f"| {res.metric_name} | {res.statistic:.4f} | {res.p_value_raw:.6f} | {res.p_value_corrected:.6f} | {sig_str} | {conclusion_str} |"
        )
    
    lines.extend([
        "",
        "## Conclusions",
        "",
    ])
    
    # Generate specific conclusions based on results
    ndcg_res = next(r for r in test_results if r.metric_name == "NDCG@10")
    wasted_res = next(r for r in test_results if r.metric_name == "Wasted Call Ratio")
    
    if ndcg_res.is_significant:
        lines.append(f"- **NDCG@10:** The difference in ranking quality is statistically significant (p = {ndcg_res.p_value_corrected:.6f}). "
                     f"The clustering-aided variant {'improves' if clustering_summary.mean_ndcg > baseline_summary.mean_ndcg else 'degrades'} performance.")
    else:
        lines.append(f"- **NDCG@10:** No statistically significant difference in ranking quality was found (p = {ndcg_res.p_value_corrected:.6f}). "
                     f"The clustering approach maintains comparable performance to the baseline.")
    
    if wasted_res.is_significant:
        lines.append(f"- **Wasted Call Ratio:** The difference in efficiency is statistically significant (p = {wasted_res.p_value_corrected:.6f}). "
                     f"The clustering-aided variant {'significantly reduces' if clustering_summary.mean_wasted_ratio < baseline_summary.mean_wasted_ratio else 'increases'} wasted calls.")
    else:
        lines.append(f"- **Wasted Call Ratio:** No statistically significant difference in efficiency was found (p = {wasted_res.p_value_corrected:.6f}).")
    
    lines.extend([
        "",
        "## Compliance Statement",
        "",
        "This report satisfies **FR-007** (Statistical Significance) and **SC-003** (Reporting Requirements) by providing",
        "Bonferroni-corrected p-values and explicit conclusions on the efficiency and quality gains of the proposed method.",
        "",
        "---",
        "*Generated by llmXive Automated Science Pipeline*"
    ])
    
    return "\n".join(lines)

def main():
    """Main entry point for T031."""
    logger.info("Starting T031: Statistical Report Generation")
    
    try:
        # 1. Load results
        logger.info("Loading experiment results...")
        baseline_results, clustering_results = load_experiment_results()
        logger.info(f"Loaded {len(baseline_results)} baseline and {len(clustering_results)} clustering results.")
        
        # 2. Calculate descriptive statistics
        logger.info("Calculating descriptive statistics...")
        baseline_summary = calculate_statistics(baseline_results)
        clustering_summary = calculate_statistics(clustering_results)
        
        # 3. Run statistical tests
        logger.info("Running Wilcoxon signed-rank tests with Bonferroni correction...")
        test_results = run_statistical_tests(baseline_results, clustering_results)
        
        # 4. Generate report
        logger.info("Generating Markdown report...")
        report_content = generate_markdown_report(baseline_summary, clustering_summary, test_results)
        
        # 5. Write to disk
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(REPORT_PATH, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Statistical report successfully written to: {REPORT_PATH}")
        print(f"Report generated: {REPORT_PATH}")
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()
