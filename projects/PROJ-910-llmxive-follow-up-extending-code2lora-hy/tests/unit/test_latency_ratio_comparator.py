"""
Unit tests for the latency ratio comparator (T049b).

Tests:
- Loading of latency files
- Computation of reduction ratio
- Verification of SC-001 requirement (>= 10x)
- Error handling for missing/invalid files
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.utils.latency_ratio_comparator import (
    compute_latency_ratio,
    generate_comparison_report,
    load_json_file,
    RESULTS_DIR
)

class TestComputeLatencyRatio:
    """Tests for compute_latency_ratio function."""
    
    def test_compute_ratio_normal_case(self):
        """Test normal ratio computation."""
        ast_latency = 100.0  # ms
        baseline_latency = 1500.0  # ms
        ratio, status = compute_latency_ratio(ast_latency, baseline_latency)
        
        assert ratio == pytest.approx(15.0, rel=1e-4)
        assert status == "PASS"
    
    def test_compute_ratio_below_threshold(self):
        """Test ratio computation when below 10x threshold."""
        ast_latency = 200.0
        baseline_latency = 1500.0
        ratio, status = compute_latency_ratio(ast_latency, baseline_latency)
        
        assert ratio == pytest.approx(7.5, rel=1e-4)
        assert status == "FAIL"
    
    def test_compute_ratio_exactly_threshold(self):
        """Test ratio computation exactly at 10x threshold."""
        ast_latency = 150.0
        baseline_latency = 1500.0
        ratio, status = compute_latency_ratio(ast_latency, baseline_latency)
        
        assert ratio == pytest.approx(10.0, rel=1e-4)
        assert status == "PASS"
    
    def test_compute_ratio_zero_ast_latency_raises(self):
        """Test that zero AST latency raises ValueError."""
        with pytest.raises(ValueError, match="AST latency must be positive"):
            compute_latency_ratio(0.0, 1500.0)
    
    def test_compute_ratio_negative_baseline_raises(self):
        """Test that negative baseline latency raises ValueError."""
        with pytest.raises(ValueError, match="Baseline latency must be positive"):
            compute_latency_ratio(100.0, -1500.0)

class TestGenerateComparisonReport:
    """Tests for generate_comparison_report function."""
    
    def test_report_structure(self):
        """Test that report contains all required fields."""
        ast_latency = 100.0
        baseline_latency = 1500.0
        ratio = 15.0
        status = "PASS"
        
        report = generate_comparison_report(ast_latency, baseline_latency, ratio, status)
        
        required_fields = [
            "ast_generation_latency_ms",
            "baseline_generation_latency_ms",
            "latency_reduction_ratio",
            "reduction_percentage",
            "sc_001_requirement",
            "meets_requirement",
            "status",
            "message"
        ]
        
        for field in required_fields:
            assert field in report, f"Missing field: {field}"
    
    def test_report_values(self):
        """Test that report values are computed correctly."""
        ast_latency = 100.0
        baseline_latency = 1500.0
        ratio = 15.0
        status = "PASS"
        
        report = generate_comparison_report(ast_latency, baseline_latency, ratio, status)
        
        assert report["ast_generation_latency_ms"] == ast_latency
        assert report["baseline_generation_latency_ms"] == baseline_latency
        assert report["latency_reduction_ratio"] == pytest.approx(ratio, rel=1e-4)
        assert report["meets_requirement"] is True
        assert report["status"] == "PASS"
        
        # Check reduction percentage: (1500-100)/1500 * 100 = 93.33%
        expected_percentage = ((baseline_latency - ast_latency) / baseline_latency) * 100
        assert report["reduction_percentage"] == pytest.approx(expected_percentage, rel=1e-2)
    
    def test_report_fail_status(self):
        """Test report generation with FAIL status."""
        ast_latency = 200.0
        baseline_latency = 1500.0
        ratio = 7.5
        status = "FAIL"
        
        report = generate_comparison_report(ast_latency, baseline_latency, ratio, status)
        
        assert report["meets_requirement"] is False
        assert report["status"] == "FAIL"

class TestLoadJsonFile:
    """Tests for load_json_file function."""
    
    def test_load_valid_json(self):
        """Test loading a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            temp_path = Path(f.name)
        
        try:
            result = load_json_file(temp_path)
            assert result == {"key": "value"}
        finally:
            os.unlink(temp_path)
    
    def test_load_nonexistent_file_raises(self):
        """Test that loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_json_file(Path("/nonexistent/path/file.json"))
    
    def test_load_invalid_json_raises(self):
        """Test that loading invalid JSON raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json {{{")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_json_file(temp_path)
        finally:
            os.unlink(temp_path)

class TestIntegration:
    """Integration-style tests for the full workflow."""
    
    def test_end_to_end_pass_case(self, tmp_path):
        """Test end-to-end workflow with passing case."""
        # Create temporary results directory
        temp_results = tmp_path / "data" / "results"
        temp_results.mkdir(parents=True)
        
        # Create mock AST latency file
        ast_file = temp_results / "generation_latency.json"
        ast_file.write_text(json.dumps({"generation_latency_ms": 100.0}))
        
        # Create mock baseline latency file
        baseline_file = temp_results / "baseline_generation_latency.json"
        baseline_file.write_text(json.dumps({"generation_latency_ms": 1500.0}))
        
        # Temporarily override RESULTS_DIR for testing
        import code.utils.latency_ratio_comparator as module
        original_results_dir = module.RESULTS_DIR
        module.RESULTS_DIR = temp_results
        
        try:
            from code.utils.latency_ratio_comparator import run_latency_comparison
            result = run_latency_comparison()
            
            assert result["meets_requirement"] is True
            assert result["latency_reduction_ratio"] == pytest.approx(15.0, rel=1e-4)
            
            # Verify output file was created
            output_file = temp_results / "generation_latency_comparison.json"
            assert output_file.exists()
            
            with open(output_file) as f:
                saved_report = json.load(f)
            
            assert saved_report["status"] == "PASS"
        finally:
            module.RESULTS_DIR = original_results_dir
    
    def test_end_to_end_fail_case(self, tmp_path):
        """Test end-to-end workflow with failing case."""
        temp_results = tmp_path / "data" / "results"
        temp_results.mkdir(parents=True)
        
        ast_file = temp_results / "generation_latency.json"
        ast_file.write_text(json.dumps({"generation_latency_ms": 200.0}))
        
        baseline_file = temp_results / "baseline_generation_latency.json"
        baseline_file.write_text(json.dumps({"generation_latency_ms": 1500.0}))
        
        import code.utils.latency_ratio_comparator as module
        original_results_dir = module.RESULTS_DIR
        module.RESULTS_DIR = temp_results
        
        try:
            from code.utils.latency_ratio_comparator import run_latency_comparison
            result = run_latency_comparison()
            
            assert result["meets_requirement"] is False
            assert result["status"] == "FAIL"
        finally:
            module.RESULTS_DIR = original_results_dir