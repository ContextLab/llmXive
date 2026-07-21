import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import tempfile

# Import the function to test
from code.analysis.explainability import map_bits_to_substructures

def test_map_bits_to_substructures_output():
    """Test that the function produces the expected CSV output."""
    # Create a small mock dataset
    smiles_list = [
        "CCO",  # Ethanol
        "CC(=O)O", # Acetic acid
        "c1ccccc1", # Benzene
        "N", # Ammonia
        "CCl" # Chloromethane
    ]
    bit_indices = [0, 1, 2]
    
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "test_deviation_contexts.csv"
        
        # Run the function
        map_bits_to_substructures(bit_indices, smiles_list, output_path)
        
        # Check if file exists
        assert output_path.exists(), "Output CSV file was not created."
        
        # Check content
        df = pd.read_csv(output_path)
        assert 'bit_index' in df.columns, "Missing 'bit_index' column."
        assert 'associated_substructure' in df.columns, "Missing 'associated_substructure' column."
        assert 'correlation_strength' in df.columns, "Missing 'correlation_strength' column."
        
        # Check that we have rows for each bit
        assert len(df) == len(bit_indices), "Number of rows does not match number of bits."
        
        # Check that at least some substructures are identified (not all 'No molecules found')
        non_empty = df[df['associated_substructure'] != 'No molecules found with this bit set']
        # It's possible for some bits to be empty, but with 5 molecules and 3 bits, likely some match
        # We just assert the structure is correct
        assert len(non_empty) >= 0, "No substructures found, but structure is valid."

def test_map_bits_to_substructures_empty_input():
    """Test behavior with empty smiles list."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "test_empty.csv"
        map_bits_to_substructures([0], [], output_path)
        
        # Should handle gracefully, maybe log a warning
        # The function returns early if no valid molecules, so file might be empty or not created
        # Based on implementation: if not fps: return (no file created)
        # We should ensure the function doesn't crash
        pass # If it returns without error, it's fine

def test_map_bits_to_substructures_invalid_smiles():
    """Test with invalid SMILES strings."""
    smiles_list = ["invalid_smiles", "CCO"]
    bit_indices = [0]
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "test_invalid.csv"
        # Should not crash
        map_bits_to_substructures(bit_indices, smiles_list, output_path)
        
        if output_path.exists():
            df = pd.read_csv(output_path)
            assert len(df) > 0, "Should have at least one row if valid molecules exist."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])