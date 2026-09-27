"""
Integration test for T015: Generate and validate rsametrics.csv.

Tests the full pipeline from image processing to CSV generation and validation.
"""
import pytest
import pandas as pd
from pathlib import Path
import os
import sys

# Add parent to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.generate_rsametrics import aggregate_and_validate_metrics, validate_row
from code.config import ensure_directories

class TestRSAMetricsGeneration:
    
    def test_validate_row_positive_values(self):
        """Test that valid rows pass validation."""
        valid_row = {
            'species_id': 'Arabidopsis_thaliana',
            'depth': 10.5,
            'branching_density': 2.3,
            'surface_area': 45.6
        }
        assert validate_row(valid_row) is True

    def test_validate_row_zero_depth_fails(self):
        """Test that zero depth fails validation."""
        invalid_row = {
            'species_id': 'Arabidopsis_thaliana',
            'depth': 0.0,
            'branching_density': 2.3,
            'surface_area': 45.6
        }
        with pytest.raises(ValueError, match="must be > 0"):
            validate_row(invalid_row)

    def test_validate_row_missing_field_fails(self):
        """Test that missing fields fail validation."""
        invalid_row = {
            'species_id': 'Arabidopsis_thaliana',
            'depth': 10.5,
            # missing branching_density
            'surface_area': 45.6
        }
        with pytest.raises(ValueError, match="Missing required field"):
            validate_row(invalid_row)

    def test_aggregate_and_validate_returns_dataframe(self):
        """Test that the main aggregation function returns a DataFrame."""
        # Note: This test assumes T012 and T013 have run and data exists.
        # If data doesn't exist, it will raise FileNotFoundError which is expected behavior.
        try:
            df = aggregate_and_validate_metrics()
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert 'species_id' in df.columns
            assert 'depth' in df.columns
            assert 'branching_density' in df.columns
            assert 'surface_area' in df.columns
            
            # Check data types
            assert df['depth'].dtype in ['float64', 'int64']
            assert df['branching_density'].dtype in ['float64', 'int64']
            assert df['surface_area'].dtype in ['float64', 'int64']
            
            # Check all values are positive
            assert (df['depth'] > 0).all()
            assert (df['branching_density'] > 0).all()
            assert (df['surface_area'] > 0).all()
            
        except FileNotFoundError:
            pytest.skip("Input data not found. Run T012 and T013 first.")

    def test_csv_output_exists_and_valid(self):
        """Test that the output CSV file is created and valid."""
        output_path = Path("data/derived/rsametrics.csv")
        
        # Run the generation
        try:
            from code.generate_rsametrics import main
            main()
        except FileNotFoundError:
            pytest.skip("Input data not found. Run T012 and T013 first.")
        
        assert output_path.exists(), "Output CSV file was not created"
        
        # Load and verify
        df = pd.read_csv(output_path)
        assert len(df) > 0, "Output CSV is empty"
        assert list(df.columns) == ['species_id', 'depth', 'branching_density', 'surface_area']
        assert (df['depth'] > 0).all()
        assert (df['branching_density'] > 0).all()
        assert (df['surface_area'] > 0).all()