"""
Validation script to check results against success criteria (SC-001 to SC-005).

This module validates the statistical summary against predefined success criteria:
- SC-001: SART commission errors show significant reduction (p < 0.05, negative change)
- SC-002: Ospan scores show significant improvement (p < 0.05, positive change)
- SC-003: PSS-10 scores show significant reduction (p < 0.05, negative change)
- SC-004: PANAS positive affect shows significant increase (p < 0.05, positive change)
- SC-005: Effect sizes (Cohen's d) >= 0.2 for significant metrics

The script loads results from results/statistical_summary.json and generates
a validation report to results/validation_report.json and results/validation_report.md.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SuccessCriterion:
    """Represents a single success criterion."""
    id: str
    metric: str
    direction: str  # 'negative' for reduction, 'positive' for increase
    threshold_p: float
    threshold_d: float
    description: str


@dataclass
class ValidationResult:
    """Result of checking a single criterion."""
    criterion_id: str
    metric: str
    passed: bool
    reason: str
    observed_p: Optional[float] = None
    observed_d: Optional[float] = None
    observed_change: Optional[float] = None


@dataclass
class ValidationReport:
    """Complete validation report."""
    timestamp: str
    overall_passed: bool
    total_criteria: int
    passed_criteria: int
    failed_criteria: int
    results: List[Dict[str, Any]]
    summary: str


# Define success criteria based on SC-001 to SC-005
SUCCESS_CRITERIA = [
    SuccessCriterion(
        id="SC-001",
        metric="sart_commission_errors",
        direction="negative",  # Reduction in errors is good
        threshold_p=0.05,
        threshold_d=0.2,
        description="SART commission errors show significant reduction (p < 0.05, negative change)"
    ),
    SuccessCriterion(
        id="SC-002",
        metric="ospan_total_correct",
        direction="positive",  # Increase in correct responses is good
        threshold_p=0.05,
        threshold_d=0.2,
        description="Ospan scores show significant improvement (p < 0.05, positive change)"
    ),
    SuccessCriterion(
        id="SC-003",
        metric="pss10_total",
        direction="negative",  # Reduction in stress is good
        threshold_p=0.05,
        threshold_d=0.2,
        description="PSS-10 scores show significant reduction (p < 0.05, negative change)"
    ),
    SuccessCriterion(
        id="SC-004",
        metric="panas_positive_affect",
        direction="positive",  # Increase in positive affect is good
        threshold_p=0.05,
        threshold_d=0.2,
        description="PANAS positive affect shows significant increase (p < 0.05, positive change)"
    ),
    SuccessCriterion(
        id="SC-005",
        metric="all_significant",
        direction="any",
        threshold_p=0.05,
        threshold_d=0.2,
        description="Effect sizes (Cohen's d) >= 0.2 for all significant metrics"
    )
]


def get_metric_key(metric_name: str) -> str:
    """
    Convert metric name to the key used in statistical_summary.json.

    Args:
        metric_name: The metric name (e.g., 'sart_commission_errors')

    Returns:
        The key used in the JSON file
    """
    # Map metric names to JSON keys
    metric_map = {
        'sart_commission_errors': 'sart_commission_errors',
        'ospan_total_correct': 'ospan_total_correct',
        'pss10_total': 'pss10_total',
        'panas_positive_affect': 'panas_positive_affect',
        'panas_negative_affect': 'panas_negative_affect'
    }
    return metric_map.get(metric_name, metric_name)


def load_statistical_summary(summary_path: str) -> Dict[str, Any]:
    """
    Load the statistical summary from JSON file.

    Args:
        summary_path: Path to statistical_summary.json

    Returns:
        Dictionary containing the statistical summary

    Raises:
        FileNotFoundError: If the summary file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    path = Path(summary_path)
    if not path.exists():
        raise FileNotFoundError(f"Statistical summary file not found: {summary_path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_criterion(
    criterion: SuccessCriterion,
    summary: Dict[str, Any]
) -> ValidationResult:
    """
    Check a single success criterion against the statistical summary.

    Args:
        criterion: The success criterion to check
        summary: The statistical summary data

    Returns:
        ValidationResult with pass/fail status and details
    """
    metric_key = get_metric_key(criterion.metric)

    # Handle special case for SC-005 (all significant metrics)
    if criterion.metric == 'all_significant':
        return _check_all_effect_sizes(summary, criterion)

    # Check if metric exists in summary
    if metric_key not in summary.get('metrics', {}):
        return ValidationResult(
            criterion_id=criterion.id,
            metric=criterion.metric,
            passed=False,
            reason=f"Metric '{metric_key}' not found in statistical summary"
        )

    metric_data = summary['metrics'][metric_key]

    # Extract observed values
    observed_p = metric_data.get('corrected_p_value')
    observed_d = metric_data.get('cohens_d')
    observed_change = metric_data.get('mean_change')

    # Check significance (p < threshold)
    if observed_p is None:
        return ValidationResult(
            criterion_id=criterion.id,
            metric=criterion.metric,
            passed=False,
            reason=f"No p-value found for metric '{metric_key}'",
            observed_p=observed_p,
            observed_d=observed_d,
            observed_change=observed_change
        )

    is_significant = observed_p < criterion.threshold_p

    if not is_significant:
        return ValidationResult(
            criterion_id=criterion.id,
            metric=criterion.metric,
            passed=False,
            reason=f"Not significant (p={observed_p:.4f} >= {criterion.threshold_p})",
            observed_p=observed_p,
            observed_d=observed_d,
            observed_change=observed_change
        )

    # Check direction of effect
    direction_valid = False
    if criterion.direction == 'negative':
        direction_valid = observed_change is not None and observed_change < 0
        if not direction_valid:
            return ValidationResult(
                criterion_id=criterion.id,
                metric=criterion.metric,
                passed=False,
                reason=f"Wrong direction: expected negative change, got {observed_change:.4f}",
                observed_p=observed_p,
                observed_d=observed_d,
                observed_change=observed_change
            )
    elif criterion.direction == 'positive':
        direction_valid = observed_change is not None and observed_change > 0
        if not direction_valid:
            return ValidationResult(
                criterion_id=criterion.id,
                metric=criterion.metric,
                passed=False,
                reason=f"Wrong direction: expected positive change, got {observed_change:.4f}",
                observed_p=observed_p,
                observed_d=observed_d,
                observed_change=observed_change
            )

    # Check effect size
    if observed_d is None:
        return ValidationResult(
            criterion_id=criterion.id,
            metric=criterion.metric,
            passed=False,
            reason=f"No effect size (Cohen's d) found for metric '{metric_key}'",
            observed_p=observed_p,
            observed_d=observed_d,
            observed_change=observed_change
        )

    if abs(observed_d) < criterion.threshold_d:
        return ValidationResult(
            criterion_id=criterion.id,
            metric=criterion.metric,
            passed=False,
            reason=f"Effect size too small (d={observed_d:.4f} < {criterion.threshold_d})",
            observed_p=observed_p,
            observed_d=observed_d,
            observed_change=observed_change
        )

    return ValidationResult(
        criterion_id=criterion.id,
        metric=criterion.metric,
        passed=True,
        reason="Criterion met",
        observed_p=observed_p,
        observed_d=observed_d,
        observed_change=observed_change
    )


