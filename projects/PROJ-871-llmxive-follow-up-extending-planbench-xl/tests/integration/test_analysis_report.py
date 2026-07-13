"""
Integration test for report generation (T022).

This test verifies that the analysis pipeline (log parsing, statistical analysis,
and report generation) works end-to-end when provided with real execution logs.
It creates synthetic but realistic log data to simulate the output of the
baseline and augmented agents, then validates the generated report structure
and statistical correctness.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path to import analysis modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.log_parser import parse_execution_logs
from code.analysis.stats import run_statistical_test
from code.analysis.report import generate_report


def create_mock_logs(
    tmp_path: Path,
    baseline_successes: int,
    baseline_total: int,
    augmented_successes: int,
    augmented_total: int
) -> tuple[Path, Path]:
    """
    Create mock execution logs that simulate real agent outputs.

    Args:
        tmp_path: Temporary directory for log files
        baseline_successes: Number of successful baseline tasks
        baseline_total: Total baseline tasks
        augmented_successes: Number of successful augmented tasks
        augmented_total: Total augmented tasks

    Returns:
        Tuple of (baseline_log_path, augmented_log_path)
    """
    baseline_log_path = tmp_path / "baseline_execution.jsonl"
    augmented_log_path = tmp_path / "augmented_execution.jsonl"

    # Create baseline logs
    with open(baseline_log_path, "w") as f:
        for i in range(baseline_total):
            log_entry = {
                "task_id": f"task_{i:04d}",
                "status": "success" if i < baseline_successes else "failure",
                "ground_truth": "success",
                "steps": [],
                "tool_calls": [],
                "timestamp": "2024-01-01T00:00:00Z"
            }
            f.write(json.dumps(log_entry) + "\n")

    # Create augmented logs
    with open(augmented_log_path, "w") as f:
        for i in range(augmented_total):
            log_entry = {
                "task_id": f"task_{i:04d}",
                "status": "success" if i < augmented_successes else "failure",
                "ground_truth": "success",
                "signature_used": True,
                "recovery_attempted": i >= augmented_successes and i < augmented_total,
                "steps": [],
                "tool_calls": [],
                "timestamp": "2024-01-01T00:00:00Z"
            }
            f.write(json.dumps(log_entry) + "\n")

    return baseline_log_path, augmented_log_path


def test_report_generation_end_to_end(tmp_path: Path):
    """
    Test the full report generation pipeline.

    This test:
    1. Creates mock execution logs with known success/failure counts
    2. Parses the logs to extract statistics
    3. Runs the appropriate statistical test (Fisher or Z-test based on N)
    4. Generates a final report
    5. Validates the report structure and content
    """
    # Setup: Create mock logs with specific success rates
    # Using N=50 for each (>=30) to trigger Z-test
    baseline_successes = 30
    baseline_total = 50
    augmented_successes = 40
    augmented_total = 50

    baseline_log_path, augmented_log_path = create_mock_logs(
        tmp_path,
        baseline_successes,
        baseline_total,
        augmented_successes,
        augmented_total
    )

    # Execute: Parse logs
    baseline_stats = parse_execution_logs(str(baseline_log_path))
    augmented_stats = parse_execution_logs(str(augmented_log_path))

    # Verify parsing results
    assert baseline_stats["total"] == baseline_total
    assert baseline_stats["successes"] == baseline_successes
    assert augmented_stats["total"] == augmented_total
    assert augmented_stats["successes"] == augmented_successes

    # Execute: Run statistical test
    test_result = run_statistical_test(
        baseline_stats["successes"],
        baseline_stats["total"],
        augmented_stats["successes"],
        augmented_stats["total"]
    )

    # Verify test result structure
    assert "test_type" in test_result
    assert "p_value" in test_result
    assert "statistic" in test_result
    assert test_result["test_type"] == "z_test"  # N >= 30

    # Execute: Generate report
    report_path = tmp_path / "final_report.json"
    generate_report(
        baseline_stats,
        augmented_stats,
        test_result,
        str(report_path)
    )

    # Verify: Report file exists
    assert report_path.exists(), "Report file was not created"

    # Verify: Report content
    with open(report_path, "r") as f:
        report = json.load(f)

    # Validate report structure
    required_fields = [
        "baseline_success_rate",
        "augmented_success_rate",
        "success_rate_difference",
        "p_value",
        "test_type",
        "conclusion",
        "baseline_total",
        "augmented_total",
        "baseline_successes",
        "augmented_successes"
    ]

    for field in required_fields:
        assert field in report, f"Missing required field: {field}"

    # Validate calculated values
    assert report["baseline_success_rate"] == baseline_successes / baseline_total
    assert report["augmented_success_rate"] == augmented_successes / augmented_total
    expected_diff = (augmented_successes / augmented_total) - (baseline_successes / baseline_total)
    assert abs(report["success_rate_difference"] - expected_diff) < 1e-6

    # Validate conclusion logic
    if report["p_value"] < 0.05:
        assert "significant" in report["conclusion"].lower()
    else:
        assert "not significant" in report["conclusion"].lower()

    # Validate counts
    assert report["baseline_total"] == baseline_total
    assert report["augmented_total"] == augmented_total
    assert report["baseline_successes"] == baseline_successes
    assert report["augmented_successes"] == augmented_successes


def test_report_generation_small_sample_fisher(tmp_path: Path):
    """
    Test report generation with small sample size (N < 30) to trigger Fisher's Exact Test.
    """
    # Setup: Create mock logs with N < 30
    baseline_successes = 3
    baseline_total = 10
    augmented_successes = 7
    augmented_total = 10

    baseline_log_path, augmented_log_path = create_mock_logs(
        tmp_path,
        baseline_successes,
        baseline_total,
        augmented_successes,
        augmented_total
    )

    # Execute: Parse logs
    baseline_stats = parse_execution_logs(str(baseline_log_path))
    augmented_stats = parse_execution_logs(str(augmented_log_path))

    # Execute: Run statistical test
    test_result = run_statistical_test(
        baseline_stats["successes"],
        baseline_stats["total"],
        augmented_stats["successes"],
        augmented_stats["total"]
    )

    # Verify test result uses Fisher's Exact Test
    assert test_result["test_type"] == "fisher_exact"

    # Execute: Generate report
    report_path = tmp_path / "final_report.json"
    generate_report(
        baseline_stats,
        augmented_stats,
        test_result,
        str(report_path)
    )

    # Verify: Report content
    with open(report_path, "r") as f:
        report = json.load(f)

    assert report["test_type"] == "fisher_exact"
    assert "p_value" in report
    assert "conclusion" in report


def test_report_generation_with_zero_successes(tmp_path: Path):
    """
    Test report generation edge case: one group has zero successes.
    """
    # Setup: Baseline has 0 successes, augmented has some
    baseline_successes = 0
    baseline_total = 15
    augmented_successes = 8
    augmented_total = 15

    baseline_log_path, augmented_log_path = create_mock_logs(
        tmp_path,
        baseline_successes,
        baseline_total,
        augmented_successes,
        augmented_total
    )

    # Execute: Parse logs
    baseline_stats = parse_execution_logs(str(baseline_log_path))
    augmented_stats = parse_execution_logs(str(augmented_log_path))

    # Execute: Run statistical test
    test_result = run_statistical_test(
        baseline_stats["successes"],
        baseline_stats["total"],
        augmented_stats["successes"],
        augmented_stats["total"]
    )

    # Execute: Generate report (should not crash)
    report_path = tmp_path / "final_report.json"
    generate_report(
        baseline_stats,
        augmented_stats,
        test_result,
        str(report_path)
    )

    # Verify: Report exists and has valid structure
    assert report_path.exists()
    with open(report_path, "r") as f:
        report = json.load(f)

    assert report["baseline_success_rate"] == 0.0
    assert report["augmented_success_rate"] == 8 / 15
    assert "conclusion" in report