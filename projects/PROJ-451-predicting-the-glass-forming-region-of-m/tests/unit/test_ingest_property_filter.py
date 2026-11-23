import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.scripts.ingest import run_property_filtering

class TestPropertyFiltering:
    def test_filter_missing_properties(self):
        """Test that rows with missing properties are dropped."""
        data = {
            'composition': ['Zr50Cu50', 'Zr60Cu20Al20', 'Ti50Ni50'],
            'phase': ['amorphous', 'crystalline', 'amorphous'],
            'atomic_radius': [1.0, 1.2, 1.1],
            'electronegativity': [1.5, 1.6, None], # Missing
            'vec': [2.0, 2.1, 2.2],
            'size_mismatch': [0.1, 0.2, 0.15],
            'mixing_enthalpy': [-10.0, -12.0, -11.0],
            'electronegativity_diff': [0.1, 0.2, 0.3]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            
            df.to_csv(input_path, index=False)
            
            original, dropped = run_property_filtering(input_path, output_path)
            
            assert original == 3
            assert dropped == 1
            
            output_df = pd.read_csv(output_path)
            assert len(output_df) == 2
            # Check that the row with missing electronegativity is gone
            assert output_df['composition'].tolist() == ['Zr50Cu50', 'Zr60Cu20Al20']

    def test_no_missing_properties(self):
        """Test that no rows are dropped if all properties are present."""
        data = {
            'composition': ['Zr50Cu50', 'Zr60Cu20Al20'],
            'phase': ['amorphous', 'crystalline'],
            'atomic_radius': [1.0, 1.2],
            'electronegativity': [1.5, 1.6],
            'vec': [2.0, 2.1],
            'size_mismatch': [0.1, 0.2],
            'mixing_enthalpy': [-10.0, -12.0],
            'electronegativity_diff': [0.1, 0.2]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            
            df.to_csv(input_path, index=False)
            
            original, dropped = run_property_filtering(input_path, output_path)
            
            assert original == 2
            assert dropped == 0
            
            output_df = pd.read_csv(output_path)
            assert len(output_df) == 2

    def test_missing_required_columns(self):
        """Test behavior when required columns are missing from input."""
        data = {
            'composition': ['Zr50Cu50'],
            'phase': ['amorphous'],
            # No property columns
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            
            df.to_csv(input_path, index=False)
            
            # Should not crash, but log warning
            original, dropped = run_property_filtering(input_path, output_path)
            
            assert original == 1
            # If no columns to check, nothing is dropped based on properties
            assert dropped == 0
            
            output_df = pd.read_csv(output_path)
            assert len(output_df) == 1

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        data = {
            'composition': [],
            'phase': [],
            'atomic_radius': [],
            'electronegativity': [],
            'vec': [],
            'size_mismatch': [],
            'mixing_enthalpy': [],
            'electronegativity_diff': []
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.csv")
            output_path = os.path.join(tmpdir, "output.csv")
            
            df.to_csv(input_path, index=False)
            
            original, dropped = run_property_filtering(input_path, output_path)
            
            assert original == 0
            assert dropped == 0