def _check_all_effect_sizes(
    summary: Dict[str, Any],
    criterion: SuccessCriterion
) -> ValidationResult:
    """
    Check SC-005: All significant metrics have effect size >= 0.2.

    Args:
        summary: The statistical summary data
        criterion: The success criterion (SC-005)

    Returns:
        ValidationResult
    """
    metrics = summary.get('metrics', {})
    failed_metrics = []

    for metric_key, metric_data in metrics.items():
        observed_p = metric_data.get('corrected_p_value')
        observed_d = metric_data.get('cohens_d')

        # Skip non-significant metrics
        if observed_p is None or observed_p >= 0.05:
            continue

        # Check effect size for significant metrics
        if observed_d is None or abs(observed_d) < 0.2:
            failed_metrics.append({
                'metric': metric_key,
                'p_value': observed_p,
                'cohens_d': observed_d
            })

    if failed_metrics:
        details = ", ".join([
            f"{m['metric']} (d={m['cohens_d']})" if m['cohens_d'] is not None else m['metric']
            for m in failed_metrics
        ])
        return ValidationResult(
            criterion_id=criterion.id,
            metric=criterion.metric,
            passed=False,
            reason=f"Effect size < 0.2 for significant metrics: {details}",
            observed_d=None
        )

    return ValidationResult(
        criterion_id=criterion.id,
        metric=criterion.metric,
        passed=True,
        reason="All significant metrics have effect size >= 0.2"
    )


def check_all_significant_criteria(
    summary: Dict[str, Any]
) -> List[ValidationResult]:
    """
    Check all success criteria against the statistical summary.

    Args:
        summary: The statistical summary data

    Returns:
        List of ValidationResult objects
    """
    results = []
    for criterion in SUCCESS_CRITERIA:
        result = check_criterion(criterion, summary)
        results.append(result)
    return results


