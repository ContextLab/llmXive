import os
import tempfile
import hashlib
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import yaml

# Import the module under test
from quantization_logging import (
    verify_artifact_hash,
    log_quantization_step,
    log_quantized_generation,
    register_quantized_artifacts,
    load_config,
    compute_sha256 # Assuming compute_sha256 is available or we mock it
)
from state_manager import load_artifacts_state, save_artifacts_state

# Mock dependencies if necessary to avoid heavy imports in tests
# For this task, we assume the imports in the module are valid as per the API surface.

class TestQuantizationLogging:
    def test_compute_sha256_valid_file(self, tmp_path):
        """Test that SHA-256 is correctly computed for a file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        computed = compute_sha256(test_file)
        
        assert computed == expected_hash

    def test_verify_artifact_hash_success(self, tmp_path):
        """Test successful hash verification."""
        test_file = tmp_path / "verify.txt"
        content = b"Test content"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Should not raise
        result = verify_artifact_hash(str(test_file), expected_hash)
        assert result == expected_hash

    def test_verify_artifact_hash_mismatch(self, tmp_path):
        """Test that hash mismatch raises ValueError."""
        test_file = tmp_path / "verify_fail.txt"
        test_file.write_bytes(b"Data")
        
        wrong_hash = "0" * 64
        
        with pytest.raises(ValueError, match="Hash mismatch"):
            verify_artifact_hash(str(test_file), wrong_hash)

    def test_verify_artifact_hash_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            verify_artifact_hash(str(tmp_path / "nonexistent.txt"))

    def test_log_quantization_step(self, caplog):
        """Test that logging step works without error."""
        with caplog.at_level("INFO"):
            log_quantization_step("TEST_STEP", {"key": "value"})
        
        assert "QUANTIZATION STEP: TEST_STEP" in caplog.text
        assert "key: value" in caplog.text

    def test_log_quantized_generation(self, caplog):
        """Test logging of generated image."""
        with caplog.at_level("INFO"):
            log_quantized_generation(
                quantization_level="int8",
                prompt="test prompt",
                seed=42,
                output_path="data/test.png",
                image_hash="abc123"
            )
        
        assert "GENERATED [Quantization: int8]" in caplog.text
        assert "test prompt" in caplog.text
        assert "abc123" in caplog.text

    def test_register_quantized_artifacts(self, tmp_path):
        """Test registration of artifacts into state."""
        # Setup temp files
        adapter_path = tmp_path / "adapter_int8.safetensors"
        adapter_path.write_bytes(b"fake adapter data")
        
        img_path = tmp_path / "generated.png"
        img_path.write_bytes(b"fake image data")
        
        state_file = tmp_path / "artifacts.yaml"
        state_file.write_text("artifacts: []\n") # Initialize empty state

        # Mock the load/save to use our temp file
        with patch('quantization_logging.load_artifacts_state') as mock_load, \
             patch('quantization_logging.save_artifacts_state') as mock_save:
            
            mock_state = {"artifacts": []}
            mock_load.return_value = mock_state
            
            # Call the function
            register_quantized_artifacts(
                quantization_level="int8",
                adapter_path=str(adapter_path),
                generated_images=[str(img_path)],
                state_file=str(state_file)
            )
            
            # Verify load and save were called
            mock_load.assert_called_once()
            mock_save.assert_called_once()

    def test_load_config_missing_file(self):
        """Test that load_config raises error if file missing."""
        with pytest.raises(FileNotFoundError):
            load_config() # Assuming config.yaml doesn't exist in temp context or we mock path

# Helper to patch compute_sha256 if it's not directly importable from the same module in test env
# In the actual implementation, compute_sha256 is imported from data_loader.
# We rely on the fact that the module under test imports it correctly.
# For this test, we assume the environment allows importing the function.
# If compute_sha256 is not available in the test scope, we mock it in the module.
# However, since the task requires real implementation, we assume the imports in quantization_logging.py are correct.
# The test above assumes compute_sha256 is available in the namespace of the test or module.
# To be safe, we can import it from data_loader in the test if needed, but the module under test handles it.
# The test verifies the LOGIC of the logging module.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])