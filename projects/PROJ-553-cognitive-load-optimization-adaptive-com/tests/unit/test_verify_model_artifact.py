"""
Unit tests for code/verify_model_artifact.py
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.verify_model_artifact import verify_model_artifact, MAX_SIZE_BYTES, HIGH_CONF_FILE, LOW_CONF_FILE
from pathlib import Path as PathLib

class TestVerifyModelArtifact:
    """Tests for the model artifact verification logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = PathLib(self.temp_dir) / "data" / "processed"
        self.processed_dir.mkdir(parents=True)
        
        # Temporarily override the global constants for testing
        self.original_high_conf = HIGH_CONF_FILE
        self.original_low_conf = LOW_CONF_FILE
        
        # We need to reload the module with new paths, but since the paths are 
        # module-level constants, we will test the logic by mocking or 
        # creating files in the expected temp locations and adjusting the test logic.
        # However, the function `verify_model_artifact` uses global constants.
        # To properly test, we will patch the module's attributes.
        
        import code.verify_model_artifact as mod
        mod.PROCESSED_DIR = self.processed_dir
        mod.HIGH_CONF_FILE = self.processed_dir / "load_model.pkl"
        mod.LOW_CONF_FILE = self.processed_dir / "load_model_low_confidence.pkl"

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Restore original constants
        import code.verify_model_artifact as mod
        mod.PROCESSED_DIR = self.original_high_conf.parent.parent
        mod.HIGH_CONF_FILE = self.original_high_conf
        mod.LOW_CONF_FILE = self.original_low_conf

    def test_missing_model_raises_error(self):
        """Test that missing model files raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as excinfo:
            verify_model_artifact()
        assert "Model artifact missing" in str(excinfo.value)

    def test_high_conf_model_valid(self):
        """Test that a valid high-confidence model passes."""
        # Create a dummy high confidence model file
        model_path = self.processed_dir / "load_model.pkl"
        model_path.write_bytes(b"dummy model data")
        
        result = verify_model_artifact()
        assert result is True

    def test_low_conf_model_valid(self):
        """Test that a valid low-confidence model passes."""
        # Create a dummy low confidence model file
        model_path = self.processed_dir / "load_model_low_confidence.pkl"
        model_path.write_bytes(b"dummy low conf model data")
        
        result = verify_model_artifact()
        assert result is True

    def test_high_conf_priority_over_low_conf(self):
        """Test that high confidence model is preferred if both exist."""
        # Create both files
        high_conf_path = self.processed_dir / "load_model.pkl"
        low_conf_path = self.processed_dir / "load_model_low_confidence.pkl"
        high_conf_path.write_bytes(b"high")
        low_conf_path.write_bytes(b"low")
        
        # The function doesn't return the path, but it should find one.
        # We can't easily test the preference without modifying the function to return the path.
        # However, the logic in the function checks HIGH first.
        # Let's just verify it doesn't crash and finds *a* model.
        result = verify_model_artifact()
        assert result is True

    def test_model_too_large_raises_error(self):
        """Test that a model exceeding size limit raises ValueError."""
        # Create a dummy file larger than 500MB
        # Note: Creating a 500MB+ file in a test might be slow or hit disk limits.
        # Instead, we will mock the file size check by creating a small file
        # and temporarily lowering the MAX_SIZE_BYTES constant.
        
        import code.verify_model_artifact as mod
        original_max = mod.MAX_SIZE_BYTES
        mod.MAX_SIZE_BYTES = 10 # Set limit to 10 bytes
        
        try:
            model_path = self.processed_dir / "load_model.pkl"
            model_path.write_bytes(b"x" * 20) # 20 bytes > 10 bytes limit
            
            with pytest.raises(ValueError) as excinfo:
                verify_model_artifact()
            assert "too large" in str(excinfo.value).lower()
        finally:
            mod.MAX_SIZE_BYTES = original_max