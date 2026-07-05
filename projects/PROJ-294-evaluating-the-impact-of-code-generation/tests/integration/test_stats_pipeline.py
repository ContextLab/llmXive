"""
Integration test verifying the full statistical report generation from metrics.json.

This test validates the end-to-end flow of:
1. Loading metrics from a JSON file (simulating the output of T017/T041)
2. Running the full statistical analysis suite (T020-T025)
3. Verifying that all expected statistical outputs are generated correctly

Prerequisites:
- code/statistical_tests.py must implement: load_metrics, run_statistical_analysis, main
- data/analysis/metrics.json must exist with valid paired data
"""
import os
import json
import tempfile
import pytest
import sys
import logging
from pathlib import Path

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from statistical_tests import (
    load_metrics,
    run_statistical_analysis,
    main as statistical_main
)
from utils import setup_logging, get_logger

# Configure logging for the test
setup_logging(task_id="T027")
logger = get_logger("T027")


def create_mock_metrics_file(tmp_path):
    """
    Creates a realistic mock metrics.json file for integration testing.
    This simulates the output of the data acquisition and analysis pipeline.
    """
    metrics_data = {
        "metadata": {
            "source": "HumanEval",
            "model": "codegen-mono-350M",
            "n_samples": 50,
            "generated_at": "2024-01-01T00:00:00Z"
        },
        "samples": []
    }

    # Generate 50 realistic mock samples
    # We use a mix of values to ensure statistical tests have variance
    import random
    random.seed(42)  # Reproducibility

    for i in range(50):
        # Simulate paired data: original (human) vs generated (LLM)
        # We create a slight correlation to make the tests realistic
        base_complexity = random.gauss(5.0, 1.5)
        base_halstead = random.gauss(100.0, 20.0)
        base_coverage = random.gauss(80.0, 10.0)
        
        # Add some noise and slight bias for the generated code
        orig_complexity = max(1.0, base_complexity)
        gen_complexity = max(1.0, base_complexity + random.gauss(0.5, 0.5))
        
        orig_halstead = max(10.0, base_halstead)
        gen_halstead = max(10.0, base_halstead + random.gauss(5.0, 5.0))
        
        orig_coverage = max(0.0, min(100.0, base_coverage))
        gen_coverage = max(0.0, min(100.0, base_coverage - random.gauss(2.0, 3.0)))
        
        # Binary pass rate (0 or 1)
        orig_pass = 1 if random.random() > 0.2 else 0
        gen_pass = 1 if random.random() > 0.3 else 0  # Slightly lower pass rate

        sample = {
            "task_id": f"HumanEval_{i:03d}",
            "original": {
                "cyclomatic_complexity": round(orig_complexity, 2),
                "halstead_volume": round(orig_halstead, 2),
                "branch_coverage_pct": round(orig_coverage, 2),
                "pass_rate": orig_pass
            },
            "generated": {
                "cyclomatic_complexity": round(gen_complexity, 2),
                "halstead_volume": round(gen_halstead, 2),
                "branch_coverage_pct": round(gen_coverage, 2),
                "pass_rate": gen_pass
            }
        }
        metrics_data["samples"].append(sample)

    metrics_file = tmp_path / "metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    return metrics_file


def test_load_metrics_valid_file(tmp_path):
    """Test that load_metrics correctly parses a valid metrics.json file."""
    metrics_file = create_mock_metrics_file(tmp_path)
    
    metrics = load_metrics(str(metrics_file))
    
    assert metrics is not None
    assert "metadata" in metrics
    assert "samples" in metrics
    assert len(metrics["samples"]) == 50
    assert "task_id" in metrics["samples"][0]
    assert "original" in metrics["samples"][0]
    assert "generated" in metrics["samples"][0]


