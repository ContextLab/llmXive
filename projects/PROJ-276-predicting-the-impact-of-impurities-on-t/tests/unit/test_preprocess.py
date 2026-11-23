"""
Unit tests for the preprocess module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.ingestion.preprocess import (
    weight_pct_to_atomic_pct,
    handle_synthesis_range,
    clean_column_name,
    merge_datasets,
    convert_impurity_units,
    filter_valid_entries,
    attach_provenance
)
from code.src.utils.constants import get_atomic_weight

class TestWeightToAtomicConversion:
    """Tests for weight% to atomic% conversion."""

    def test_magnesium_conversion(self):
        """Test conversion for magnesium impurity."""
        # 10 wt% Mg in MgB2 matrix
        atomic_pct = weight_pct_to_atomic_pct(10.0, "Mg")
        assert 0.0 < atomic_pct < 100.0
        # Should be less than weight% due to atomic weight differences

    def test_carbon_conversion(self):
        """Test conversion for carbon impurity."""
        atomic_pct = weight_pct_to_atomic_pct(5.0, "C")
        assert 0.0 < atomic_pct < 100.0

    def test_zero_weight(self):
        """Test conversion with zero weight percentage."""
        atomic_pct = weight_pct_to_atomic_pct(0.0, "C")
        assert atomic_pct == 0.0

    def test_nan_weight(self):
        """Test conversion with NaN weight percentage."""
        atomic_pct = weight_pct_to_atomic_pct(np.nan, "C")
        assert atomic_pct == 0.0

    def test_unknown_element(self):
        """Test conversion with unknown element."""
        # This should log a warning and return 0.0
        atomic_pct = weight_pct_to_atomic_pct(10.0, "XZZ")
        assert atomic_pct == 0.0

class TestSynthesisRangeHandling:
    """Tests for synthesis range handling."""

    def test_range_with_dash(self):
        """Test parsing range with dash."""
        result = handle_synthesis_range("500-600")
        assert result == 550.0

    def test_range_with_to(self):
        """Test parsing range with 'to'."""
        result = handle_synthesis_range("500 to 600")
        assert result == 550.0

    def test_numeric_value(self):
        """Test parsing numeric value."""
        result = handle_synthesis_range(550.0)
        assert result == 550.0

    def test_string_numeric(self):
        """Test parsing string numeric."""
        result = handle_synthesis_range("550")
        assert result == 550.0

    def test_nan_value(self):
        """Test parsing NaN value."""
        result = handle_synthesis_range(np.nan)
        assert result == 0.0

    def test_invalid_range(self):
        """Test parsing invalid range."""
        result = handle_synthesis_range("invalid")
        assert result == 0.0

class TestColumnCleaning:
    """Tests for column name cleaning."""

    def test_basic_cleaning(self):
        """Test basic column name cleaning."""
        assert clean_column_name("Test Column") == "test_column"
        assert clean_column_name("test-column") == "test_column"
        assert clean_column_name("  Test  ") == "test"

class TestMergeDatasets:
    """Tests for dataset merging."""

    def test_merge_basic(self):
        """Test basic dataset merge."""
        mp_df = pd.DataFrame({
            'tc': [39.0, 40.0],
            'source': ['mp1', 'mp2']
        })
        supercon_df = pd.DataFrame({
            'tc': [38.0, 41.0],
            'source': ['sc1', 'sc2']
        })

        result = merge_datasets(mp_df, supercon_df)

        assert len(result) == 4
        assert 'source' in result.columns
        assert result['source'].tolist() == ['mp1', 'mp2', 'sc1', 'sc2']

    def test_merge_with_common_columns(self):
        """Test merge with common columns."""
        mp_df = pd.DataFrame({
            'tc': [39.0],
            'pressure': [0.1],
            'source': ['mp1']
        })
        supercon_df = pd.DataFrame({
            'tc': [38.0],
            'pressure': [0.2],
            'source': ['sc1']
        })

        result = merge_datasets(mp_df, supercon_df)

        assert len(result) == 2
        assert 'pressure' in result.columns

class TestConvertImpurityUnits:
    """Tests for impurity unit conversion."""

    def test_convert_single_impurity(self):
        """Test conversion of single impurity column."""
        df = pd.DataFrame({
            'tc': [39.0, 40.0],
            'impurity_c_weight_pct': [1.0, 2.0]
        })

        result = convert_impurity_units(df)

        assert 'impurity_c_weight_pct_atomic_pct' in result.columns
        assert len(result) == 2

    def test_no_impurity_columns(self):
        """Test with no impurity columns."""
        df = pd.DataFrame({
            'tc': [39.0]
        })

        result = convert_impurity_units(df)

        # Should return unchanged dataframe
        assert len(result.columns) == 1

class TestFilterValidEntries:
    """Tests for filtering valid entries."""

    def test_filter_null_tc(self):
        """Test filtering rows with null Tc."""
        df = pd.DataFrame({
            'tc': [39.0, np.nan, 40.0],
            'impurity_c_atomic_pct': [1.0, 2.0, 3.0]
        })

        result = filter_valid_entries(df)

        assert len(result) == 2
        assert not result['tc'].isna().any()

    def test_filter_null_impurities(self):
        """Test filtering rows with null impurities."""
        df = pd.DataFrame({
            'tc': [39.0, 40.0, 41.0],
            'impurity_c_atomic_pct': [1.0, np.nan, 3.0]
        })

        result = filter_valid_entries(df)

        # Should keep rows with at least one non-null impurity
        assert len(result) >= 2

    def test_filter_low_tc(self):
        """Test filtering rows with Tc below minimum."""
        df = pd.DataFrame({
            'tc': [0.0, 39.0, 40.0],
            'impurity_c_atomic_pct': [1.0, 2.0, 3.0]
        })

        result = filter_valid_entries(df)

        # Should filter out Tc = 0.0
        assert len(result) == 2

class TestAttachProvenance:
    """Tests for provenance attachment."""

    def test_attach_provenance_structure(self):
        """Test that provenance is attached correctly."""
        df = pd.DataFrame({
            'tc': [39.0],
            'impurity_c_atomic_pct': [1.0]
        })

        result = attach_provenance(df, ['source1.csv', 'source2.csv'], '1.0.0')

        assert '_provenance' in result.columns
        assert len(result) == 1

        # Verify provenance is valid JSON
        provenance_str = result['_provenance'].iloc[0]
        provenance = json.loads(provenance_str)

        assert 'source' in provenance
        assert 'timestamp' in provenance
        assert 'version' in provenance
        assert provenance['version'] == '1.0.0'

    def test_provenance_source_includes_files(self):
        """Test that provenance includes source files."""
        df = pd.DataFrame({'tc': [39.0]})
        result = attach_provenance(df, ['file1.csv'], '1.0.0')

        provenance = json.loads(result['_provenance'].iloc[0])
        assert 'file1.csv' in provenance['source']

class TestPreprocessIntegration:
    """Integration tests for the full preprocessing pipeline."""

    def test_full_pipeline_with_mock_data(self, tmp_path):
        """Test full pipeline with mock data files."""
        from code.src.ingestion.preprocess import preprocess_datasets

        # Create mock data files
        mp_data = tmp_path / "materials_project_mgb2.csv"
        supercon_data = tmp_path / "supercon_mgb2.csv"
        output_data = tmp_path / "mgb2_clean.csv"

        # Create mock Materials Project data
        mp_df = pd.DataFrame({
            'tc': [39.0, 40.0, np.nan, 38.5],
            'impurity_c_weight_pct': [1.0, 2.0, 3.0, 4.0],
            'pressure_gpa': [0.0, 0.1, 0.2, 0.3]
        })
        mp_df.to_csv(mp_data, index=False)

        # Create mock SuperCon data
        supercon_df = pd.DataFrame({
            'tc': [38.0, 41.0, 39.5],
            'impurity_n_weight_pct': [0.5, 1.5, 2.5],
            'pressure_gpa': [0.0, 0.1, 0.2]
        })
        supercon_df.to_csv(supercon_data, index=False)

        # Run preprocessing
        result = preprocess_datasets(
            cached_mp_path=str(mp_data),
            cached_supercon_path=str(supercon_data),
            output_path=str(output_data)
        )

        # Verify output
        assert output_data.exists()
        assert len(result) > 0
        assert 'tc' in result.columns
        assert '_provenance' in result.columns

        # Verify no null Tc values
        assert not result['tc'].isna().any()

        # Verify output file can be read back
        loaded_df = pd.read_csv(output_data)
        assert len(loaded_df) == len(result)