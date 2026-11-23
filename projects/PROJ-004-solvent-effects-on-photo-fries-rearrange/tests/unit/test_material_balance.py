"""
Unit tests for material balance report generation (T061).

Verifies that:
  1. Trial configurations are loaded correctly.
  2. Environmental logs are integrated.
  3. Error margins are calculated and propagated correctly.
  4. Output CSV is written with correct structure.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Adjust import path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.material_balance import (
    load_trial_configurations,
    load_environment_logs,
    calculate_material_balance,
    write_material_balance_report,
    run_material_balance_pipeline,
    UNCERTAINTY_SUBSTRATE_MASS_G,
    UNCERTAINTY_SOLVENT_VOLUME_ML
)

class TestMaterialBalance:
    """Test suite for material balance generation."""

    def test_load_trial_configurations_list(self, tmp_path):
        """Test loading trial configurations from a list."""
        trials = [
            {'trial_id': 'T001', 'solvent_name': 'water', 'substrate_mass_g': 0.1},
            {'trial_id': 'T002', 'solvent_name': 'methanol', 'substrate_mass_g': 0.2}
        ]
        config_file = tmp_path / "trial_configurations.json"
        config_file.write_text(json.dumps(trials))
        
        with patch('analysis.material_balance.TRIAL_CONFIG_FILE', str(config_file)):
            loaded = load_trial_configurations()
            
        assert len(loaded) == 2
        assert loaded[0]['trial_id'] == 'T001'
        assert loaded[1]['solvent_name'] == 'methanol'

    def test_load_trial_configurations_dict(self, tmp_path):
        """Test loading trial configurations from a dict with 'trials' key."""
        data = {
            'trials': [
                {'trial_id': 'T001', 'solvent_name': 'water'},
                {'trial_id': 'T002', 'solvent_name': 'methanol'}
            ]
        }
        config_file = tmp_path / "trial_configurations.json"
        config_file.write_text(json.dumps(data))
        
        with patch('analysis.material_balance.TRIAL_CONFIG_FILE', str(config_file)):
            loaded = load_trial_configurations()
            
        assert len(loaded) == 2
        assert loaded[0]['trial_id'] == 'T001'

    def test_load_environment_logs(self, tmp_path):
        """Test loading environmental logs."""
        env_data = [
            {'temperature_c': 25.0, 'relative_humidity_pct': 50.0},
            {'temperature_c': 25.5, 'relative_humidity_pct': 48.0}
        ]
        env_file = tmp_path / "environment_logs.json"
        env_file.write_text(json.dumps(env_data))
        
        with patch('analysis.material_balance.ENV_LOG_FILE', str(env_file)):
            loaded = load_environment_logs()
            
        assert isinstance(loaded, list)
        assert len(loaded) == 2
        assert loaded[0]['temperature_c'] == 25.0

    def test_calculate_material_balance(self):
        """Test material balance calculation with error propagation."""
        trials = [
            {
                'trial_id': 'T001',
                'solvent_name': 'water',
                'solvent_volume_ml': 5.0,
                'substrate_mass_g': 0.050,
                'integration_time_ms': 1000
            }
        ]
        env_logs = [{'temperature_c': 25.0, 'relative_humidity_pct': 50.0}]
        
        records = calculate_material_balance(trials, env_logs)
        
        assert len(records) == 1
        record = records[0]
        
        # Check basic fields
        assert record['trial_id'] == 'T001'
        assert record['solvent_name'] == 'water'
        assert record['solvent_volume_ml'] == 5.0
        assert record['substrate_mass_g'] == 0.050
        
        # Check uncertainty fields are present and non-zero
        assert record['solvent_volume_uncertainty_ml'] == UNCERTAINTY_SOLVENT_VOLUME_ML
        assert record['substrate_mass_uncertainty_g'] == UNCERTAINTY_SUBSTRATE_MASS_G
        assert record['integration_time_uncertainty_ms'] > 0
        
        # Check concentration calculation
        expected_conc = 0.050 / 5.0  # 0.01 g/mL
        assert abs(record['concentration_g_ml'] - expected_conc) < 1e-6
        assert record['concentration_uncertainty_g_ml'] > 0

    def test_calculate_material_balance_zero_volume(self):
        """Test handling of zero solvent volume."""
        trials = [
            {
                'trial_id': 'T002',
                'solvent_name': 'water',
                'solvent_volume_ml': 0.0,
                'substrate_mass_g': 0.050
            }
        ]
        env_logs = []
        
        records = calculate_material_balance(trials, env_logs)
        
        assert len(records) == 1
        record = records[0]
        assert record['concentration_g_ml'] == 0.0
        assert record['concentration_uncertainty_g_ml'] == 0.0

    def test_write_material_balance_report(self, tmp_path):
        """Test writing material balance report to CSV."""
        records = [
            {
                'trial_id': 'T001',
                'timestamp': '2024-01-01T00:00:00',
                'solvent_name': 'water',
                'solvent_volume_ml': 5.0,
                'solvent_volume_uncertainty_ml': 0.05,
                'substrate_mass_g': 0.050,
                'substrate_mass_uncertainty_g': 0.0001,
                'integration_time_ms': 1000,
                'integration_time_uncertainty_ms': 1.0,
                'temperature_c': 25.0,
                'temperature_uncertainty_c': 0.1,
                'relative_humidity_pct': 50.0,
                'relative_humidity_uncertainty_pct': 2.0,
                'barometric_pressure_hPa': 1013.25,
                'concentration_g_ml': 0.01,
                'concentration_uncertainty_g_ml': 0.0002,
                'measurement_source': 'Test',
                'notes': 'Test record'
            }
        ]
        
        output_path = tmp_path / "material_balance_report.csv"
        write_material_balance_report(records, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        assert rows[0]['trial_id'] == 'T001'
        assert rows[0]['concentration_g_ml'] == '0.01'

    def test_run_material_balance_pipeline_with_defaults(self, tmp_path, monkeypatch):
        """Test pipeline execution with no trial configurations (uses defaults)."""
        # Patch paths to use tmp_path
        monkeypatch.setattr('analysis.material_balance.TRIAL_CONFIG_FILE', 
                          str(tmp_path / "nonexistent.json"))
        monkeypatch.setattr('analysis.material_balance.ENV_LOG_FILE', 
                          str(tmp_path / "nonexistent.json"))
        
        # Patch config path
        from config import get_processed_data_path
        processed_path = tmp_path / "processed"
        processed_path.mkdir()
        
        with patch('analysis.material_balance.get_processed_data_path', return_value=processed_path):
            output_path = run_material_balance_pipeline()
        
        assert output_path.exists()
        assert output_path.name == "material_balance_report.csv"
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        # Should have at least one default record
        assert len(rows) >= 1
        assert rows[0]['trial_id'].startswith('DEFAULT')

    def test_error_propagation_correctness(self):
        """Verify that error propagation follows standard formulas."""
        trials = [
            {
                'trial_id': 'T001',
                'solvent_volume_ml': 10.0,
                'substrate_mass_g': 0.100,
            }
        ]
        records = calculate_material_balance(trials, {})
        record = records[0]
        
        # Manual calculation:
        # conc = 0.1 / 10 = 0.01
        # rel_unc_mass = 0.0001 / 0.1 = 0.001
        # rel_unc_vol = 0.05 / 10 = 0.005
        # rel_unc_conc = sqrt(0.001^2 + 0.005^2) = sqrt(0.000001 + 0.000025) = sqrt(0.000026) ≈ 0.0051
        # abs_unc_conc = 0.01 * 0.0051 = 0.000051
        
        expected_rel_unc = ( (0.0001/0.1)**2 + (0.05/10.0)**2 )**0.5
        expected_abs_unc = 0.01 * expected_rel_unc
        
        assert abs(record['concentration_uncertainty_g_ml'] - expected_abs_unc) < 1e-8

if __name__ == "__main__":
    pytest.main([__file__, "-v"])