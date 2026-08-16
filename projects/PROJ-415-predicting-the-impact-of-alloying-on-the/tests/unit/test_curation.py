import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
import shutil

# Mock the config and constants for testing
# In a real run, these would be imported from the project
# For unit tests, we mock the behavior or use fixtures

from code.data.curation import exclude_missing_concentration, validate_atomic_radii, log_exclusions

class TestExcludeMissingConcentration:
    def test_exclude_missing_concentration(self):
        # Create a mock dataframe
        data = {
            'row_id': [1, 2, 3, 4],
            'solute_concentration': [0.5, None, 0.2, ''],
            'host_element': ['Cu', 'Cu', 'Cu', 'Cu'],
            'solute_element': ['Zn', 'Zn', 'Zn', 'Zn']
        }
        df = pd.DataFrame(data)
        
        cleaned_df, exclusions = exclude_missing_concentration(df)
        
        assert len(cleaned_df) == 2
        assert len(exclusions) == 2
        assert all(ex['reason_code'] == 'MISSING_CONCENTRATION' for ex in exclusions)
        assert set(cleaned_df['row_id']) == {1, 3}

    def test_no_missing_concentration(self):
        data = {
            'row_id': [1, 2],
            'solute_concentration': [0.5, 0.2],
            'host_element': ['Cu', 'Cu'],
            'solute_element': ['Zn', 'Zn']
        }
        df = pd.DataFrame(data)
        
        cleaned_df, exclusions = exclude_missing_concentration(df)
        
        assert len(cleaned_df) == 2
        assert len(exclusions) == 0

class TestValidateAtomicRadii:
    def test_validate_atomic_radii_missing_host(self, monkeypatch):
        # Mock get_metallic_radius to return None for 'Unknown'
        def mock_get_radius(elem):
            if elem == 'Unknown':
                return None
            return 1.0 # Simulate valid radius for others

        from code.utils import constants
        monkeypatch.setattr(constants, 'get_metallic_radius', mock_get_radius)

        data = {
            'row_id': [1, 2],
            'host_element': ['Unknown', 'Cu'],
            'solute_element': ['Zn', 'Zn']
        }
        df = pd.DataFrame(data)
        
        cleaned_df, exclusions, missing_data = validate_atomic_radii(df)
        
        assert len(cleaned_df) == 1
        assert len(exclusions) == 1
        assert exclusions[0]['reason_code'] == 'MISSING_ATOMIC_RADIUS_HOST'
        assert missing_data[0]['role'] == 'host'

    def test_validate_atomic_radii_missing_solute(self, monkeypatch):
        def mock_get_radius(elem):
            if elem == 'BadSolute':
                return None
            return 1.0

        from code.utils import constants
        monkeypatch.setattr(constants, 'get_metallic_radius', mock_get_radius)

        data = {
            'row_id': [1],
            'host_element': ['Cu'],
            'solute_element': ['BadSolute']
        }
        df = pd.DataFrame(data)
        
        cleaned_df, exclusions, missing_data = validate_atomic_radii(df)
        
        assert len(cleaned_df) == 0
        assert len(exclusions) == 1
        assert exclusions[0]['reason_code'] == 'MISSING_ATOMIC_RADIUS_SOLUTE'
        assert missing_data[0]['role'] == 'solute'

class TestLogExclusions:
    def test_log_exclusions_creates_files(self, tmp_path):
        # Setup temporary directories
        log_dir = tmp_path / "logs"
        errors_dir = tmp_path / "errors"
        log_dir.mkdir()
        errors_dir.mkdir()
        
        # Monkeypatch global paths for the test
        import code.data.curation as curation_module
        original_log_dir = curation_module.LOG_DIR
        original_project_root = curation_module.PROJECT_ROOT
        
        curation_module.LOG_DIR = log_dir
        curation_module.PROJECT_ROOT = tmp_path

        exclusions = [
            {'row_id': 1, 'reason_code': 'MISSING_CONCENTRATION'},
            {'row_id': 2, 'reason_code': 'MISSING_ATOMIC_RADIUS_HOST', 'element': 'X'}
        ]
        missing_atomic = [
            {'row_id': 2, 'element': 'X', 'role': 'host'}
        ]

        log_exclusions(exclusions, missing_atomic)

        # Check exclusions.log
        exclusions_log = log_dir / "exclusions.log"
        assert exclusions_log.exists()
        
        content = exclusions_log.read_text()
        lines = content.splitlines()
        
        # Check first line is count
        assert lines[0] == "# EXCLUSION_COUNT: 2"
        
        # Check CSV structure
        assert "row_id" in lines[1]
        assert "reason_code" in lines[1]
        
        # Check errors file
        errors_file = errors_dir / "missing_atomic_data.csv"
        assert errors_file.exists()
        err_content = errors_file.read_text()
        assert "row_id" in err_content
        assert "X" in err_content

        # Restore
        curation_module.LOG_DIR = original_log_dir
        curation_module.PROJECT_ROOT = original_project_root
