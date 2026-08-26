"""
Unit tests for the halt_check module (T027b).
"""
import json
import tempfile
from pathlib import Path
import pytest

from stats.halt_check import load_power_analysis, check_halt_conditions, write_status_file


class TestLoadPowerAnalysis:
    def test_load_valid_file(self):
        """Test loading a valid power analysis JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"power_for_r03": 0.85, "is_sufficient": True, "n": 100}, f)
            temp_path = Path(f.name)

        try:
            result = load_power_analysis(temp_path)
            assert result["power_for_r03"] == 0.85
            assert result["is_sufficient"] is True
            assert result["n"] == 100
        finally:
            temp_path.unlink()

    def test_load_missing_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_power_analysis(Path("/nonexistent/path/power_analysis.json"))

    def test_load_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                load_power_analysis(temp_path)
        finally:
            temp_path.unlink()


class TestCheckHaltConditions:
    def test_sufficient_power(self):
        """Test that sufficient power returns False (continue)."""
        results = {"power_for_r03": 0.85, "is_sufficient": True, "n": 100}
        assert check_halt_conditions(results) is False

    def test_insufficient_sample_size(self):
        """Test that insufficient sample size returns True (halt)."""
        results = {"power_for_r03": 0.60, "is_sufficient": False, "n": 50}
        assert check_halt_conditions(results) is True

    def test_low_power_with_adequate_sample(self):
        """Test that low power with adequate sample returns True (halt)."""
        results = {"power_for_r03": 0.60, "is_sufficient": False, "n": 100}
        assert check_halt_conditions(results) is True

    def test_boundary_sample_size(self):
        """Test boundary condition at n=85."""
        # n=84 should halt
        results = {"power_for_r03": 0.60, "is_sufficient": False, "n": 84}
        assert check_halt_conditions(results) is True

        # n=85 should halt if power is low
        results = {"power_for_r03": 0.60, "is_sufficient": False, "n": 85}
        assert check_halt_conditions(results) is True

        # n=85 with sufficient power should continue
        results = {"power_for_r03": 0.85, "is_sufficient": True, "n": 85}
        assert check_halt_conditions(results) is False

    def test_override_sample_size(self):
        """Test that sample_size parameter overrides value in results."""
        results = {"power_for_r03": 0.60, "is_sufficient": False, "n": 100}
        # Override n to 50, should halt
        assert check_halt_conditions(results, sample_size=50) is True


class TestWriteStatusFile:
    def test_write_status_file(self):
        """Test writing a status file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "halt_status.json"
            write_status_file(status_path, skip_cognitive=True, reason="Test reason")

            assert status_path.exists()
            with open(status_path, 'r') as f:
                data = json.load(f)

            assert data["skip_cognitive_tasks"] is True
            assert data["reason"] == "Test reason"
            assert "timestamp" in data