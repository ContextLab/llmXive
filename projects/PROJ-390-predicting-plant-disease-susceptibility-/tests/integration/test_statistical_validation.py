"""
Integration test for statistical validation (Task T024).

Verifies validation report structure.
"""
import pytest
import json
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class TestStatisticalValidationIntegration:
    """Integration tests for statistical validation."""

    @pytest.fixture
    def processed_dir(self):
        return project_root / "data" / "processed"

    def test_validation_report_generated(self, processed_dir):
        """Verify validation_report.json is generated (if pipeline ran)."""
        report_path = processed_dir / "validation_report.json"
        if report_path.exists():
            with open(report_path, 'r') as f:
                data = json.load(f)
            assert 'permutation_test' in data
            assert 'sensitivity_analysis' in data
        else:
            pytest.skip("validation_report.json not yet generated (T025 pending)")