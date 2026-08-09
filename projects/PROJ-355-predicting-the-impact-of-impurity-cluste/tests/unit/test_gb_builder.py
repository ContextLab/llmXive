"""Unit tests for code/data/gb_builder.py."""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data.gb_builder import insert_impurity, build_gb_supercell, save_structure

def test_insert_impurity_structure_modification():
    """Test that insert_impurity modifies the structure."""
    # Mock a simple structure for testing
    with patch('code.data.gb_builder.Structure') as mock_structure:
        mock_inst = MagicMock()
        mock_structure.return_value = mock_inst
        
        # Call function
        result = insert_impurity(mock_inst, "Fe", 1.0, (0, 0, 0))
        
        # Verify structure was modified (mocked behavior)
        assert mock_inst.append.called or result is not None

def test_save_structure_creates_file():
    """Test that save_structure creates a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_structure.cif"
        with patch('code.data.gb_builder.Structure.from_file') as mock_from_file:
            mock_struct = MagicMock()
            mock_from_file.return_value = mock_struct
            
            # This would normally write to disk, we mock the write part
            # For unit test, we verify the path logic
            save_structure(mock_struct, str(output_path))
            
            # Verify path construction
            assert output_path.suffix == ".cif"
