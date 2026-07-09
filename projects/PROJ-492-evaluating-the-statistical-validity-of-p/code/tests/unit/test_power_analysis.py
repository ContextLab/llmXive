"""
Unit tests for power analysis utility (FR-025).
"""
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result,
    MIN_CORPUS_SIZE,
    CLAIM_ID
)
from code.src.models.data_models import AuditRecord

class TestCalculateSampleSizeBinary:
    """Tests for binary outcome sample size calculation."""
    
    def test_basic_calculation(self):
        """Test basic sample size calculation."""
        n = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)
        
    def test_larger_effect_smaller_sample(self):
        """Larger effect size should require smaller sample."""
        n_small_effect = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.02,
            alpha=0.05,
            power=0.80
        )
        n_large_effect = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.10,
            alpha=0.05,
            power=0.80
        )
        assert n_large_effect < n_small_effect
        
    def test_higher_power_larger_sample(self):
        """Higher power should require larger sample."""
        n_low_power = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.05,
            alpha=0.05,
            power=0.80
        )
        n_high_power = calculate_sample_size_binary(
            baseline=0.10,
            effect_size=0.05,
            alpha=0.05,
            power=0.95
        )
        assert n_high_power > n_low_power
        
    def test_invalid_baseline(self):
        """Test that invalid baseline raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline=1.5,  # Invalid
                effect_size=0.05,
                alpha=0.05,
                power=0.80
            )
            
    def test_invalid_effect_size(self):
        """Test that invalid effect size raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline=0.10,
                effect_size=-0.05,  # Invalid
                alpha=0.05,
                power=0.80
            )

class TestCalculateSampleSizeContinuous:
    """Tests for continuous outcome sample size calculation."""
    
    def test_basic_calculation(self):
        """Test basic continuous sample size calculation."""
        n = calculate_sample_size_continuous(
            baseline_mean=100.0,
            effect_size=5.0,
            baseline_std=15.0,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, int)
        
    def test_larger_effect_smaller_sample(self):
        """Larger effect size should require smaller sample."""
        n_small = calculate_sample_size_continuous(
            baseline_mean=100.0,
            effect_size=2.0,
            baseline_std=15.0,
            alpha=0.05,
            power=0.80
        )
        n_large = calculate_sample_size_continuous(
            baseline_mean=100.0,
            effect_size=10.0,
            baseline_std=15.0,
            alpha=0.05,
            power=0.80
        )
        assert n_large < n_small

class TestCountCorpusSize:
    """Tests for corpus size counting."""
    
    def test_count_from_list(self):
        """Test counting records from a list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}, {"id": 3}], f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 3
        finally:
            temp_path.unlink()
            
    def test_count_from_dict_with_records(self):
        """Test counting records from dict with 'records' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"records": [{"id": 1}, {"id": 2}]}, f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 2
        finally:
            temp_path.unlink()
            
    def test_file_not_found(self):
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            count_corpus_size(Path("/nonexistent/path.json"))

class TestRunPowerAnalysis:
    """Integration tests for run_power_analysis."""
    
    def test_creates_output_file(self):
        """Test that output file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power.json"
            
            result = run_power_analysis(
                audit_report_path=None,
                output_path=output_path,
                baseline=0.10,
                effect_size=0.05
            )
            
            assert output_path.exists()
            assert result["minimum_sample_size_per_group"] > 0
            assert result["corpus_validation"]["minimum_required"] == MIN_CORPUS_SIZE
            
    def test_validates_corpus_size(self):
        """Test corpus size validation with a mock audit report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock audit report with enough records
            audit_path = Path(tmpdir) / "audit_report.json"
            mock_records = [{"id": i} for i in range(MIN_CORPUS_SIZE + 100)]
            with open(audit_path, 'w') as f:
                json.dump(mock_records, f)
                
            output_path = Path(tmpdir) / "test_power.json"
            
            result = run_power_analysis(
                audit_report_path=audit_path,
                output_path=output_path,
                baseline=0.10,
                effect_size=0.05
            )
            
            assert result["corpus_validation"]["meets_requirement"] is True
            assert result["corpus_validation"]["actual_corpus_size"] > MIN_CORPUS_SIZE
            
    def test_fails_when_corpus_too_small(self):
        """Test corpus validation fails when corpus is too small."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock audit report with too few records
            audit_path = Path(tmpdir) / "audit_report.json"
            mock_records = [{"id": i} for i in range(100)]  # Way below MIN_CORPUS_SIZE
            with open(audit_path, 'w') as f:
                json.dump(mock_records, f)
                
            output_path = Path(tmpdir) / "test_power.json"
            
            result = run_power_analysis(
                audit_report_path=audit_path,
                output_path=output_path,
                baseline=0.10,
                effect_size=0.05
            )
            
            assert result["corpus_validation"]["meets_requirement"] is False
            assert result["corpus_validation"]["validation_error"] is not None
            assert CLAIM_ID in result["corpus_validation"]["validation_error"]

class TestWritePowerAnalysisResult:
    """Tests for writing power analysis results."""
    
    def test_writes_valid_json(self):
        """Test that results are written as valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "result.json"
            
            result_data = {
                "test": "value",
                "number": 42,
                "nested": {"key": "val"}
            }
            
            write_power_analysis_result(result_data, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                
            assert loaded == result_data