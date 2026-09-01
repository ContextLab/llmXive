"""
Unit tests for the data curation module (T014).
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.curation import (
    exclude_missing_concentration,
    validate_atomic_radii,
    log_exclusions
)
from code.utils.constants import get_metallic_radius

class TestCuration:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup temporary directories for testing."""
        # Mock the global paths temporarily if needed, 
        # but for unit tests we pass data directly or use mocks.
        self.tmp_path = tmp_path
        yield

    def test_exclude_missing_concentration(self):
        """Test that rows with missing concentration are excluded."""
        data = {
            'solute_symbol': ['Cu', 'Zn', 'Ni'],
            'host_symbol': ['Al', 'Al', 'Al'],
            'concentration': [5.0, None, 10.0],
            'activation_energy': [1.0, 1.1, 1.2]
        }
        df = pd.DataFrame(data)

        df_clean, log = exclude_missing_concentration(df)

        assert len(df_clean) == 2
        assert 'Ni' in df_clean['solute_symbol'].values
        assert 'Cu' in df_clean['solute_symbol'].values
        assert 'Zn' not in df_clean['solute_symbol'].values
        assert len(log) == 1
        assert log[0]['reason_code'] == 'MISSING_CONCENTRATION'

    def test_validate_atomic_radii(self):
        """Test that rows with missing atomic radii are excluded."""
        # We use real symbols for valid radii and a fake one for invalid
        data = {
            'solute_symbol': ['Cu', 'FakeElement123', 'Ni'],
            'host_symbol': ['Al', 'Al', 'Al'],
            'concentration': [5.0, 10.0, 15.0],
            'activation_energy': [1.0, 1.1, 1.2]
        }
        df = pd.DataFrame(data)

        df_clean, log = validate_atomic_radii(df)

        assert len(df_clean) == 2
        assert 'Cu' in df_clean['solute_symbol'].values
        assert 'Ni' in df_clean['solute_symbol'].values
        assert 'FakeElement123' not in df_clean['solute_symbol'].values
        assert len(log) == 1
        assert log[0]['missing_attribute'] == 'solute_radius'

    def test_log_exclusions_creation(self):
        """Test that log files are created correctly."""
        conc_log = [{'row_id': 1, 'reason_code': 'MISSING_CONCENTRATION', 'solute_symbol': 'X'}]
        radii_log = [{'row_id': 2, 'missing_attribute': 'solute_radius', 'solute_symbol': 'Y'}]

        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            error_dir = Path(tmpdir) / "errors"
            log_dir.mkdir()
            error_dir.mkdir()

            # Temporarily override global constants for this test
            import code.data.curation as cur_module
            original_log_dir = cur_module.LOG_DIR
            original_error_dir = cur_module.ERRORS_DIR
            
            cur_module.LOG_DIR = log_dir
            cur_module.ERRORS_DIR = error_dir

            try:
                count = log_exclusions(conc_log, radii_log)
                
                assert count == 2
                assert (log_dir / "exclusions.log").exists()
                assert (error_dir / "missing_atomic_data.csv").exists()

                # Verify exclusion count header
                with open(log_dir / "exclusions.log", 'r') as f:
                    first_line = f.readline().strip()
                    assert "# EXCLUSION_COUNT: 2" in first_line

                # Verify missing data CSV content
                with open(error_dir / "missing_atomic_data.csv", 'r') as f:
                    content = f.read()
                    assert "solute_symbol,missing_attribute" in content
                    assert "Y,solute_radius" in content
            finally:
                cur_module.LOG_DIR = original_log_dir
                cur_module.ERRORS_DIR = original_error_dir

    def test_get_metallic_radius_valid(self):
        """Verify that valid elements return radii."""
        radius = get_metallic_radius("Cu")
        assert radius is not None
        assert radius > 0

    def test_get_metallic_radius_invalid(self):
        """Verify that invalid elements return None."""
        radius = get_metallic_radius("InvalidElementXYZ")
        assert radius is None
