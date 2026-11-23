"""
Unit tests for sample quantity tracking (T053).
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from analysis.sample_tracker import (
    validate_significant_figures,
    record_trial_quantities,
    generate_material_balance_report,
    MaterialBalanceError
)

class TestValidateSignificantFigures:
    def test_valid_positive_value(self):
        is_valid, msg = validate_significant_figures(5.00, 3, "Volume")
        assert is_valid is True
        assert "validated" in msg

    def test_valid_mass(self):
        is_valid, msg = validate_significant_figures(0.1250, 4, "Mass")
        assert is_valid is True
        assert "validated" in msg

    def test_invalid_negative(self):
        is_valid, msg = validate_significant_figures(-1.0, 3, "Volume")
        assert is_valid is False
        assert "positive" in msg

    def test_invalid_zero(self):
        is_valid, msg = validate_significant_figures(0.0, 3, "Volume")
        assert is_valid is False
        assert "positive" in msg

class TestRecordTrialQuantities:
    def test_successful_recording(self):
        record = record_trial_quantities(
            solvent_name="cyclohexane",
            solvent_volume_ml=5.00,
            substrate_mass_g=0.1250,
            integration_time_ms=100.0,
            temperature_c=25.0,
            run_id="TEST-001"
        )

        assert record["run_id"] == "TEST-001"
        assert record["solvent_name"] == "cyclohexane"
        assert record["solvent_volume_ml"] == 5.00
        assert record["substrate_mass_g"] == 0.1250
        assert record["integration_time_ms"] == 100.0
        assert record["temperature_c"] == 25.0
        assert record["validation_passed"] is True
        assert len(record["validations"]) == 4

    def test_invalid_volume_rejected(self):
        with pytest.raises(MaterialBalanceError):
            record_trial_quantities(
                solvent_name="methanol",
                solvent_volume_ml=-1.0,  # Invalid: negative
                substrate_mass_g=0.1250,
                integration_time_ms=100.0,
                temperature_c=25.0,
                run_id="TEST-002"
            )

    def test_invalid_mass_rejected(self):
        with pytest.raises(MaterialBalanceError):
            record_trial_quantities(
                solvent_name="acetonitrile",
                solvent_volume_ml=5.00,
                substrate_mass_g=0.0,  # Invalid: zero
                integration_time_ms=100.0,
                temperature_c=25.0,
                run_id="TEST-003"
            )

    def test_timestamp_generation(self):
        record = record_trial_quantities(
            solvent_name="toluene",
            solvent_volume_ml=5.00,
            substrate_mass_g=0.1250,
            integration_time_ms=100.0,
            temperature_c=25.0,
            run_id="TEST-004"
        )

        assert "timestamp" in record
        assert record["timestamp"] is not None

class TestGenerateMaterialBalanceReport:
    def test_report_generation(self):
        records = [
            {
                "run_id": "RUN-001",
                "solvent_name": "cyclohexane",
                "solvent_volume_ml": 5.00,
                "substrate_mass_g": 0.1250,
                "integration_time_ms": 100.0,
                "temperature_c": 25.0,
                "validation_passed": True,
                "validations": []
            },
            {
                "run_id": "RUN-002",
                "solvent_name": "methanol",
                "solvent_volume_ml": 5.00,
                "substrate_mass_g": 0.1250,
                "integration_time_ms": 100.0,
                "temperature_c": 25.0,
                "validation_passed": True,
                "validations": []
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            report = generate_material_balance_report(records, output_path)

            # Verify report structure
            assert "generated_at" in report
            assert "total_runs" in report
            assert report["total_runs"] == 2
            assert "summary_statistics" in report
            assert "compliance_status" in report
            assert report["compliance_status"] == "PASS"

            # Verify file was written
            assert output_path.exists()
            with open(output_path, 'r') as f:
                written_data = json.load(f)
            assert written_data["total_runs"] == 2

        finally:
            output_path.unlink(missing_ok=True)

    def test_report_with_failures(self):
        records = [
            {
                "run_id": "RUN-001",
                "solvent_volume_ml": 5.00,
                "substrate_mass_g": 0.1250,
                "validation_passed": True,
                "validations": []
            },
            {
                "run_id": "RUN-002",
                "solvent_volume_ml": 5.00,
                "substrate_mass_g": 0.1250,
                "validation_passed": False,
                "validations": []
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            report = generate_material_balance_report(records, output_path)

            assert report["validations_passed"] == 1
            assert report["validations_failed"] == 1
            assert report["compliance_status"] == "FAIL"

        finally:
            output_path.unlink(missing_ok=True)

    def test_empty_records_raises_error(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            with pytest.raises(MaterialBalanceError):
                generate_material_balance_report([], output_path)
        finally:
            output_path.unlink(missing_ok=True)
