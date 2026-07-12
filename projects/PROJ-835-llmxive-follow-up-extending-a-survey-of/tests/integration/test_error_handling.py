"""
Integration test for error handling of corrupted audio files during embedding extraction.

This test verifies that the pipeline gracefully handles corrupted or unsupported audio files
without crashing, logging appropriate warnings, and continuing processing of valid files.

Related to User Story 1 (US1): CPU-Only Latent Embedding Extraction
"""
import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_module_logger, configure_logging_level
from src.utils.env_config import enforce_cpu_only

# Enforce CPU-only mode as per project constraints
enforce_cpu_only()

# Configure logging for the test
configure_logging_level(logging.INFO)
logger = get_module_logger(__name__)


class TestErrorHandling:
    """Integration tests for error handling in audio processing pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test fixtures."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp(prefix="llmxive_test_")
        self.corrupted_file = Path(self.test_dir) / "corrupted_audio.wav"
        self.valid_file = Path(self.test_dir) / "valid_audio.wav"
        
        # Create a corrupted audio file (invalid header)
        with open(self.corrupted_file, "wb") as f:
            f.write(b"RIFF" + b"\x00" * 100)  # Invalid RIFF header
        
        # Create a minimal valid WAV file (44 bytes header + 100 bytes data)
        # This is a minimal valid WAV file structure
        wav_header = (
            b"RIFF" + 
            (100 + 36).to_bytes(4, 'little') + 
            b"WAVE" + 
            b"fmt " + 
            (16).to_bytes(4, 'little') +  # Chunk size
            (1).to_bytes(2, 'little') +    # Audio format (PCM)
            (1).to_bytes(2, 'little') +    # Number of channels
            (44100).to_bytes(4, 'little') + # Sample rate
            (44100).to_bytes(4, 'little') + # Byte rate
            (2).to_bytes(2, 'little') +    # Block align
            (16).to_bytes(2, 'little') +   # Bits per sample
            b"data" + 
            (100).to_bytes(4, 'little')    # Data chunk size
        )
        with open(self.valid_file, "wb") as f:
            f.write(wav_header)
            f.write(b"\x00" * 100)  # Dummy audio data

        yield

        # Clean up temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_corrupted_file_handling(self):
        """Test that corrupted audio files are handled gracefully without crashing."""
        from src.data.preprocess import load_audio, validate_audio_file
        
        # Test that corrupted file raises appropriate exception
        with pytest.raises(Exception):
            load_audio(str(self.corrupted_file))
        
        # Test that validate_audio_file returns False for corrupted file
        is_valid, error_msg = validate_audio_file(str(self.corrupted_file))
        assert is_valid is False
        assert "corrupted" in error_msg.lower() or "invalid" in error_msg.lower()

    def test_valid_file_processing(self):
        """Test that valid audio files are processed correctly."""
        from src.data.preprocess import load_audio, validate_audio_file
        
        # Test that valid file passes validation
        is_valid, error_msg = validate_audio_file(str(self.valid_file))
        assert is_valid is True
        assert error_msg is None or error_msg == ""
        
        # Test that valid file can be loaded
        audio_data, sample_rate = load_audio(str(self.valid_file))
        assert audio_data is not None
        assert sample_rate == 44100
        assert len(audio_data) > 0

    def test_missing_file_handling(self):
        """Test that missing audio files are handled gracefully."""
        from src.data.preprocess import load_audio, validate_audio_file
        
        missing_file = Path(self.test_dir) / "nonexistent.wav"
        
        # Test that missing file raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            load_audio(str(missing_file))
        
        # Test that validate_audio_file returns False for missing file
        is_valid, error_msg = validate_audio_file(str(missing_file))
        assert is_valid is False
        assert "not found" in error_msg.lower() or "missing" in error_msg.lower()

    def test_batch_processing_with_mixed_files(self):
        """Test batch processing with a mix of valid and corrupted files."""
        from src.data.preprocess import process_audio_batch
        
        # Create a list of files: valid, corrupted, valid
        file_list = [
            str(self.valid_file),
            str(self.corrupted_file),
            str(self.valid_file)
        ]
        
        # Process batch - should handle corrupted files gracefully
        results = process_audio_batch(file_list)
        
        # Should have results for all files
        assert len(results) == 3
        
        # Valid files should succeed
        assert results[0]["success"] is True
        assert results[2]["success"] is True
        
        # Corrupted file should fail gracefully
        assert results[1]["success"] is False
        assert "error" in results[1] or "message" in results[1]

    def test_logging_of_corrupted_files(self):
        """Test that corrupted files are logged appropriately."""
        from src.data.preprocess import validate_audio_file
        
        # Capture log output
        with patch('src.data.preprocess.logger') as mock_logger:
            validate_audio_file(str(self.corrupted_file))
            
            # Verify that error/warning was logged
            assert mock_logger.warning.called or mock_logger.error.called

    def test_graceful_continuation_after_error(self):
        """Test that processing continues after encountering a corrupted file."""
        from src.data.preprocess import process_audio_batch
        
        # Create files: valid, corrupted, valid, valid
        file_list = [
            str(self.valid_file),
            str(self.corrupted_file),
            str(self.valid_file),
            str(self.valid_file)
        ]
        
        # Process all files
        results = process_audio_batch(file_list)
        
        # Should have processed all files
        assert len(results) == 4
        
        # Count successful vs failed
        successful = sum(1 for r in results if r["success"])
        failed = sum(1 for r in results if not r["success"])
        
        # Should have 3 successful and 1 failed
        assert successful == 3
        assert failed == 1

    def test_invalid_format_handling(self):
        """Test handling of unsupported audio formats."""
        from src.data.preprocess import validate_audio_file
        
        # Create a file with unsupported extension
        unsupported_file = Path(self.test_dir) / "audio.txt"
        with open(unsupported_file, "w") as f:
            f.write("This is not audio data")
        
        # Should fail validation
        is_valid, error_msg = validate_audio_file(str(unsupported_file))
        assert is_valid is False
        assert "format" in error_msg.lower() or "unsupported" in error_msg.lower()

    def test_empty_file_handling(self):
        """Test handling of empty audio files."""
        empty_file = Path(self.test_dir) / "empty.wav"
        empty_file.touch()
        
        from src.data.preprocess import validate_audio_file, load_audio
        
        # Should fail validation
        is_valid, error_msg = validate_audio_file(str(empty_file))
        assert is_valid is False
        
        # Should raise exception when loading
        with pytest.raises(Exception):
            load_audio(str(empty_file))

    def test_integration_with_pipeline_error_handling(self):
        """Test that the error handling integrates properly with the main pipeline."""
        from src.data.preprocess import process_audio_batch
        
        # Create a realistic mix of files
        file_list = [
            str(self.valid_file),
            str(self.corrupted_file),
            str(self.valid_file),
            str(self.valid_file)
        ]
        
        # Process with error handling
        results = process_audio_batch(file_list)
        
        # Verify all files were processed
        assert len(results) == len(file_list)
        
        # Verify success/failure counts
        success_count = sum(1 for r in results if r["success"])
        failure_count = sum(1 for r in results if not r["success"])
        
        assert success_count == 3
        assert failure_count == 1
        
        # Verify that failed files have error information
        for result in results:
            if not result["success"]:
                assert "error" in result or "message" in result
                assert result["file"] == str(self.corrupted_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])