def validate_success_criteria(
    summary_path: str = "results/statistical_summary.json",
    report_path: str = "results/validation_report.json"
) -> ValidationReport:
    """
    Main validation function that checks all success criteria and generates a report.

    Args:
        summary_path: Path to statistical_summary.json
        report_path: Path to write the validation report

    Returns:
        ValidationReport object
    """
    logger.info(f"Loading statistical summary from: {summary_path}")

    try:
        summary = load_statistical_summary(summary_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        # Create a failed report
        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            overall_passed=False,
            total_criteria=len(SUCCESS_CRITERIA),
            passed_criteria=0,
            failed_criteria=len(SUCCESS_CRITERIA),
            results=[{
                'criterion_id': 'SYSTEM',
                'metric': 'N/A',
                'passed': False,
                'reason': str(e)
            }],
            summary=f"Validation failed: {str(e)}"
        )
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in summary file: {e}")
        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            overall_passed=False,
            total_criteria=len(SUCCESS_CRITERIA),
            passed_criteria=0,
            failed_criteria=len(SUCCESS_CRITERIA),
            results=[{
                'criterion_id': 'SYSTEM',
                'metric': 'N/A',
                'passed': False,
                'reason': f"Invalid JSON: {str(e)}"
            }],
            summary=f"Validation failed: Invalid JSON in summary file"
        )

    logger.info("Checking success criteria...")
    results = check_all_significant_criteria(summary)

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    overall_passed = failed_count == 0

    # Create report
    report = ValidationReport(
        timestamp=datetime.now().isoformat(),
        overall_passed=overall_passed,
        total_criteria=len(results),
        passed_criteria=passed_count,
        failed_criteria=failed_count,
        results=[asdict(r) for r in results],
        summary=f"Validation {'PASSED' if overall_passed else 'FAILED'}: {passed_count}/{len(results)} criteria met"
    )

    # Ensure results directory exists
    report_dir = Path(report_path).parent
    report_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON report
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(report), f, indent=2)

    logger.info(f"Validation report written to: {report_path}")

    # Also write Markdown report
    md_report_path = str(Path(report_path).with_suffix('.md'))
    _write_markdown_report(report, md_report_path)

    logger.info(f"Markdown report written to: {md_report_path}")

    return report


def _write_markdown_report(report: ValidationReport, path: str) -> None:
    """
    Write a human-readable Markdown validation report.

    Args:
        report: The validation report
        path: Path to write the Markdown file
    """
    lines = [
        "# Success Criteria Validation Report",
        "",
        f"**Generated:** {report.timestamp}",
        f"**Overall Status:** {'✅ PASSED' if report.overall_passed else '❌ FAILED'}",
        "",
        f"**Summary:** {report.summary}",
        "",
        f"**Criteria Met:** {report.passed_criteria} / {report.total_criteria}",
        "",
        "---",
        "",
        "## Detailed Results",
        ""
    ]

    for result in report.results:
        status = "✅" if result['passed'] else "❌"
        lines.append(f"### {result['criterion_id']}: {result['metric']}")
        lines.append(f"- **Status:** {status} {'Passed' if result['passed'] else 'Failed'}")
        lines.append(f"- **Reason:** {result['reason']}")

        if result.get('observed_p') is not None:
            lines.append(f"- **Observed p-value:** {result['observed_p']:.4f}")
        if result.get('observed_d') is not None:
            lines.append(f"- **Observed Cohen's d:** {result['observed_d']:.4f}")
        if result.get('observed_change') is not None:
            change_sign = "+" if result['observed_change'] >= 0 else ""
            lines.append(f"- **Observed mean change:** {change_sign}{result['observed_change']:.4f}")

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Success Criteria Definitions")
    lines.append("")
    for criterion in SUCCESS_CRITERIA:
        lines.append(f"- **{criterion.id}:** {criterion.description}")
    lines.append("")

    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))


def main():
    """Main entry point for the validation script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate statistical results against success criteria"
    )
    parser.add_argument(
        "--summary",
        type=str,
        default="results/statistical_summary.json",
        help="Path to statistical_summary.json"
    )
    parser.add_argument(
        "--report",
        type=str,
        default="results/validation_report.json",
        help="Path to write validation report"
    )

    args = parser.parse_args()

    logger.info("Starting success criteria validation...")

    report = validate_success_criteria(
        summary_path=args.summary,
        report_path=args.report
    )

    # Print summary to console
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Overall Status: {'PASSED' if report.overall_passed else 'FAILED'}")
    print(f"Criteria Met: {report.passed_criteria}/{report.total_criteria}")
    print(f"Report saved to: {args.report}")
    print(f"Markdown report saved to: {args.report.replace('.json', '.md')}")
    print("=" * 60 + "\n")

    # Exit with appropriate code
    sys.exit(0 if report.overall_passed else 1)


if __name__ == "__main__":
    main()
