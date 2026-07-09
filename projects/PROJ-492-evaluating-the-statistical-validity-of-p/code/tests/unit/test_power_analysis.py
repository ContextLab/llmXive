"""
Unit tests for power_analysis.py
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
    CORPUS_MIN_SIZE_THRESHOLD
)


class TestSampleSizeBinary:
    def test_basic_calculation(self):
        """Test basic sample size calculation for binary outcome."""
        baseline = 0.10
        effect = 0.05
        n_per_group, stats = calculate_sample_size_binary(baseline, effect)
        
        assert n_per_group > 0
        assert stats["baseline_rate"] == baseline
        assert stats["treatment_rate"] == baseline + effect
        assert stats["delta"] == effect
        assert "total_n" in stats
        assert stats["total_n"] == 2 * n_per_group

    def test_high_baseline(self):
        """Test with high baseline rate."""
        baseline = 0.50
        effect = 0.05
        n_per_group, _ = calculate_sample_size_binary(baseline, effect)
        
        # Higher baseline usually requires smaller N for same absolute effect
        # compared to very low baseline, but variance is maximized at 0.5
        assert n_per_group > 0

    def test_invalid_baseline(self):
        """Test that invalid baseline raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(1.5, 0.05)
        
        with pytest.raises(ValueError):
            calculate_sample_size_binary(-0.1, 0.05)

    def test_invalid_effect(self):
        """Test that invalid effect raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.1, 1.5)

    def test_resulting_rate_out_of_bounds(self):
        """Test that effect making p2 > 1 raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.95, 0.10)  # p2 = 1.05


class TestSampleSizeContinuous:
    def test_basic_calculation(self):
        """Test basic sample size calculation for continuous outcome."""
        baseline = 10.0
        effect = 2.0
        std = 5.0
        n_per_group, stats = calculate_sample_size_continuous(baseline, effect, std)
        
        assert n_per_group > 0
        assert stats["effect_size_d"] == effect / std
        assert stats["total_n"] == 2 * n_per_group

    def test_invalid_std(self):
        """Test that invalid std dev raises error."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(10.0, 2.0, -1.0)
        
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(10.0, 2.0, 0.0)


class TestCorpusSize:
    def test_count_list(self):
        """Test counting records from a list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            data = [{"id": 1}, {"id": 2}, {"id": 3}]
            with open(path, 'w') as f:
                json.dump(data, f)
            
            count = count_corpus_size(path)
            assert count == 3

    def test_count_dict_records(self):
        """Test counting from dict with 'records' key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            data = {"records": [{"id": 1}, {"id": 2}]}
            with open(path, 'w') as f:
                json.dump(data, f)
            
            count = count_corpus_size(path)
            assert count == 2

    def test_count_dict_keys(self):
        """Test counting top-level dict keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            data = {"id1": {}, "id2": {}}
            with open(path, 'w') as f:
                json.dump(data, f)
            
            count = count_corpus_size(path)
            assert count == 2

    def test_missing_file(self):
        """Test handling of missing file."""
        count = count_corpus_size(Path("/nonexistent/file.json"))
        assert count == 0


class TestRunPowerAnalysis:
    def test_full_run(self):
        """Test the full power analysis pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Create a dummy audit report with enough records to pass threshold
            # Threshold is 2510 per arXiv:2510.17487
            dummy_records = [{"id": i, "consistent": True} for i in range(3000)]
            with open(input_path, 'w') as f:
                json.dump(dummy_records, f)
            
            result = run_power_analysis(
                audit_report_path=input_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.05
            )
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify result structure
            assert "parameters" in result
            assert "calculated_requirements" in result
            assert "corpus_statistics" in result
            assert "validation_status" in result
            
            # Verify threshold check
            assert result["corpus_statistics"]["actual_size"] == 3000
            assert result["corpus_statistics"]["meets_arxiv_2510_17487_threshold"] is True
            
            # Verify output file content
            with open(output_path, 'r') as f:
                saved_result = json.load(f)
            
            assert saved_result["corpus_statistics"]["actual_size"] == 3000

    def test_below_threshold(self):
        """Test when corpus size is below threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "audit_report.json"
            output_path = Path(tmpdir) / "power_analysis.json"
            
            # Create a dummy audit report with fewer records
            dummy_records = [{"id": i} for i in range(100)]
            with open(input_path, 'w') as f:
                json.dump(dummy_records, f)
            
            result = run_power_analysis(
                audit_report_path=input_path,
                output_path=output_path,
                baseline_rate=0.10,
                detectable_effect=0.05
            )
            
            assert result["corpus_statistics"]["meets_arxiv_2510_17487_threshold"] is False
            assert result["validation_status"] == "WARNING"
            
            with open(output_path, 'r') as f:
                saved_result = json.load(f)
            
            assert saved_result["corpus_statistics"]["actual_size"] == 100
            assert saved_result["corpus_statistics"]["meets_arxiv_2510_17487_threshold"] is False


class TestConstants:
    def test_threshold_value(self):
        """Verify the threshold value matches the claim."""
        # Claim c_21f3e400 references arXiv:2510.17487 suggesting 2510 samples
        assert CORPUS_MIN_SIZE_THRESHOLD == 2510
