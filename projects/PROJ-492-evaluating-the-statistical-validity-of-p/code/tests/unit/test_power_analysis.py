import json
import pytest
from pathlib import Path
import tempfile
import shutil

from code.src.audit.power_analysis import (
    calculate_sample_size_binary,
    calculate_sample_size_continuous,
    count_corpus_size,
    write_power_analysis_result,
    run_power_analysis,
    CLAIM_CORPUS_SIZE_THRESHOLD
)
from code.src.config import SEED

class TestPowerAnalysis:

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def sample_audit_report(self, temp_dir):
        """Create a sample audit report JSON file."""
        report_path = temp_dir / "audit_report.json"
        sample_data = [
            {"id": 1, "consistent": True},
            {"id": 2, "consistent": False},
            {"id": 3, "consistent": True}
        ]
        with open(report_path, 'w') as f:
            json.dump(sample_data, f)
        return report_path

    def test_calculate_sample_size_binary_valid_inputs(self):
        """Test binary sample size calculation with valid inputs."""
        n = calculate_sample_size_binary(
            baseline_rate=0.10,
            detectable_effect=0.05,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, (int, float))

    def test_calculate_sample_size_binary_invalid_baseline(self):
        """Test that invalid baseline rate raises ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=1.5,  # Invalid: > 1
                detectable_effect=0.05,
                alpha=0.05,
                power=0.80
            )

    def test_calculate_sample_size_binary_invalid_effect(self):
        """Test that invalid detectable effect raises ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_binary(
                baseline_rate=0.10,
                detectable_effect=1.5,  # Invalid: > 1
                alpha=0.05,
                power=0.80
            )

    def test_calculate_sample_size_continuous_valid_inputs(self):
        """Test continuous sample size calculation with valid inputs."""
        n = calculate_sample_size_continuous(
            baseline_mean=100.0,
            detectable_effect=10.0,
            baseline_std=20.0,
            alpha=0.05,
            power=0.80
        )
        assert n > 0
        assert isinstance(n, (int, float))

    def test_calculate_sample_size_continuous_invalid_std(self):
        """Test that non-positive standard deviation raises ValueError."""
        with pytest.raises(ValueError):
            calculate_sample_size_continuous(
                baseline_mean=100.0,
                detectable_effect=10.0,
                baseline_std=0.0,  # Invalid: not positive
                alpha=0.05,
                power=0.80
            )

    def test_count_corpus_size_from_list(self, temp_dir):
        """Test counting records from a list-based audit report."""
        report_path = temp_dir / "report.json"
        with open(report_path, 'w') as f:
            json.dump([{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}], f)

        count = count_corpus_size(report_path)
        assert count == 4

    def test_count_corpus_size_missing_file(self, temp_dir):
        """Test counting when file does not exist."""
        missing_path = temp_dir / "nonexistent.json"
        count = count_corpus_size(missing_path)
        assert count == 0

    def test_write_power_analysis_result(self, temp_dir):
        """Test writing power analysis results to JSON."""
        output_path = temp_dir / "power_analysis.json"

        write_power_analysis_result(
            output_path=output_path,
            sample_size_binary=100.0,
            sample_size_continuous=200.0,
            corpus_size=500,
            meets_claim=True
        )

        assert output_path.exists()
        with open(output_path, 'r') as f:
            result = json.load(f)

        assert result["sample_size_binary_per_group"] == 100.0
        assert result["sample_size_continuous_per_group"] == 200.0
        assert result["actual_corpus_size"] == 500
        assert result["meets_claim_requirement"] is True
        assert result["claim_reference"] == "2510.17487 (https://arxiv.org/abs/2510.17487)"

    def test_run_power_analysis_creates_output(self, temp_dir):
        """Test that run_power_analysis creates the output file."""
        # Create a sample audit report
        audit_path = temp_dir / "audit_report.json"
        with open(audit_path, 'w') as f:
            json.dump([{"id": i} for i in range(3000)], f)  # 3000 records

        output_path = temp_dir / "power_analysis.json"

        result = run_power_analysis(
            audit_report_path=audit_path,
            output_path=output_path,
            baseline_rate=0.10,
            detectable_effect_binary=0.05,
            baseline_mean=100.0,
            detectable_effect_continuous=10.0,
            baseline_std=20.0
        )

        assert output_path.exists()
        assert result["corpus_size"] == 3000
        assert result["meets_claim"] is True  # 3000 >= 2511

    def test_run_power_analysis_with_small_corpus(self, temp_dir):
        """Test run_power_analysis with corpus below claim threshold."""
        # Create a small audit report
        audit_path = temp_dir / "audit_report.json"
        with open(audit_path, 'w') as f:
            json.dump([{"id": i} for i in range(100)], f)  # 100 records

        output_path = temp_dir / "power_analysis.json"

        result = run_power_analysis(
            audit_report_path=audit_path,
            output_path=output_path
        )

        assert result["corpus_size"] == 100
        assert result["meets_claim"] is False  # 100 < 2511

    def test_claim_threshold_value(self):
        """Verify the claim threshold is set correctly."""
        assert CLAIM_CORPUS_SIZE_THRESHOLD == 2511.0