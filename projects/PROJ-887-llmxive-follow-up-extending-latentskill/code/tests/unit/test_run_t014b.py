import os
import sys
import tempfile
import pytest
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.run_t014b import verify_file_integrity

class TestRunT014b:
    
    def test_verify_file_integrity_missing_file(self):
        """Test that verify_file_integrity returns False for missing file."""
        result = verify_file_integrity(Path("/nonexistent/path/file.npz"))
        assert result is False

    def test_verify_file_integrity_empty_file(self):
        """Test that verify_file_integrity returns False for empty file."""
        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            # Create empty file
            tmp_path.touch()
            result = verify_file_integrity(tmp_path)
            assert result is False
        finally:
            tmp_path.unlink()

    def test_verify_file_integrity_invalid_format(self):
        """Test that verify_file_integrity returns False for non-npz file."""
        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False, mode='w') as tmp:
            tmp.write("not a numpy file")
            tmp_path = Path(tmp.name)
        try:
            result = verify_file_integrity(tmp_path)
            assert result is False
        finally:
            tmp_path.unlink()

    def test_verify_file_integrity_valid(self):
        """Test that verify_file_integrity returns True for valid npz with required keys."""
        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            # Create a valid npz with required keys
            data = {
                'vectors': np.random.rand(10, 100).astype(np.float32),
                'metadata': np.array(['test_metadata'], dtype=object)
            }
            np.savez(tmp_path, **data)
            
            result = verify_file_integrity(tmp_path)
            assert result is True
        finally:
            tmp_path.unlink()

    def test_verify_file_integrity_missing_keys(self):
        """Test that verify_file_integrity returns False if required keys are missing."""
        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            # Create npz with missing 'vectors' key
            data = {
                'other_key': np.array([1, 2, 3])
            }
            np.savez(tmp_path, **data)
            
            result = verify_file_integrity(tmp_path)
            assert result is False
        finally:
            tmp_path.unlink()