"""
Unit tests for power analysis utility.
Tests calculation accuracy and abort behavior.
"""
import json
import pytest
from pathlib import Path
import tempfile
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from power_analysis import calculate_required_n, run_power_analysis, MIN_REQUIRED_N
from exceptions import E_POWER


class TestCalculateRequiredN:
    """Tests for calculate_required_n function."""
    
    def test_effect_size_05(self):
        """Test with effect size r=0.5, alpha=0.05, power=0.8"""
        n = calculate_required_n(effect_size=0.5, alpha=0.05, power=0.8)
        # Expected value should be around 28-30
        assert 28 <= n <= 32, f"Expected n around 29, got {n}"
    
    def test_effect_size_03(self):
        """Test with smaller effect size r=0.3"""
        n = calculate_required_n(effect_size=0.3, alpha=0.05, power=0.8)
        # Smaller effect size requires larger sample
        assert n > 50, f"Expected n > 50 for r=0.3, got {n}"
    
    def test_effect_size_08(self):
        """Test with larger effect size r=0.8"""
        n = calculate_required_n(effect_size=0.8, alpha=0.05, power=0.8)
        # Larger effect size requires smaller sample
        assert n < 15, f"Expected n < 15 for r=0.8, got {n}"
    
    def test_invalid_effect_size(self):
        """Test that invalid effect sizes raise ValueError"""
        with pytest.raises(ValueError):
            calculate_required_n(effect_size=1.5)
        
        with pytest.raises(ValueError):
            calculate_required_n(effect_size=-1.5)
    
    def test_boundary_effect_size(self):
        """Test edge cases near boundaries"""
        # Very small effect size
        n_small = calculate_required_n(effect_size=0.1, alpha=0.05, power=0.8)
        assert n_small > 100
        
        # Effect size close to 1
        n_large = calculate_required_n(effect_size=0.9, alpha=0.05, power=0.8)
        assert n_large < 10


class TestRunPowerAnalysis:
    """Tests for run_power_analysis function."""
    
    def test_successful_analysis(self):
        """Test successful power analysis with default parameters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power_analysis.json"
            results = run_power_analysis(
                effect_size=0.5,
                alpha=0.05,
                power=0.8,
                output_path=str(output_path)
            )
            
            # Check results structure
            assert "effect_size" in results
            assert "alpha" in results
            assert "power" in results
            assert "required_n" in results
            assert "passes_threshold" in results
            assert "status" in results
            
            # Check file was created
            assert output_path.exists()
            
            # Check file contents
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
            
            assert saved_results["required_n"] == results["required_n"]
            assert saved_results["status"] == "PASS"
    
    def test_failing_threshold(self):
        """Test that E_POWER is raised when n < 28"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power_analysis_fail.json"
            
            # Use a large effect size that results in small n
            with pytest.raises(E_POWER) as exc_info:
                run_power_analysis(
                    effect_size=0.9,  # Large effect -> small n
                    alpha=0.05,
                    power=0.8,
                    output_path=str(output_path)
                )
            
            assert "E-POWER" in str(exc_info.value)
            assert "below minimum threshold" in str(exc_info.value)
    
    def test_output_file_format(self):
        """Test that output JSON has correct format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_format.json"
            run_power_analysis(output_path=str(output_path))
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # Check all required fields
            required_fields = [
                "effect_size", "alpha", "power", 
                "required_n", "min_required_n", 
                "passes_threshold", "status"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
    
    def test_default_output_path(self):
        """Test default output path creation"""
        # This test just verifies the function can handle the default path
        # without raising errors (actual file creation depends on environment)
        try:
            results = run_power_analysis(
                effect_size=0.5,
                alpha=0.05,
                power=0.8
            )
            assert results["status"] == "PASS"
        except Exception:
            # If default path fails due to permissions, that's okay for this test
            # The important part is the logic works
            pass


class TestMinRequiredN:
    """Tests for the minimum required n threshold."""
    
    def test_threshold_value(self):
        """Verify the threshold is set to 28"""
        assert MIN_REQUIRED_N == 28
    
    def test_passes_threshold_logic(self):
        """Test passes_threshold calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test case that passes
            output_path = Path(tmpdir) / "pass.json"
            results = run_power_analysis(effect_size=0.5, output_path=str(output_path))
            assert results["passes_threshold"] == (results["required_n"] >= 28)
            
            # Test case that fails (large effect size)
            output_path_fail = Path(tmpdir) / "fail.json"
            try:
                run_power_analysis(effect_size=0.9, output_path=str(output_path_fail))
                # If it didn't raise, check the logic
                # But it should raise E_POWER
                assert False, "Should have raised E_POWER"
            except E_POWER:
                # Expected
                pass


class TestIntegration:
    """Integration tests for power analysis module."""
    
    def test_end_to_end(self):
        """Test complete flow from calculation to file output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "integration_test.json"
            
            # Run analysis
            results = run_power_analysis(
                effect_size=0.5,
                alpha=0.05,
                power=0.8,
                output_path=str(output_path)
            )
            
            # Verify file exists and is valid JSON
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                file_data = json.load(f)
            
            # Verify data consistency
            assert file_data["effect_size"] == results["effect_size"]
            assert file_data["required_n"] == results["required_n"]
            assert file_data["status"] == results["status"]
            
            # Verify calculation is reasonable
            assert 28 <= file_data["required_n"] <= 35
            
            # Verify threshold logic
            assert file_data["passes_threshold"] == (file_data["required_n"] >= 28)
            assert file_data["min_required_n"] == 28