def test_run_statistical_analysis_full_pipeline(tmp_path):
    """
    Integration test: Run the full statistical analysis pipeline on mock data.
    Verifies that all statistical tests execute without errors and produce
    expected output structures.
    """
    metrics_file = create_mock_metrics_file(tmp_path)
    
    # Run the full statistical analysis
    results = run_statistical_analysis(str(metrics_file))
    
    # Verify the structure of the results
    assert results is not None
    assert "wilcoxon" in results
    assert "mcnemar" in results
    assert "fisher" in results
    assert "permutation" in results
    assert "power_analysis" in results
    assert "correlation" in results
    
    # Verify Wilcoxon results for all metrics
    wilcoxon = results["wilcoxon"]
    assert "cyclomatic_complexity" in wilcoxon
    assert "halstead_volume" in wilcoxon
    assert "branch_coverage_pct" in wilcoxon
    
    for metric, stats in wilcoxon.items():
        assert "statistic" in stats
        assert "pvalue" in stats
        assert "n" in stats
        assert stats["n"] == 50  # All 50 samples should be used
    
    # Verify McNemar test for pass rate
    mcnemar = results["mcnemar"]
    assert "statistic" in mcnemar
    assert "pvalue" in mcnemar
    assert mcnemar["n"] == 50
    
    # Verify Fisher's exact test
    fisher = results["fisher"]
    assert "statistic" in fisher
    assert "pvalue" in fisher
    
    # Verify permutation test
    perm = results["permutation"]
    assert "statistic" in perm
    assert "pvalue" in perm
    
    # Verify power analysis
    power = results["power_analysis"]
    assert "a_priori" in power
    assert "post_hoc" in power
    assert power["a_priori"]["required_n"] >= 38
    
    # Verify correlation analysis
    corr = results["correlation"]
    assert "spearman" in corr
    assert "point_biserial" in corr
    
    logger.info("Full statistical pipeline executed successfully")
    logger.info(f"Wilcoxon p-values: {wilcoxon['cyclomatic_complexity']['pvalue']:.4f}, "
               f"{wilcoxon['halstead_volume']['pvalue']:.4f}, "
               f"{wilcoxon['branch_coverage_pct']['pvalue']:.4f}")


def test_main_entry_point(tmp_path):
    """
    Integration test: Verify the main() entry point runs correctly.
    This simulates the actual command-line execution of statistical_tests.py
    """
    metrics_file = create_mock_metrics_file(tmp_path)
    
    # Save results to a temporary output file
    output_file = tmp_path / "statistical_results.json"
    
    # Mock sys.argv to simulate command-line execution
    original_argv = sys.argv
    try:
        sys.argv = [
            "statistical_tests.py",
            "--input", str(metrics_file),
            "--output", str(output_file)
        ]
        
        # Run the main function
        statistical_main()
        
        # Verify output file was created
        assert output_file.exists()
        
        # Load and verify the output
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        assert "wilcoxon" in results
        assert "mcnemar" in results
        assert "power_analysis" in results
        
        logger.info("Main entry point executed successfully")
        logger.info(f"Results written to {output_file}")
        
    finally:
        sys.argv = original_argv


def test_statistical_analysis_with_deferred_values(tmp_path):
    """
    Test that the pipeline handles [deferred] or missing values gracefully.
    """
    metrics_file = create_mock_metrics_file(tmp_path)
    
    # Load and modify the data to include a deferred value
    with open(metrics_file, 'r') as f:
        metrics_data = json.load(f)
    
    # Add a sample with a deferred coverage value
    metrics_data["samples"].append({
        "task_id": "HumanEval_deferred",
        "original": {
            "cyclomatic_complexity": 4.0,
            "halstead_volume": 80.0,
            "branch_coverage_pct": "[deferred]",  # Simulate execution failure
            "pass_rate": 1
        },
        "generated": {
            "cyclomatic_complexity": 4.5,
            "halstead_volume": 85.0,
            "branch_coverage_pct": 75.0,
            "pass_rate": 1
        }
    })
    
    # Save modified data
    modified_file = tmp_path / "metrics_with_deferred.json"
    with open(modified_file, 'w') as f:
        json.dump(metrics_data, f)
    
    # Run analysis - should handle the deferred value gracefully
    results = run_statistical_analysis(str(modified_file))
    
    # Verify that the analysis completed (n should be 49 for coverage due to one deferred)
    assert results is not None
    assert results["wilcoxon"]["branch_coverage_pct"]["n"] == 49
    
    logger.info("Pipeline handled deferred values correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
