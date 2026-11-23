"""
Report Generator Module for PROJ-263.

Generates the aggregate report (outputs/aggregate_report.md) summarizing
coverage rates across multiple UCI datasets, applying Bonferroni correction,
and explicitly contrasting the scope of real data against synthetic approaches.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import get_output_dir, get_processed_data_dir, get_random_seed
from aggregation import (
    load_coverage_records,
    load_population_means,
    calculate_mean_deviation,
    apply_bonferroni_correction,
    is_practically_significant,
    create_aggregate_report,
    save_aggregate_report,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_aggregate_report(output_dir: Optional[Path] = None) -> str:
    """
    Generate the aggregate report markdown file.

    This function:
    1. Loads coverage records from data/processed/coverage_records.json
    2. Loads population means from data/processed/population_means.json
    3. Calculates mean deviations from nominal coverage (95%)
    4. Applies Bonferroni correction for multiple comparisons
    5. Flags practically significant deviations (>1.0%)
    6. Generates a markdown report contrasting real UCI results with synthetic approaches

    Args:
        output_dir: Optional override for output directory. Defaults to project output dir.

    Returns:
        Path to the generated report file as a string.
    """
    if output_dir is None:
        output_dir = get_output_dir()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading coverage records from {get_processed_data_dir()}")
    coverage_records = load_coverage_records()

    if not coverage_records:
        logger.error("No coverage records found. Cannot generate report.")
        raise ValueError("No coverage records found. Run simulation first.")

    logger.info(f"Loaded {len(coverage_records)} coverage records")

    logger.info(f"Loading population means from {get_processed_data_dir()}")
    population_means = load_population_means()

    # Aggregate by dataset, sample size, and interval type
    # Structure: {dataset_id: {sample_size: {interval_type: [records]}}}
    aggregated_data: Dict[str, Dict[str, Dict[str, List[Any]]]] = {}

    for record in coverage_records:
        dataset_id = record['dataset_id']
        sample_size = record['sample_size']
        interval_type = record['interval_type']

        if dataset_id not in aggregated_data:
            aggregated_data[dataset_id] = {}
        if sample_size not in aggregated_data[dataset_id]:
            aggregated_data[dataset_id][sample_size] = {}
        if interval_type not in aggregated_data[dataset_id][sample_size]:
            aggregated_data[dataset_id][sample_size][interval_type] = []

        aggregated_data[dataset_id][sample_size][interval_type].append(record)

    # Calculate statistics for each combination
    report_data = []

    for dataset_id in sorted(aggregated_data.keys()):
        for sample_size in sorted(aggregated_data[dataset_id].keys(), key=int):
            for interval_type in aggregated_data[dataset_id][sample_size]:
                records = aggregated_data[dataset_id][sample_size][interval_type]

                # Calculate coverage rate
                total = len(records)
                covered = sum(1 for r in records if r['contains_mean'])
                coverage_rate = covered / total if total > 0 else 0.0

                # Calculate mean deviation from nominal (95%)
                nominal_coverage = 0.95
                deviation = coverage_rate - nominal_coverage

                # Check practical significance
                is_sig = is_practically_significant(deviation)

                # Bonferroni correction will be applied at the report level
                # based on the total number of tests (datasets * sample sizes * interval types)

                report_data.append({
                    'dataset_id': dataset_id,
                    'sample_size': int(sample_size),
                    'interval_type': interval_type,
                    'total_replications': total,
                    'coverage_rate': coverage_rate,
                    'deviation': deviation,
                    'is_practically_significant': is_sig
                })

    # Apply Bonferroni correction across all tests
    num_tests = len(report_data)
    if num_tests == 0:
        logger.warning("No tests to correct. Cannot apply Bonferroni.")
        return str(output_dir / "aggregate_report.md")

    corrected_results = apply_bonferroni_correction(report_data, num_tests)

    # Create aggregate report structure
    aggregate_report = create_aggregate_report(
        seed=get_random_seed(),
        timestamp=datetime.utcnow().isoformat(),
        total_datasets=len(aggregated_data),
        total_tests=num_tests,
        nominal_coverage=0.95,
        bonferroni_corrected=True,
        results=corrected_results
    )

    # Save structured report to JSON
    save_aggregate_report(aggregate_report, output_dir / "aggregate_report.json")

    # Generate Markdown report
    md_content = _generate_markdown_report(aggregate_report)

    report_path = output_dir / "aggregate_report.md"
    report_path.write_text(md_content, encoding='utf-8')

    logger.info(f"Aggregate report generated: {report_path}")
    return str(report_path)


def _generate_markdown_report(aggregate_report: Dict[str, Any]) -> str:
    """
    Generate the markdown content for the aggregate report.

    Explicitly contrasts the scope of multiple UCI datasets against
    previous synthetic approaches to ensure clarity on generalization.
    """
    lines = []
    lines.append("# Aggregate Report: Validity of Frequentist Confidence Intervals")
    lines.append("")
    lines.append(f"**Generated:** {aggregate_report['timestamp']}")
    lines.append(f"**Random Seed:** {aggregate_report['seed']}")
    lines.append(f"**Total Datasets Analyzed:** {aggregate_report['total_datasets']}")
    lines.append(f"**Total Statistical Tests:** {aggregate_report['total_tests']}")
    lines.append(f"**Nominal Coverage Level:** {aggregate_report['nominal_coverage']*100:.1f}%")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This report presents the results of a Monte Carlo simulation assessing the empirical coverage rates")
    lines.append("of frequentist confidence intervals (t-intervals and bootstrap percentile intervals) across **multiple")
    lines.append("real-world UCI Machine Learning datasets**. Unlike previous studies that relied on synthetic data")
    lines.append("generated from idealized distributions, this analysis uses **actual empirical data** to evaluate")
    lines.append("interval validity under realistic conditions.")
    lines.append("")
    lines.append("### Key Findings")
    lines.append("")

    # Count significant deviations
    significant_count = sum(1 for r in aggregate_report['results'] if r['is_practically_significant'])
    lines.append(f"- **Total Tests Performed:** {aggregate_report['total_tests']}")
    lines.append(f"- **Practically Significant Deviations (>1.0%):** {significant_count}")
    lines.append(f"- **Bonferroni Correction Applied:** Yes (Family-wise error rate controlled at α=0.05)")
    lines.append("")

    if significant_count > 0:
        lines.append(f"⚠️ **Warning:** {significant_count} configuration(s) showed practically significant deviations from")
        lines.append("the nominal 95% coverage level. These deviations suggest that the t-interval or bootstrap")
        lines.append("methods may not achieve their nominal coverage for certain small-sample configurations")
        lines.append("when applied to real-world data distributions.")
    else:
        lines.append("✅ **Result:** No configurations showed practically significant deviations from the nominal")
        lines.append("95% coverage level across all tested datasets and sample sizes.")
    lines.append("")

    # Scope Contrast Section (Critical for FR-007)
    lines.append("## Scope and Generalization: Real UCI Data vs. Synthetic Approaches")
    lines.append("")
    lines.append("### Distinction from Synthetic Studies")
    lines.append("")
    lines.append("Previous research on confidence interval validity has predominantly relied on **synthetic data")
    lines.append("generated from known parametric distributions** (e.g., Normal, t-distribution, Uniform). While")
    lines.append("these studies provide theoretical insights, they often fail to capture the complexities of")
    lines.append("real-world data, including:")
    lines.append("")
    lines.append("- **Non-normality and skewness** in empirical distributions")
    lines.append("- **Outliers and heavy tails** present in real measurements")
    lines.append("- **Discrete or mixed variable types** that violate continuous assumptions")
    lines.append("- **Complex dependencies** between variables that are not captured in simple models")
    lines.append("")
    lines.append("### Generalization to Real-World Applications")
    lines.append("")
    lines.append(f"This study explicitly addresses these limitations by analyzing **{aggregate_report['total_datasets']}")
    lines.append("real UCI datasets** spanning diverse domains (chemistry, biology, health, physics). The findings")
    lines.append("here are **associational** in nature: they describe the performance of confidence interval methods")
    lines.append("when applied to this specific set of real-world datasets, but **do not claim universal validity")
    lines.append("for all possible data distributions**.")
    lines.append("")
    lines.append("### Implications")
    lines.append("")
    lines.append("The results presented in this report should be interpreted as evidence of how well standard")
    lines.append("confidence interval procedures perform on **real, messy data** rather than idealized theoretical")
    lines.append("distributions. Practitioners should exercise caution when applying these methods to small samples")
    lines.append("from non-normal populations, as the empirical coverage rates may deviate from nominal levels.")
    lines.append("")

    # Detailed Results Table
    lines.append("---")
    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("The following table summarizes the empirical coverage rates for each dataset, sample size,")
    lines.append("and interval type combination. Deviations are calculated as (Empirical Coverage - 0.95).")
    lines.append("")
    lines.append("| Dataset | Sample Size | Interval Type | Replications | Coverage Rate | Deviation | Sig? | Bonferroni p-value |")
    lines.append("|---------|-------------|---------------|--------------|---------------|-----------|------|--------------------|")

    for result in aggregate_report['results']:
        sig_marker = "Yes" if result['is_practically_significant'] else "No"
        lines.append(
            f"| {result['dataset_id']} | {result['sample_size']} | {result['interval_type']} | "
            f"{result['total_replications']} | {result['coverage_rate']:.4f} | "
            f"{result['deviation']:.4f} | {sig_marker} | {result['bonferroni_p_value']:.6f} |"
        )
    lines.append("")

    # Methodology Section
    lines.append("---")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("### Data Sources")
    lines.append("")
    lines.append("Five UCI Machine Learning Repository datasets were analyzed:")
    lines.append("")
    datasets_list = sorted(list(set(r['dataset_id'] for r in aggregate_report['results'])))
    for ds in datasets_list:
        lines.append(f"- **{ds}**")
    lines.append("")
    lines.append("### Simulation Parameters")
    lines.append("")
    lines.append("- **Sample Sizes:** n = 10, 20, 30")
    lines.append("- **Interval Types:** Student's t-interval, Bootstrap percentile interval")
    lines.append("- **Nominal Coverage:** 95%")
    lines.append("- **Replications:** 1,000 per configuration (configurable)")
    lines.append("- **Ground Truth:** Mean of the full dataset array (operational population mean)")
    lines.append("")
    lines.append("### Statistical Corrections")
    lines.append("")
    lines.append("Bonferroni correction was applied to control the family-wise error rate across all")
    lines.append(f"{aggregate_report['total_tests']} statistical tests. The corrected significance threshold is")
    lines.append(f"α / {aggregate_report['total_tests']}.")
    lines.append("")

    # Conclusion
    lines.append("---")
    lines.append("")
    lines.append("## Conclusion")
    lines.append("")
    lines.append("This analysis provides empirical evidence on the validity of frequentist confidence intervals")
    lines.append("when applied to real-world datasets with small sample sizes. The findings highlight the importance")
    lines.append("of verifying interval performance under realistic conditions rather than relying solely on")
    lines.append("theoretical guarantees derived from synthetic data.")
    lines.append("")
    lines.append("Practitioners are advised to consider these results when designing studies with limited sample")
    lines.append("sizes and to complement standard interval methods with diagnostic checks or alternative approaches")
    lines.append("(e.g., robust standard errors, transformation-based methods) when appropriate.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by the llmXive automated science pipeline.*")

    return "\n".join(lines)


def main():
    """Main entry point for the report generation workflow."""
    try:
        report_path = generate_aggregate_report()
        print(f"Aggregate report successfully generated at: {report_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate aggregate report: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
