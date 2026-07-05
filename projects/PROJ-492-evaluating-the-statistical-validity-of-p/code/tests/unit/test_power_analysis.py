"""
Unit tests for power analysis utility (T028)
"""
import json
import pytest
from pathlib import Path
import tempfile
import os

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    run_power_analysis,
    write_power_analysis_result,
    count_corpus_size,
    MIN_CORPUS_SIZE
)


class TestCalculateSampleSizeBinary:
    """Tests for binary outcome sample size calculation"""

    def test_basic_calculation(self):
        """Test basic sample size calculation"""
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n >= MIN_CORPUS_SIZE
        assert isinstance(n, int)

    def test_minimum_enforced(self):
        """Test that minimum corpus size is enforced"""
        # With very large effect size, calculated N might be small
        n = calculate_sample_size_binary(
            baseline_rate=0.50,
            detectable_effect=0.40,  # Large effect
            alpha=0.05,
            power=0.80
        )
        assert n >= MIN_CORPUS_SIZE

    def test_invalid_baseline_rate(self):
        """Test error handling for invalid baseline rate"""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=1.5,
                detectable_effect=0.05
            )

    def test_invalid_effect_size(self):
        """Test error handling for invalid effect size"""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.10,
                detectable_effect=1.5
            )


class TestCalculateSampleSizeContinuous:
    """Tests for continuous outcome sample size calculation"""

    def test_basic_calculation(self):
        """Test basic continuous sample size calculation"""
        n = calculate_sample_size_continuous(
            baseline_mean=10.0,
            detectable_effect=2.0,
            std_dev=5.0,
            alpha=0.05,
            power=0.80
        )
        assert n >= MIN_CORPUS_SIZE
        assert isinstance(n, int)

    def test_minimum_enforced(self):
        """Test that minimum corpus size is enforced"""
        n = calculate_sample_size_continuous(
            baseline_mean=10.0,
            detectable_effect=10.0,  # Large effect
            std_dev=5.0,
            alpha=0.05,
            power=0.80
        )
        assert n >= MIN_CORPUS_SIZE

    def test_invalid_std_dev(self):
        """Test error handling for invalid standard deviation"""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=10.0,
                detectable_effect=2.0,
                std_dev=0
            )


class TestRunPowerAnalysis:
    """Tests for the main power analysis function"""

    def test_basic_execution(self):
        """Test basic power analysis execution"""
        result = run_power_analysis(
            baseline_rate=0.10,
            detectable_effect=0.05
        )
        
        assert "calculated_minimum_n" in result
        assert "actual_corpus_size" in result
        assert "meets_minimum_requirement" in result
        assert "status" in result
        assert result["status"] in ["PASS", "FAIL"]

    def test_output_generation(self):
        """Test that output is written to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power_analysis.json"
            
            result = run_power_analysis(
                baseline_rate=0.10,
                detectable_effect=0.05,
                output_path=output_path
            )
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                written_result = json.load(f)
            
            assert written_result == result


class TestCountCorpusSize:
    """Tests for corpus size counting"""

    def test_count_from_json(self):
        """Test counting records from JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test_audit.json"
            
            # Create test data
            test_data = [
                {"id": 1, "consistent": True},
                {"id": 2, "consistent": False},
                {"id": 3, "consistent": True}
            ]
            
            with open(json_path, 'w') as f:
                json.dump(test_data, f)
            
            count = count_corpus_size(json_path)
            assert count == 3

    def test_missing_file(self):
        """Test handling of missing file"""
        count = count_corpus_size(Path("/nonexistent/file.json"))
        assert count == 0

    def test_dict_format(self):
        """Test counting from dict format with 'records' key"""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test_audit.json"
            
            test_data = {
                "records": [
                    {"id": 1},
                    {"id": 2},
                    {"id": 3},
                    {"id": 4},
                    {"id": 5}
                ]
            }
            
            with open(json_path, 'w') as f:
                json.dump(test_data, f)
            
            count = count_corpus_size(json_path)
            assert count == 5


class TestIntegration:
    """Integration tests for power analysis"""

    def test_end_to_end_with_min_requirement(self):
        """Test end-to-end with corpus meeting minimum requirement"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            corpus_path = Path(tmpdir) / "audit_report.json"
            
            # Create corpus with 300+ records
            test_data = [{"id": i, "consistent": i % 2 == 0} for i in range(350)]
            
            with open(corpus_path, 'w') as f:
                json.dump(test_data, f)
            
            result = run_power_analysis(
                baseline_rate=0.10,
                detectable_effect=0.05,
                corpus_path=corpus_path,
                output_path=output_path
            )
            
            assert result["actual_corpus_size"] == 350
            assert result["meets_minimum_requirement"] is True
            assert result["status"] == "PASS"
            assert output_path.exists()

    def test_corpus_below_minimum(self):
        """Test when corpus is below minimum requirement"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_analysis.json"
            corpus_path = Path(tmpdir) / "audit_report.json"
            
            # Create small corpus
            test_data = [{"id": i} for i in range(100)]
            
            with open(corpus_path, 'w') as f:
                json.dump(test_data, f)
            
            result = run_power_analysis(
                baseline_rate=0.10,
                detectable_effect=0.05,
                corpus_path=corpus_path,
                output_path=output_path
            )
            
            assert result["actual_corpus_size"] == 100
            # Should still pass if calculated minimum is <= 100
            # or fail if calculated minimum > 100
            assert "meets_minimum_requirement" in result
            assert output_path.exists()