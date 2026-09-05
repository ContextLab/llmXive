"""
Integration test for the full comparative pipeline (US3).

This test orchestrates the end-to-end comparison between the Symbolic Memory system
and the Neural Baseline (ABot-AgentOS v1.0 or mock). It verifies:
1. Real data loading (ALFWorld traces).
2. Graph construction via the symbolic pipeline.
3. Baseline execution.
4. Metrics collection (success, latency, memory).
5. Statistical analysis (McNemar test).
6. Final report generation.

The test runs the actual scripts to produce real output files in data/results/.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"

# Expected output artifacts
EXPECTED_ARTIFACTS = [
    RESULTS_DIR / "sweep_metrics.csv",
    RESULTS_DIR / "latency_violations.json",
    RESULTS_DIR / "reconstruction_error.json",
    RESULTS_DIR / "comparative_results.json",
    RESULTS_DIR / "final_report.md",
    RESULTS_DIR / "error_coverage.json",
    RESULTS_DIR / "deltas.json",
]

@pytest.fixture(scope="module", autouse=True)
def ensure_directories():
    """Ensure required output directories exist."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    yield

def run_python_script(script_name: str, args: list = None, timeout: int = 300) -> tuple:
    """Helper to run a Python script in the code directory."""
    cmd = [sys.executable, str(CODE_DIR / script_name)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        pytest.fail(f"Script {script_name} timed out after {timeout}s")

def test_01_run_graph_construction_sweep():
    """
    Step 1: Run the graph construction sweep (T016).
    This populates sweep_metrics.csv and ensures the symbolic graph builder works.
    """
    # T016: Parametric sweep
    rc, out, err = run_python_script("experiment_runner.py", ["--mode", "sweep"])
    assert rc == 0, f"Graph sweep failed: {err}\n{out}"
    assert (RESULTS_DIR / "sweep_metrics.csv").exists(), "sweep_metrics.csv not generated"

def test_02_run_baseline_and_symbolic_comparison():
    """
    Step 2: Run the comparative experiment (T028).
    This executes both the symbolic pipeline and the baseline, collects metrics,
    runs McNemar test (T029), and generates the final report (T032).
    """
    # T028: Comparative experiment orchestration
    # T029: McNemar test is called internally by metrics.py or experiment_runner
    # T032: Final report generation
    rc, out, err = run_python_script("experiment_runner.py", ["--mode", "compare"])
    
    # Assert success
    assert rc == 0, f"Comparative experiment failed: {err}\n{out}"
    
    # Verify output files exist
    assert (RESULTS_DIR / "comparative_results.json").exists(), "comparative_results.json missing"
    assert (RESULTS_DIR / "final_report.md").exists(), "final_report.md missing"
    
    # Verify content of final report (T032)
    report_path = RESULTS_DIR / "final_report.md"
    with open(report_path, "r") as f:
        content = f.read()
    
    # Check for required statistical markers
    assert "p-value" in content.lower(), "Report missing p-value"
    assert "success_rate_delta" in content.lower() or "success rate difference" in content.lower(), "Report missing success rate delta"
    assert "memory_reduction" in content.lower() or "memory reduction" in content.lower(), "Report missing memory reduction metric"

def test_03_verify_latency_guard_integration():
    """
    Step 3: Verify that the latency guard (T023) was triggered and logged.
    """
    # T023: Latency guard violations
    violations_path = RESULTS_DIR / "latency_violations.json"
    assert violations_path.exists(), "latency_violations.json missing"
    
    with open(violations_path, "r") as f:
        violations = json.load(f)
    
    # The file must be valid JSON list/dict, even if empty (no violations)
    assert isinstance(violations, (list, dict)), "latency_violations.json is not valid JSON structure"

def test_04_verify_error_analysis_coverage():
    """
    Step 4: Verify error analysis (T030, T030b) coverage report.
    """
    # T030b: Error coverage report
    coverage_path = RESULTS_DIR / "error_coverage.json"
    assert coverage_path.exists(), "error_coverage.json missing"
    
    with open(coverage_path, "r") as f:
        coverage = json.load(f)
    
    assert "coverage_percentage" in coverage or "categorized_failures" in coverage, \
        "Error coverage report missing required fields"

def test_05_verify_reconstruction_error():
    """
    Step 5: Verify ground truth validation (T009b).
    """
    # T009b: Reconstruction error
    error_path = RESULTS_DIR / "reconstruction_error.json"
    assert error_path.exists(), "reconstruction_error.json missing"
    
    with open(error_path, "r") as f:
        error_data = json.load(f)
    
    assert "error_rate" in error_data, "Reconstruction error missing error_rate"

def test_06_final_artifact_check():
    """
    Final check: Ensure all expected artifacts from the pipeline exist and are non-empty.
    """
    missing = []
    for artifact in EXPECTED_ARTIFACTS:
        if not artifact.exists():
            missing.append(str(artifact.relative_to(PROJECT_ROOT)))
        elif artifact.stat().st_size == 0:
            missing.append(f"{artifact.relative_to(PROJECT_ROOT)} (empty)")
    
    if missing:
        pytest.fail(f"Missing or empty artifacts: {', '.join(missing)}")

def test_07_verify_deltas_content():
    """
    Step 7: Verify deltas.json contains real calculated values.
    """
    deltas_path = RESULTS_DIR / "deltas.json"
    assert deltas_path.exists(), "deltas.json missing"
    
    with open(deltas_path, "r") as f:
        deltas = json.load(f)
    
    assert "success_rate_delta" in deltas, "deltas.json missing success_rate_delta"
    assert "memory_reduction_pct" in deltas, "deltas.json missing memory_reduction_pct"
    
    # Values should be floats (not None or strings)
    assert isinstance(deltas["success_rate_delta"], (int, float)), "success_rate_delta is not a number"
    assert isinstance(deltas["memory_reduction_pct"], (int, float)), "memory_reduction_pct is not a number"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])