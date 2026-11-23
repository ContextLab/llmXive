"""
Unit tests for preprocessing functions in preprocess.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.ingestion.preprocess import (
    clean_column_name,
    weight_pct_to_atomic_pct,
    handle_synthesis_range,
    convert_impurity_units,
    merge_datasets,
    filter_valid_entries,
    attach_provenance,
    preprocess_datasets
)
from code.src.utils.constants import get_atomic_weight


class TestWeightToAtomicConversion:
    """Tests for weight percentage to atomic percentage conversion."""
    
    def test_basic_conversion(self):
        """Test basic weight to atomic conversion."""
        # For MgB2: Mg=52.9%, B=47.1% by weight
        # 1% weight impurity should convert to approximately 2% atomic
        result = weight_pct_to_atomic_pct(1.0, "C", [("Mg", 52.9), ("B", 47.1)])
        assert result > 0
        assert result < 100
    
    def test_zero_weight(self):
        """Test conversion with zero weight percentage."""
        result = weight_pct_to_atomic_pct(0.0, "C", [("Mg", 52.9), ("B", 47.1)])
        assert result == 0.0
    
    def test_nan_weight(self):
        """Test conversion with NaN weight percentage."""
        result = weight_pct_to_atomic_pct(np.nan, "C", [("Mg", 52.9), ("B", 47.1)])
        assert result == 0.0
    
    def test_high_impurity(self):
        """Test conversion with high impurity percentage."""
        result = weight_pct_to_atomic_pct(10.0, "C", [("Mg", 52.9), ("B", 47.1)])
        assert result > 0
        assert result < 100
    
    def test_unknown_element(self):
        """Test conversion with unknown element."""
        result = weight_pct_to_atomic_pct(1.0, "X", [("Mg", 52.9), ("B", 47.1)])
        assert result == 0.0


class TestSynthesisRange:
    """Tests for synthesis range handling."""
    
    def test_range_string(self):
        """Test parsing of range string."""
        result = handle_synthesis_range("300-400")
        assert result == 350.0
    
    def test_single_value(self):
        """Test parsing of single value."""
        result = handle_synthesis_range("350")
        assert result == 350.0
    
    def test_float_value(self):
        """Test parsing of float value."""
        result = handle_synthesis_range("350.5")
        assert result == 350.5
    
    def test_nan_value(self):
        """Test handling of NaN."""
        result = handle_synthesis_range(np.nan)
        assert result is None
    
    def test_invalid_string(self):
        """Test handling of invalid string."""
        result = handle_synthesis_range("invalid")
        assert result is None
    
    def test_range_with_spaces(self):
        """Test parsing of range with spaces."""
        result = handle_synthesis_range(" 300 - 400 ")
        assert result == 350.0
    
    def test_negative_range(self):
        """Test parsing of negative range."""
        result = handle_synthesis_range("-10-10")
        assert result == 0.0


class TestCleanColumnName:
    """Tests for column name cleaning."""
    
    def test_basic_cleaning(self):
        """Test basic column name cleaning."""
        result = clean_column_name("Critical Temperature")
        assert result == "critical_temperature"
    
    def test_special_characters(self):
        """Test removal of special characters."""
        result = clean_column_name("Tc (K)!@#$")
        assert result == "tc_k"
    
    def test_hyphens(self):
        """Test conversion of hyphens to underscores."""
        result = clean_column_name("impurity-weight")
        assert result == "impurity_weight"
    
    def test_multiple_spaces(self):
        """Test handling of multiple spaces."""
        result = clean_column_name("  multiple   spaces  ")
        assert result == "multiple_spaces"
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = clean_column_name("")
        assert result == ""

def test_convert_impurity_units():
    """Test conversion of impurity units."""
    df = pd.DataFrame({
        "impurity_C_weight": [1.0, 2.0, 3.0],
        "impurity_O_weight": [0.5, 1.0, 1.5],
        "Tc": [39.0, 38.5, 38.0]
    })
    
    result = convert_impurity_units(df, ["impurity_C_weight", "impurity_O_weight"])
    
    assert "impurity_C_atomic" in result.columns
    assert "impurity_O_atomic" in result.columns
    assert "impurity_C_weight" not in result.columns
    assert "impurity_O_weight" not in result.columns
    assert all(result["impurity_C_atomic"] > 0)

def test_merge_datasets():
    """Test merging of datasets."""
    mp_df = pd.DataFrame({
        "tc": [39.0, 38.5],
        "impurity_c": [1.0, 2.0],
        "source": ["mp1", "mp2"]
    })
    
    supercon_df = pd.DataFrame({
        "critical_temperature": [38.0, 37.5],
        "carbon_impurity": [0.5, 1.5],
        "source": ["sc1", "sc2"]
    })
    
    result = merge_datasets(mp_df, supercon_df)
    
    assert len(result) == 4
    assert "Tc" in result.columns
    assert "impurity_C" in result.columns
    assert "source" in result.columns
    assert all(result["source"].isin(["materials_project", "supercon"]))

def test_filter_valid_entries():
    """Test filtering of valid entries."""
    df = pd.DataFrame({
        "Tc": [39.0, np.nan, 38.0, 37.5],
        "impurity_C": [1.0, 2.0, np.nan, 0.5],
        "impurity_O": [0.5, np.nan, 1.0, 1.5]
    })
    
    result = filter_valid_entries(df)
    
    # Should drop row 1 (NaN Tc) and row 2 (all impurities NaN)
    assert len(result) == 2
    assert all(result["Tc"].notna())

def test_attach_provenance():
    """Test attaching provenance metadata."""
    df = pd.DataFrame({
        "Tc": [39.0, 38.5],
        "impurity_C": [1.0, 2.0]
    })
    
    raw_headers = ["header1", "header2"]
    result = attach_provenance(df, raw_headers)
    
    assert "provenance" in result.attrs
    assert "provenance_header" in result.attrs
    assert len(result.attrs["provenance"]["sources"]) == 2

def test_preprocess_datasets_integration():
    """Integration test for preprocess_datasets with mock files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock raw files
        mp_data = [
            {"material_id": "mp-1", "tc": 39.0, "impurity_c": 1.0, "impurity_o": 0.5},
            {"material_id": "mp-2", "tc": 38.5, "impurity_c": 2.0, "impurity_o": 1.0}
        ]
        
        mp_file = tmpdir / "materials_project_mgb2.json"
        with open(mp_file, 'w') as f:
            json.dump(mp_data, f)
        
        supercon_file = tmpdir / "supercon_mgb2.csv"
        supercon_df = pd.DataFrame({
            "tc": [38.0, 37.5],
            "impurity_c": [0.5, 1.5],
            "impurity_o": [0.2, 0.8]
        })
        supercon_df.to_csv(supercon_file, index=False)
        
        # Temporarily override paths
        import code.src.ingestion.preprocess as preprocess_module
        original_mp_file = preprocess_module.MATERIALS_PROJECT_FILE
        original_supercon_file = preprocess_module.SUPERCON_FILE
        
        preprocess_module.MATERIALS_PROJECT_FILE = mp_file
        preprocess_module.SUPERCON_FILE = supercon_file
        
        try:
            result = preprocess_datasets()
            assert len(result) > 0
            assert "Tc" in result.columns
            assert "source" in result.columns
        finally:
            preprocess_module.MATERIALS_PROJECT_FILE = original_mp_file
            preprocess_module.SUPERCON_FILE = original_supercon_file
