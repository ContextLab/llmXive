import json
import pytest
from pathlib import Path
import tempfile
import os

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    run_power_analysis,
    count_corpus_size,
    write_power_analysis_result
)
from code.src.config import SEED


class TestSampleSizeCalculations:
    def test_calculate_sample_size_binary_valid_inputs(self):
        """Test binary sample size calculation with valid inputs."""
        p0 = 0.10
        p1 = 0.15
        n = calculate_sample_size_binary(p0, p1)
        assert n > 0
        assert isinstance(n, float)

    def test_calculate_sample_size_binary_small_effect(self):
        """Test that smaller effect sizes require larger sample sizes."""
        n_small_effect = calculate_sample_size_binary(0.10, 0.11)
        n_large_effect = calculate_sample_size_binary(0.10, 0.20)
        assert n_small_effect > n_large_effect

    def test_calculate_sample_size_binary_invalid_p0(self):
        """Test that invalid p0 raises ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.0, 0.1)
        with pytest.raises(ValueError):
            calculate_sample_size_binary(1.0, 0.9)

    def test_calculate_sample_size_binary_invalid_delta(self):
        """Test that zero effect size raises ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(0.10, 0.10)

    def test_calculate_sample_size_continuous_valid_inputs(self):
        """Test continuous sample size calculation with valid inputs."""
        mu0 = 100
        mu1 = 105
        sigma = 15
        n = calculate_sample_size_continuous(mu0, mu1, sigma)
        assert n > 0
        assert isinstance(n, float)

    def test_calculate_sample_size_continuous_small_effect(self):
        """Test that smaller effect sizes require larger sample sizes."""
        n_small_effect = calculate_sample_size_continuous(100, 101, 15)
        n_large_effect = calculate_sample_size_continuous(100, 110, 15)
        assert n_small_effect > n_large_effect

    def test_calculate_sample_size_continuous_invalid_sigma(self):
        """Test that non-positive sigma raises ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 105, 0)
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(100, 105, -1)


class TestCorpusSizeCounting:
    def test_count_corpus_size_empty_list(self):
        """Test counting records in an empty list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 0
        finally:
            os.unlink(temp_path)

    def test_count_corpus_size_with_records(self):
        """Test counting records in a list with items."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 3
        finally:
            os.unlink(temp_path)

    def test_count_corpus_size_with_nested_records(self):
        """Test counting records in a nested structure."""
        data = {"records": [{"id": 1}, {"id": 2}]}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 2
        finally:
            os.unlink(temp_path)

    def test_count_corpus_size_file_not_found(self):
        """Test handling of non-existent file."""
        count = count_corpus_size(Path("/nonexistent/file.json"))
        assert count == 0

    def test_count_corpus_size_invalid_json(self):
        """Test handling of invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = Path(f.name)
        
        try:
            count = count_corpus_size(temp_path)
            assert count == 0
        finally:
            os.unlink(temp_path)


class TestPowerAnalysisIntegration:
    def test_run_power_analysis_creates_output(self):
        """Test that run_power_analysis creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = run_power_analysis(
                output_dir=output_dir,
                baseline_conversion=0.10,
                detectable_effect=0.05,
                seed=SEED
            )
            
            output_path = output_dir / "power_analysis.json"
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                saved_result = json.load(f)
            
            assert "calculated_sample_size_per_group" in saved_result
            assert "meets_sample_size_requirement" in saved_result
            assert saved_result["parameters"]["baseline_conversion"] == 0.10

    def test_run_power_analysis_with_audit_report(self):
        """Test run_power_analysis with an audit report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create a mock audit report
            audit_data = [{"id": i, "consistent": True} for i in range(100)]
            audit_path = output_dir / "audit_report.json"
            with open(audit_path, 'w') as f:
                json.dump(audit_data, f)
            
            result = run_power_analysis(
                output_dir=output_dir,
                audit_report_path=audit_path,
                baseline_conversion=0.10,
                detectable_effect=0.05,
                seed=SEED
            )
            
            assert result["corpus_size"] == 100
            # The calculated N should be around 600-700 for these parameters
            # So it should not meet the requirement
            assert result["meets_sample_size_requirement"] == False

    def test_run_power_analysis_meets_requirement(self):
        """Test run_power_analysis when corpus meets requirement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create a large mock audit report
            # For baseline=0.10, effect=0.05, alpha=0.05, power=0.80,
            # required N is approximately 600-700 per group
            # So we need at least that many records
            large_data = [{"id": i, "consistent": True} for i in range(1000)]
            audit_path = output_dir / "audit_report.json"
            with open(audit_path, 'w') as f:
                json.dump(large_data, f)
            
            result = run_power_analysis(
                output_dir=output_dir,
                audit_report_path=audit_path,
                baseline_conversion=0.10,
                detectable_effect=0.05,
                seed=SEED
            )
            
            assert result["corpus_size"] == 1000
            # With 1000 records, it should meet the requirement
            assert result["meets_sample_size_requirement"] == True
            assert result["sample_size_gap"] == 0

    def test_run_power_analysis_seed_reproducibility(self):
        """Test that the same seed produces the same results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir1 = Path(tmpdir) / "run1"
            output_dir1.mkdir()
            output_dir2 = Path(tmpdir) / "run2"
            output_dir2.mkdir()
            
            result1 = run_power_analysis(
                output_dir=output_dir1,
                baseline_conversion=0.10,
                detectable_effect=0.05,
                seed=42
            )
            
            result2 = run_power_analysis(
                output_dir=output_dir2,
                baseline_conversion=0.10,
                detectable_effect=0.05,
                seed=42
            )
            
            assert result1["calculated_sample_size_per_group"] == result2["calculated_sample_size_per_group"]


class TestWritePowerAnalysisResult:
    def test_write_power_analysis_result_creates_file(self):
        """Test that write_power_analysis_result creates the file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            result = {"test": "data", "number": 42}
            
            write_power_analysis_result(result, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                saved = json.load(f)
            
            assert saved == result

    def test_write_power_analysis_result_creates_directories(self):
        """Test that write_power_analysis_result creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / "power_analysis.json"
            result = {"test": "data"}
            
            write_power_analysis_result(result, output_path)
            
            assert output_path.exists()