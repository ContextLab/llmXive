import pytest
import json
from pathlib import Path
import tempfile
import os

from code.data.power_check import (
    load_retention_metrics,
    check_power,
    save_power_check_results,
)


class TestCheckPower:
    def test_passes_power_check(self):
        """Test that power check passes when N is sufficient."""
        n_subjects = 100
        power_threshold = 85

        is_powered, message, warning = check_power(n_subjects, power_threshold)

        assert is_powered is True
        assert "sufficient" in message.lower() or "adequate" in message.lower()
        assert warning is None

    def test_fails_power_check(self):
        """Test that power check fails when N is insufficient."""
        n_subjects = 50
        power_threshold = 85

        is_powered, message, warning = check_power(n_subjects, power_threshold)

        assert is_powered is False
        assert "underpowered" in message.lower() or "insufficient" in message.lower()
        assert warning is not None
        assert "small effects" in warning.lower()

    def test_exact_threshold(self):
        """Test behavior at exact threshold."""
        n_subjects = 85
        power_threshold = 85

        is_powered, message, warning = check_power(n_subjects, power_threshold)

        assert is_powered is True
        assert warning is None

    def test_handles_edge_cases(self):
        """Test behavior with edge case sample sizes."""
        # Very small sample
        is_powered, _, warning = check_power(10, 85)
        assert is_powered is False
        assert warning is not None

        # Large sample
        is_powered, _, warning = check_power(200, 85)
        assert is_powered is True
        assert warning is None


class TestSavePowerCheckResults:
    def test_saves_correctly(self):
        """Test that power check results are saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_check_results.json"
            results = {
                'n_subjects': 100,
                'power_threshold': 85,
                'is_powered': True,
                'message': 'Sample size is sufficient',
                'warning': None
            }

            save_power_check_results(results, str(output_path))

            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_results = json.load(f)

            assert saved_results['n_subjects'] == 100
            assert saved_results['is_powered'] is True

    def test_handles_warning_message(self):
        """Test that warning messages are saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_check_results.json"
            results = {
                'n_subjects': 50,
                'power_threshold': 85,
                'is_powered': False,
                'message': 'Sample size is insufficient',
                'warning': 'Underpowered for small effects (r=0.3)'
            }

            save_power_check_results(results, str(output_path))

            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_results = json.load(f)

            assert saved_results['warning'] == 'Underpowered for small effects (r=0.3)'

    def test_creates_directory_if_not_exists(self):
        """Test that the function creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "output" / "power_check_results.json"
            results = {
                'n_subjects': 100,
                'power_threshold': 85,
                'is_powered': True,
                'message': 'Sample size is sufficient',
                'warning': None
            }

            save_power_check_results(results, str(nested_path))

            assert nested_path.exists()
