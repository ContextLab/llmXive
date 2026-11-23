"""
tests/unit/test_descriptors_io.py

Unit tests for T026: verifying that descriptors are saved to CSV with required columns.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import tempfile
import shutil

# Import functions from code/descriptors.py
# Note: Assuming code/ is in the PYTHONPATH or we adjust sys.path
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from descriptors import (
    parse_composition,
    calculate_radius_mismatch,
    calculate_electronegativity_difference,
    calculate_vec,
    calculate_weighted_mean_radius,
    process_dataframe,
    save_descriptors,
    save_diagnostic_log
)


class TestDescriptorCalculations:
    """Test individual descriptor calculation functions."""

    def test_parse_composition_simple(self):
        """Test parsing a simple binary composition."""
        comp = parse_composition("Fe50Zr50")
        assert abs(comp['Fe'] - 0.5) < 1e-6
        assert abs(comp['Zr'] - 0.5) < 1e-6

    def test_parse_composition_decimal(self):
        """Test parsing a composition with decimals."""
        comp = parse_composition("Fe50.5Zr49.5")
        assert abs(comp['Fe'] - 0.505) < 1e-6
        assert abs(comp['Zr'] - 0.495) < 1e-6

    def test_parse_composition_invalid(self):
        """Test that invalid composition raises error."""
        with pytest.raises(ValueError):
            parse_composition("InvalidString")

    def test_calculate_vec(self):
        """Test VEC calculation for a known composition."""
        # Fe: ~8 valence electrons (approx), Zr: ~4
        comp = parse_composition("Fe50Zr50")
        vec = calculate_vec(comp)
        # Expected: 0.5 * 8 + 0.5 * 4 = 6.0
        # Mendeleev values might differ slightly, but should be reasonable
        assert vec > 0

    def test_calculate_electronegativity_diff(self):
        """Test electronegativity difference calculation."""
        comp = parse_composition("Fe50Zr50")
        chi_diff = calculate_electronegativity_difference(comp)
        assert chi_diff >= 0


class TestDescriptorIO:
    """Test saving descriptors to CSV (T026 verification)."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir)

    def test_save_descriptors_creates_file(self, temp_dir):
        """Test that save_descriptors creates the output file."""
        # Create a dummy dataframe
        df = pd.DataFrame({
            'composition': ['Fe50Zr50', 'Cu50Zr50'],
            'radius_mismatch': [0.05, 0.06],
            'electronegativity_diff': [0.1, 0.2],
            'VEC': [6.0, 5.5]
        })

        output_path = temp_dir / "test_descriptors.csv"
        save_descriptors(df, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_save_descriptors_has_required_columns(self, temp_dir):
        """Test that the saved CSV contains required columns."""
        df = pd.DataFrame({
            'composition': ['Fe50Zr50'],
            'radius_mismatch': [0.05],
            'electronegativity_diff': [0.1],
            'VEC': [6.0]
        })

        output_path = temp_dir / "test_descriptors.csv"
        save_descriptors(df, output_path)

        saved_df = pd.read_csv(output_path)
        required_cols = ['radius_mismatch', 'electronegativity_diff', 'VEC']

        for col in required_cols:
            assert col in saved_df.columns, f"Missing column: {col}"

    def test_save_descriptors_drops_nan_rows(self, temp_dir):
        """Test that rows with NaN descriptors are dropped."""
        df = pd.DataFrame({
            'composition': ['Fe50Zr50', 'Invalid'],
            'radius_mismatch': [0.05, np.nan],
            'electronegativity_diff': [0.1, np.nan],
            'VEC': [6.0, np.nan]
        })

        output_path = temp_dir / "test_descriptors.csv"
        save_descriptors(df, output_path)

        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 1
        assert saved_df.iloc[0]['radius_mismatch'] == 0.05

    def test_save_diagnostic_log(self, temp_dir):
        """Test that diagnostic log is saved correctly."""
        df = pd.DataFrame({
            'composition': ['Fe50Zr50'],
            'weighted_mean_radius': [150.0]
        })

        output_path = temp_dir / "test_diag.json"
        save_diagnostic_log(df, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert 'weighted_mean_radius' in data
        assert data['weighted_mean_radius'] == 150.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])