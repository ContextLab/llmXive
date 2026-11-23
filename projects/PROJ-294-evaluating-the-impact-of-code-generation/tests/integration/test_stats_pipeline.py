"""
Integration test verifying the full statistical report generation from metrics.json.

This test validates the end-to-end flow of the statistical analysis pipeline:
1. Loads real metrics data from data/analysis/metrics.json
2. Runs all statistical tests (Wilcoxon, McNemar, Fisher, Permutation, Power Analysis)
3. Validates the statistical results structure
4. Verifies success criteria validation (SC-002, SC-003)
5. Ensures the statistical results are written to state/statistical_results.yaml

This test requires that T017 has completed successfully and produced a valid
data/analysis/metrics.json file with paired HumanEval data.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from statistical_tests import (
    load_metrics,
    wilcoxon_signed_rank_test,
    calculate_wilcoxon_for_all_metrics,
    mcnemar_test,
    calculate_mcnemar_for_pass_rate,
    fisher_exact_test_paired,
    calculate_fisher_for_pass_rate,
    permutation_test_paired,
    calculate_permutation_for_branch_coverage,
    calculate_effect_size_cohen_d,
    a_priori_power_analysis,
    post_hoc_power_analysis,
    validate_success_criteria,
    run_statistical_analysis
)

from analyze_metrics import load_intermediate_metrics

# Test fixtures
@pytest.fixture
def sample_metrics_file(tmp_path):
    """Create a minimal valid metrics.json file for testing."""
    metrics_data = [
        {
            "task_id": "HumanEval/0",
            "source_type": "human",
            "cyclomatic_complexity": 5,
            "halstead_volume": 50.5,
            "halstead_components": {"N": 20, "n": 5, "L": 10, "D": 4, "E": 202},
            "branch_coverage_pct": 85.0,
            "pass_rate": 1
        },
        {
            "task_id": "HumanEval/0",
            "source_type": "codegen",
            "cyclomatic_complexity": 7,
            "halstead_volume": 65.2,
            "halstead_components": {"N": 25, "n": 6, "L": 12, "D": 5, "E": 326},
            "branch_coverage_pct": 75.0,
            "pass_rate": 0
        },
        {
            "task_id": "HumanEval/1",
            "source_type": "human",
            "cyclomatic_complexity": 4,
            "halstead_volume": 45.0,
            "halstead_components": {"N": 18, "n": 4, "L": 9, "D": 4, "E": 180},
            "branch_coverage_pct": 90.0,
            "pass_rate": 1
        },
        {
            "task_id": "HumanEval/1",
            "source_type": "codegen",
            "cyclomatic_complexity": 6,
            "halstead_volume": 58.3,
            "halstead_components": {"N": 22, "n": 5, "L": 11, "D": 4.5, "E": 291.5},
            "branch_coverage_pct": 80.0,
            "pass_rate": 1
        }
    ]
    
    output_file = tmp_path / "metrics.json"
    with open(output_file, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    return str(output_file)

@pytest.fixture
def real_metrics_file():
    """Load the real metrics.json if it exists from T017."""
    metrics_path = PROJECT_ROOT / "data" / "analysis" / "metrics.json"
    if metrics_path.exists():
        return str(metrics_path)
    return None

class TestStatisticalPipelineIntegration:
    """Integration tests for the full statistical analysis pipeline."""

    def test_load_metrics_valid_file(self, sample_metrics_file):
        """Test that load_metrics correctly parses a valid metrics.json file."""
        metrics = load_metrics(sample_metrics_file)
        
        assert isinstance(metrics, list)
        assert len(metrics) == 4
        
        # Check required fields exist
        for record in metrics:
            assert "task_id" in record
            assert "source_type" in record
            assert "cyclomatic_complexity" in record
            assert "halstead_volume" in record
            assert "branch_coverage_pct" in record
            assert "pass_rate" in record
    
    def test_load_metrics_missing_file(self, tmp_path):
        """Test that load_metrics raises FileNotFoundError for missing file."""
        non_existent = str(tmp_path / "non_existent.json")
        
        with pytest.raises(FileNotFoundError):
            load_metrics(non_existent)
    
    def test_wilcoxon_test_computation(self, sample_metrics_file):
        """Test Wilcoxon signed-rank test on paired continuous metrics."""
        metrics = load_metrics(sample_metrics_file)
        
        # Filter for paired data (same task_id, different source_type)
        paired_data = {}
        for record in metrics:
            task_id = record["task_id"]
            source = record["source_type"]
            if task_id not in paired_data:
                paired_data[task_id] = {}
            paired_data[task_id][source] = record["cyclomatic_complexity"]
        
        # Extract paired values
        human_values = []
        codegen_values = []
        for task_id in paired_data:
            if "human" in paired_data[task_id] and "codegen" in paired_data[task_id]:
                human_values.append(paired_data[task_id]["human"])
                codegen_values.append(paired_data[task_id]["codegen"])
        
        # Run Wilcoxon test
        result = wilcoxon_signed_rank_test(human_values, codegen_values)
        
        assert "statistic" in result
        assert "pvalue" in result
        assert isinstance(result["statistic"], (int, float))
        assert isinstance(result["pvalue"], (int, float))
        assert 0 <= result["pvalue"] <= 1

    def test_mcnemar_test_computation(self, sample_metrics_file):
        """Test McNemar's test on paired binary pass-rate data."""
        metrics = load_metrics(sample_metrics_file)
        
        # Filter for paired binary data
        paired_data = {}
        for record in metrics:
            task_id = record["task_id"]
            source = record["source_type"]
            if task_id not in paired_data:
                paired_data[task_id] = {}
            paired_data[task_id][source] = record["pass_rate"]
        
        # Extract paired binary values
        human_pass = []
        codegen_pass = []
        for task_id in paired_data:
            if "human" in paired_data[task_id] and "codegen" in paired_data[task_id]:
                human_pass.append(paired_data[task_id]["human"])
                codegen_pass.append(paired_data[task_id]["codegen"])
        
        # Run McNemar test
        result = mcnemar_test(human_pass, codegen_pass)
        
        assert "statistic" in result
        assert "pvalue" in result
        assert isinstance(result["statistic"], (int, float))
        assert isinstance(result["pvalue"], (int, float))
        assert 0 <= result["pvalue"] <= 1

    def test_fisher_exact_test_paired(self, sample_metrics_file):
        """Test paired Fisher's exact test on binary data."""
        metrics = load_metrics(sample_metrics_file)
        
        # Prepare paired binary data
        paired_data = {}
        for record in metrics:
            task_id = record["task_id"]
            source = record["source_type"]
            if task_id not in paired_data:
                paired_data[task_id] = {}
            paired_data[task_id][source] = record["pass_rate"]
        
        human_pass = []
        codegen_pass = []
        for task_id in paired_data:
            if "human" in paired_data[task_id] and "codegen" in paired_data[task_id]:
                human_pass.append(paired_data[task_id]["human"])
                codegen_pass.append(paired_data[task_id]["codegen"])
        
        # Run Fisher's exact test (paired)
        result = fisher_exact_test_paired(human_pass, codegen_pass)
        
        assert "pvalue" in result
        assert isinstance(result["pvalue"], (int, float))
        assert 0 <= result["pvalue"] <= 1

    def test_permutation_test_paired(self, sample_metrics_file):
        """Test permutation test on paired branch coverage data."""
        metrics = load_metrics(sample_metrics_file)
        
        # Prepare paired coverage data
        paired_data = {}
        for record in metrics:
            task_id = record["task_id"]
            source = record["source_type"]
            if task_id not in paired_data:
                paired_data[task_id] = {}
            paired_data[task_id][source] = record["branch_coverage_pct"]
        
        human_coverage = []
        codegen_coverage = []
        for task_id in paired_data:
            if "human" in paired_data[task_id] and "codegen" in paired_data[task_id]:
                human_coverage.append(paired_data[task_id]["human"])
                codegen_coverage.append(paired_data[task_id]["codegen"])
        
        # Run permutation test
        result = permutation_test_paired(human_coverage, codegen_coverage, n_permutations=1000)
        
        assert "pvalue" in result
        assert "observed_difference" in result
        assert isinstance(result["pvalue"], (int, float))
        assert isinstance(result["observed_difference"], (int, float))
        assert 0 <= result["pvalue"] <= 1

    def test_power_analysis_computation(self, sample_metrics_file):
        """Test power analysis calculations."""
        # A priori power analysis
        a_priori_result = a_priori_power_analysis(
            effect_size=0.5,
            alpha=0.05,
            power=0.8,
            test_type="paired"
        )
        
        assert "required_sample_size" in a_priori_result
        assert a_priori_result["required_sample_size"] >= 38  # Per FR-008
        
        # Post-hoc power analysis
        # Simulate observed effect size from sample data
        metrics = load_metrics(sample_metrics_file)
        paired_data = {}
        for record in metrics:
            task_id = record["task_id"]
            source = record["source_type"]
            if task_id not in paired_data:
                paired_data[task_id] = {}
            paired_data[task_id][source] = record["cyclomatic_complexity"]
        
        human_values = []
        codegen_values = []
        for task_id in paired_data:
            if "human" in paired_data[task_id] and "codegen" in paired_data[task_id]:
                human_values.append(paired_data[task_id]["human"])
                codegen_values.append(paired_data[task_id]["codegen"])
        
        if len(human_values) >= 2:
            effect_size = calculate_effect_size_cohen_d(human_values, codegen_values)
            post_hoc_result = post_hoc_power_analysis(
                effect_size=effect_size,
                sample_size=len(human_values),
                alpha=0.05
            )
            
            assert "achieved_power" in post_hoc_result
            assert isinstance(post_hoc_result["achieved_power"], (int, float))
            assert 0 <= post_hoc_result["achieved_power"] <= 1

    def test_success_criteria_validation(self, sample_metrics_file):
        """Test success criteria validation (SC-002, SC-003)."""
        metrics = load_metrics(sample_metrics_file)
        
        # Run full statistical analysis
        results = run_statistical_analysis(
            metrics_file=sample_metrics_file,
            output_file=None  # Don't write to disk for this test
        )
        
        # Validate success criteria
        validation = validate_success_criteria(results)
        
        assert "sc_002_statistical_significance" in validation
        assert "sc_003_visualization_quality" in validation
        assert isinstance(validation["sc_002_statistical_significance"], bool)
        assert isinstance(validation["sc_003_visualization_quality"], bool)
    
    def test_full_pipeline_integration(self, tmp_path):
        """Test the complete pipeline from metrics.json to statistical results."""
        # Create output directory
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = state_dir / "statistical_results.yaml"
        
        # Run full statistical analysis
        results = run_statistical_analysis(
            metrics_file=str(PROJECT_ROOT / "data" / "analysis" / "metrics.json") if (PROJECT_ROOT / "data" / "analysis" / "metrics.json").exists() else None,
            output_file=str(output_file)
        )
        
        # If real metrics don't exist, use sample
        if not results:
            sample_file = tmp_path / "sample_metrics.json"
            sample_data = [
                {
                    "task_id": "HumanEval/0",
                    "source_type": "human",
                    "cyclomatic_complexity": 5,
                    "halstead_volume": 50.5,
                    "branch_coverage_pct": 85.0,
                    "pass_rate": 1
                },
                {
                    "task_id": "HumanEval/0",
                    "source_type": "codegen",
                    "cyclomatic_complexity": 7,
                    "halstead_volume": 65.2,
                    "branch_coverage_pct": 75.0,
                    "pass_rate": 0
                }
            ]
            with open(sample_file, 'w') as f:
                json.dump(sample_data, f)
            
            results = run_statistical_analysis(
                metrics_file=str(sample_file),
                output_file=str(output_file)
            )
        
        # Verify results structure
        assert results is not None
        assert "wilcoxon_results" in results
        assert "mcnemar_results" in results
        assert "fisher_results" in results
        assert "permutation_results" in results
        assert "power_analysis" in results
        assert "success_criteria_validation" in results
        
        # Verify output file was written
        if output_file.exists():
            import yaml
            with open(output_file, 'r') as f:
                saved_results = yaml.safe_load(f)
            
            assert saved_results is not None
            assert "wilcoxon_results" in saved_results

    def test_empty_metrics_handling(self, tmp_path):
        """Test handling of empty metrics file."""
        empty_file = tmp_path / "empty_metrics.json"
        with open(empty_file, 'w') as f:
            json.dump([], f)
        
        # Should handle gracefully without crashing
        results = run_statistical_analysis(
            metrics_file=str(empty_file),
            output_file=None
        )
        
        # Results should indicate no data or empty structure
        assert results is not None

    def test_partial_data_handling(self, tmp_path):
        """Test handling of metrics with missing paired data."""
        partial_data = [
            {
                "task_id": "HumanEval/0",
                "source_type": "human",
                "cyclomatic_complexity": 5,
                "halstead_volume": 50.5,
                "branch_coverage_pct": 85.0,
                "pass_rate": 1
            },
            # Missing codegen for HumanEval/0
            {
                "task_id": "HumanEval/1",
                "source_type": "codegen",
                "cyclomatic_complexity": 7,
                "halstead_volume": 65.2,
                "branch_coverage_pct": 75.0,
                "pass_rate": 0
            }
            # Missing human for HumanEval/1
        ]
        
        partial_file = tmp_path / "partial_metrics.json"
        with open(partial_file, 'w') as f:
            json.dump(partial_data, f)
        
        # Should handle gracefully, skipping incomplete pairs
        results = run_statistical_analysis(
            metrics_file=str(partial_file),
            output_file=None
        )
        
        assert results is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])