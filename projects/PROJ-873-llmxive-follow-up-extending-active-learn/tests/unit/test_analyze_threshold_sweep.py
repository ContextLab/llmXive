"""
Unit tests for T025a: analyze_threshold_sweep.py

Tests the threshold sweep analysis logic including:
- Result loading and parsing
- Optimal threshold selection
- Output generation
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import asdict

# Import the module under test
import sys
sys.path.insert(0, 'code')
from analyze_threshold_sweep import (
    load_sweep_result,
    find_optimal_threshold,
    calculate_baseline_metrics,
    run_analysis,
    SweepResult,
    ThresholdSweepSummary
)

class TestLoadSweepResult:
    """Tests for load_sweep_result function."""
    
    def test_load_existing_file(self, tmp_path):
        """Test loading an existing result file."""
        test_data = {
            "threshold": 0.95,
            "original_count": 1000,
            "filtered_count": 650,
            "reduction_ratio": 0.35,
            "ndcg_score": 0.95,
            "wasted_call_ratio": 0.195,
            "result_file": "test.json"
        }
        
        result_file = tmp_path / "sweep_threshold_0.95.json"
        with open(result_file, 'w') as f:
            json.dump(test_data, f)
        
        loaded = load_sweep_result(str(result_file))
        assert loaded is not None
        assert loaded['threshold'] == 0.95
        assert loaded['ndcg_score'] == 0.95
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent file returns None."""
        result = load_sweep_result(str(tmp_path / "nonexistent.json"))
        assert result is None
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON."""
        result_file = tmp_path / "invalid.json"
        with open(result_file, 'w') as f:
            f.write("not valid json")
        
        result = load_sweep_result(str(result_file))
        assert result is None

class TestFindOptimalThreshold:
    """Tests for find_optimal_threshold function."""
    
    def test_selects_highest_ndcg_with_min_reduction(self):
        """Test that optimal threshold is selected based on highest NDCG with min reduction."""
        results = [
            SweepResult(0.85, 1000, 850, 0.15, 0.925, 0.255, "file1"),
            SweepResult(0.90, 1000, 750, 0.25, 0.935, 0.225, "file2"),
            SweepResult(0.92, 1000, 700, 0.30, 0.945, 0.210, "file3"),
            SweepResult(0.95, 1000, 650, 0.35, 0.950, 0.195, "file4"),
            SweepResult(0.97, 1000, 600, 0.40, 0.950, 0.180, "file5"),
        ]
        
        optimal = find_optimal_threshold(results, min_reduction_ratio=0.30)
        assert optimal == 0.95  # Highest NDCG with reduction >= 0.30
    
    def test_selects_best_when_no_qualifying(self):
        """Test selection when no thresholds meet minimum reduction."""
        results = [
            SweepResult(0.85, 1000, 950, 0.05, 0.910, 0.300, "file1"),
            SweepResult(0.90, 1000, 900, 0.10, 0.920, 0.280, "file2"),
        ]
        
        optimal = find_optimal_threshold(results, min_reduction_ratio=0.30)
        # Should fall back to best NDCG even if below threshold
        assert optimal == 0.90
    
    def test_empty_results_raises_error(self):
        """Test that empty results list raises ValueError."""
        with pytest.raises(ValueError):
            find_optimal_threshold([], min_reduction_ratio=0.30)
    
    def test_tie_breaking_by_reduction_ratio(self):
        """Test tie-breaking when NDCG scores are equal."""
        results = [
            SweepResult(0.95, 1000, 650, 0.35, 0.950, 0.195, "file1"),
            SweepResult(0.97, 1000, 600, 0.40, 0.950, 0.180, "file2"),
        ]
        
        optimal = find_optimal_threshold(results, min_reduction_ratio=0.30)
        # Both have same NDCG, should prefer higher reduction (0.97)
        assert optimal == 0.97

class TestCalculateBaselineMetrics:
    """Tests for calculate_baseline_metrics function."""
    
    def test_loads_baseline_file(self, tmp_path):
        """Test loading baseline metrics from file."""
        baseline_data = {
            "ndcg_score": 0.92,
            "wasted_call_ratio": 0.28,
            "reduction_ratio": 0.0
        }
        
        baseline_file = tmp_path / "baseline_redundant.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f)
        
        with patch('analyze_threshold_sweep.calculate_baseline_metrics') as mock_func:
            # Mock the file path to point to our test file
            pass
        
        # Direct test with mocked path
        with patch('analyze_threshold_sweep.os.path.exists', return_value=True):
            with patch('analyze_threshold_sweep.open', 
                     mock_open_with_data(json.dumps(baseline_data))):
                result = calculate_baseline_metrics(str(baseline_file))
                assert result['ndcg'] == 0.92
                assert result['wasted_call_ratio'] == 0.28
    
    def test_returns_defaults_when_file_missing(self):
        """Test default values when baseline file is missing."""
        with patch('analyze_threshold_sweep.os.path.exists', return_value=False):
            result = calculate_baseline_metrics()
            assert result['ndcg'] is None
            assert result['wasted_call_ratio'] is None
            assert result['reduction_ratio'] == 0.0

class TestRunAnalysis:
    """Tests for run_analysis function."""
    
    def test_generates_correct_output_structure(self, tmp_path):
        """Test that output JSON has correct structure."""
        # Create mock result files
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        for threshold in [0.85, 0.90, 0.92, 0.95, 0.97]:
            result_data = {
                "threshold": threshold,
                "original_count": 1000,
                "filtered_count": int(1000 * (1 - threshold)),
                "reduction_ratio": threshold,
                "ndcg_score": 0.9 + (threshold * 0.05),
                "wasted_call_ratio": 0.3 - (threshold * 0.1),
                "result_file": f"sweep_threshold_{threshold}.json"
            }
            
            with open(results_dir / f"sweep_threshold_{threshold:.2f}.json", 'w') as f:
                json.dump(result_data, f)
        
        output_file = tmp_path / "output.json"
        
        result = run_analysis(
            sweep_dir=str(results_dir),
            output_file=str(output_file),
            dataset_name="test_dataset"
        )
        
        assert result['dataset'] == "test_dataset"
        assert len(result['thresholds_tested']) == 5
        assert 'optimal_threshold' in result
        assert 'results' in result
        assert len(result['results']) == 5
        
        # Verify output file was created
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['dataset'] == "test_dataset"
        assert saved_data['optimal_threshold'] in result['thresholds_tested']

class TestSweepResultDataclass:
    """Tests for SweepResult dataclass."""
    
    def test_serialization(self):
        """Test that SweepResult can be serialized to dict."""
        result = SweepResult(
            threshold=0.95,
            original_count=1000,
            filtered_count=650,
            reduction_ratio=0.35,
            ndcg_score=0.95,
            wasted_call_ratio=0.195,
            result_file="test.json"
        )
        
        as_dict = asdict(result)
        assert as_dict['threshold'] == 0.95
        assert as_dict['ndcg_score'] == 0.95
        assert as_dict['reduction_ratio'] == 0.35

# Helper for mocking file open
def mock_open_with_data(data):
    from unittest.mock import mock_open
    m = mock_open(read_data=data)
    return m

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
