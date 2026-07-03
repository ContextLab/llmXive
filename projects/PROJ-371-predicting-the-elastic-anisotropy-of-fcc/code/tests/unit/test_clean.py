"""
Unit tests for src/data/clean.py
"""
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import sys

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.clean import clean_elastic_data
from src.utils.config import get_path

@pytest.fixture
def sample_fcc_data():
    """Create a temporary CSV with sample FCC data."""
    data = {
        "material_id": ["MP-1", "MP-2", "MP-3", "MP-4", "MP-5"],
        "structure": ["FCC", "FCC", "BCC", "FCC", "FCC"],
        "C11": [200.0, 180.0, 200.0, 150.0, 100.0],
        "C12": [100.0, 100.0, 100.0, 100.0, 100.0],
        "C44": [80.0, 60.0, 50.0, 25.0, 0.0],  # MP-5 has C44=0
    }
    df = pd.DataFrame(data)
    return df

def test_clean_fcc_filter(sample_fcc_data):
    """Test that non-FCC entries are removed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        sample_fcc_data.to_csv(input_path, index=False)
        
        df_clean = clean_elastic_data(str(input_path), str(output_path))
        
        # Should remove MP-3 (BCC)
        assert len(df_clean) == 4
        assert "BCC" not in df_clean["structure"].values
        assert "MP-3" not in df_clean["material_id"].values

def test_clean_division_by_zero(sample_fcc_data):
    """Test that entries where C11 == C12 are removed."""
    # Modify data to have C11 == C12 for one entry
    data = sample_fcc_data.copy()
    data.loc[0, "C12"] = 200.0  # Now C11 == C12 for MP-1
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        data.to_csv(input_path, index=False)
        
        df_clean = clean_elastic_data(str(input_path), str(output_path))
        
        # MP-1 should be removed
        assert len(df_clean) == 3
        assert "MP-1" not in df_clean["material_id"].values

def test_clean_a1_calculation(sample_fcc_data):
    """Test that A1 is calculated correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        sample_fcc_data.to_csv(input_path, index=False)
        
        df_clean = clean_elastic_data(str(input_path), str(output_path))
        
        # Check A1 column exists
        assert "A1" in df_clean.columns
        
        # Verify calculation for MP-2: 2*60 / (180-100) = 120/80 = 1.5
        mp2_row = df_clean[df_clean["material_id"] == "MP-2"]
        assert not mp2_row.empty
        assert abs(mp2_row["A1"].values[0] - 1.5) < 1e-6

def test_clean_missing_columns_raises():
    """Test that missing required columns raise an error."""
    data = {
        "material_id": ["MP-1"],
        "C11": [200.0],
        # Missing C12 and C44
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        df.to_csv(input_path, index=False)
        
        with pytest.raises(ValueError, match="Missing required elastic constant columns"):
            clean_elastic_data(str(input_path), str(output_path))

def test_clean_handles_nan_values():
    """Test that rows with NaN in C11, C12, or C44 are dropped."""
    data = {
        "material_id": ["MP-1", "MP-2"],
        "structure": ["FCC", "FCC"],
        "C11": [200.0, None],
        "C12": [100.0, 100.0],
        "C44": [80.0, 60.0],
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        df.to_csv(input_path, index=False)
        
        df_clean = clean_elastic_data(str(input_path), str(output_path))
        
        assert len(df_clean) == 1
        assert "MP-2" not in df_clean["material_id"].values
        assert "MP-1" in df_clean["material_id"].values

def test_clean_output_file_created():
    """Test that the output file is actually created on disk."""
    data = {
        "material_id": ["MP-1"],
        "structure": ["FCC"],
        "C11": [200.0],
        "C12": [100.0],
        "C44": [80.0],
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        df.to_csv(input_path, index=False)
        
        clean_elastic_data(str(input_path), str(output_path))
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0