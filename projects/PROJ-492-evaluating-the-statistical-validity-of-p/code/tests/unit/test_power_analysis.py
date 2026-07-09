"""
Unit tests for power analysis utility.
"""
import json
import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    run_power_analysis,
    write_power_analysis_result
)
from code.src.config import SEED

class TestCalculateSampleSizeBinary:
    def test_basic_calculation(self):
        """Test basic sample size calculation for binary outcome."""
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.02,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, float)
        # For 10% baseline, 2% effect, 80% power, alpha=0.05
        # Expected n is approximately 3900 per group
        assert 3500 < n < 4500

    def test_invalid_baseline_rate(self):
        """Test that invalid baseline rate raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=1.5,  # Invalid
                detectable_effect=0.02
            )
    
    def test_invalid_effect(self):
        """Test that invalid effect raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.10,
                detectable_effect=1.5  # Invalid
            )
    
    def test_effect_too_large(self):
        """Test that effect making sum > 1 raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.90,
                detectable_effect=0.20  # 0.90 + 0.20 = 1.10 > 1
            )

class TestCalculateSampleSizeContinuous:
    def test_basic_calculation(self):
        """Test basic sample size calculation for continuous outcome."""
        n = calculate_sample_size_continuous(
            baseline_mean=0,
            detectable_effect=0.2,
            std_dev=1.0,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, float)
        # For effect size 0.2 (small), n should be around 394 per group
        assert 350 < n < 450

    def test_invalid_std_dev(self):
        """Test that invalid std_dev raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=0,
                detectable_effect=0.2,
                std_dev=-1.0
            )
    
    def test_zero_std_dev(self):
        """Test that zero std_dev raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=0,
                detectable_effect=0.2,
                std_dev=0.0
            )

class TestCountCorpusSize:
    def test_count_all_records(self):
        """Test counting all records when exclude_inconsistent=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "audit.json"
            test_data = [
                {"id": 1, "is_consistent": True},
                {"id": 2, "is_consistent": False},
                {"id": 3, "is_consistent": True}
            ]
            with open(test_path, 'w') as f:
                json.dump(test_data, f)
            
            count = count_corpus_size(test_path, exclude_inconsistent=False)
            assert count == 3

    def test_count_consistent_only(self):
        """Test counting only consistent records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "audit.json"
            test_data = [
                {"id": 1, "is_consistent": True},
                {"id": 2, "is_consistent": False},
                {"id": 3, "is_consistent": True}
            ]
            with open(test_path, 'w') as f:
                json.dump(test_data, f)
            
            count = count_corpus_size(test_path, exclude_inconsistent=True)
            assert count == 2

    def test_missing_file(self):
        """Test handling of missing file."""
        test_path = Path("/nonexistent/file.json")
        count = count_corpus_size(test_path)
        assert count == 0

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "audit.json"
            with open(test_path, 'w') as f:
                f.write("invalid json")
            
            count = count_corpus_size(test_path)
            assert count == 0

class TestRunPowerAnalysis:
    def test_full_run(self):
        """Test full power analysis run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock audit records
            audit_path = tmpdir_path / "audit_report.json"
            test_data = [
                {"id": i, "is_consistent": True}
                for i in range(5000)  # Simulate 5000 consistent records
            ]
            with open(audit_path, 'w') as f:
                json.dump(test_data, f)
            
            output_path = tmpdir_path / "power_analysis.json"
            
            result = run_power_analysis(
                audit_records_path=audit_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.02,
                alpha=0.05,
                power=0.80
            )
            
            # Verify result structure
            assert "analysis_parameters" in result
            assert "required_sample_sizes" in result
            assert "actual_corpus_size" in result
            assert "validation" in result
            
            # Verify corpus size
            assert result["actual_corpus_size"] == 5000
            
            # Verify output file was created
            assert output_path.exists()
            
            # Verify JSON content
            with open(output_path, 'r') as f:
                saved_result = json.load(f)
            assert saved_result["actual_corpus_size"] == 5000

    def test_insufficient_corpus(self):
        """Test when corpus is too small."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create small mock audit records
            audit_path = tmpdir_path / "audit_report.json"
            test_data = [
                {"id": i, "is_consistent": True}
                for i in range(100)  # Only 100 records
            ]
            with open(audit_path, 'w') as f:
                json.dump(test_data, f)
            
            output_path = tmpdir_path / "power_analysis.json"
            
            result = run_power_analysis(
                audit_records_path=audit_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.02,
                alpha=0.05,
                power=0.80
            )
            
            # Should not meet requirement for 2% effect with 100 records
            assert result["validation"]["meets_binary_requirement"] is False

class TestWritePowerAnalysisResult:
    def test_write_result(self):
        """Test writing result to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "result.json"
            test_result = {"test": "value", "number": 42}
            
            write_power_analysis_result(test_result, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved = json.load(f)
            assert saved == test_result