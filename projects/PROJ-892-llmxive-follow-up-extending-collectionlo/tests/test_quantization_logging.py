"""
Unit tests for quantization logging and verification module (T022).

These tests verify the logging and hash verification functionality
without requiring actual model downloads or GPU resources.
"""

import os
import tempfile
import hashlib
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from quantization_logging import (
    verify_artifact_hash,
    log_quantization_step,
    log_quantized_generation,
    register_quantized_artifacts,
    load_config,
    run_quantization_pipeline
)
from state_manager import compute_sha256


class TestVerifyArtifactHash:
    """Tests for the verify_artifact_hash function."""

    def test_verify_existing_file(self):
        """Test verification of an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            is_valid, computed_hash = verify_artifact_hash(temp_path)
            assert is_valid
            assert computed_hash == compute_sha256(temp_path)
        finally:
            temp_path.unlink()

    def test_verify_nonexistent_file(self):
        """Test verification of a non-existent file."""
        is_valid, computed_hash = verify_artifact_hash(Path("/nonexistent/file.txt"))
        assert not is_valid
        assert computed_hash == ""

    def test_verify_hash_match(self):
        """Test hash verification with matching expected hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            expected_hash = compute_sha256(temp_path)
            is_valid, computed_hash = verify_artifact_hash(temp_path, expected_hash)
            assert is_valid
            assert computed_hash == expected_hash
        finally:
            temp_path.unlink()

    def test_verify_hash_mismatch(self):
        """Test hash verification with mismatched expected hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            is_valid, computed_hash = verify_artifact_hash(temp_path, "wrong_hash")
            assert not is_valid
            assert computed_hash == compute_sha256(temp_path)
        finally:
            temp_path.unlink()


class TestLogQuantizationStep:
    """Tests for the log_quantization_step function."""

    def test_log_quantization_step_success(self, caplog):
        """Test successful logging of quantization step."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.safetensors') as f:
            f.write("mock adapter data")
            source_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.safetensors') as f:
            f.write("mock quantized data")
            target_path = Path(f.name)

        try:
            with caplog.at_level("INFO"):
                log_quantization_step(source_path, target_path, "INT8")
            
            assert "Starting INT8 quantization" in caplog.text
            assert f"Source adapter: {source_path}" in caplog.text
            assert f"Target adapter: {target_path}" in caplog.text
            assert "Source adapter SHA-256:" in caplog.text
        finally:
            source_path.unlink()
            target_path.unlink()

    def test_log_quantization_step_missing_source(self):
        """Test logging when source adapter is missing."""
        missing_path = Path("/nonexistent/adapter.safetensors")
        target_path = Path("/tmp/target.safetensors")

        with pytest.raises(FileNotFoundError):
            log_quantization_step(missing_path, target_path, "INT8")


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_valid_config(self):
        """Test loading a valid config file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            f.write("effect_prompts:\n  - prompt1\n  - prompt2\n")
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert "effect_prompts" in config
            assert len(config["effect_prompts"]) == 2
        finally:
            config_path.unlink()

    def test_load_missing_config(self):
        """Test loading a missing config file."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))


class TestIntegration:
    """Integration tests for the quantization logging module."""

    @patch('quantization_logging.generate_images_for_adapters')
    @patch('quantization_logging.compute_sha256')
    @patch('quantization_logging.register_artifact')
    @patch('quantization_logging.save_artifacts_state')
    @patch('quantization_logging.ensure_state_dir')
    def test_log_quantized_generation(
        self,
        mock_ensure_state,
        mock_save_state,
        mock_register,
        mock_compute_hash,
        mock_generate
    ):
        """Test the log_quantized_generation function with mocked dependencies."""
        mock_generate.return_value = None
        mock_compute_hash.return_value = "mock_hash_123"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            adapter_path = Path(tmpdir) / "adapter.safetensors"
            adapter_path.touch()

            # Create a mock image file
            img_path = output_dir / "test_image.png"
            img_path.touch()

            prompt_list = ["prompt1", "prompt2"]

            result = log_quantized_generation(
                adapter_path=adapter_path,
                generated_images_dir=output_dir,
                prompt_list=prompt_list,
                quantization_type="INT8"
            )

            assert len(result) == 1
            assert result[0]["path"] == str(img_path)
            assert result[0]["hash"] == "mock_hash_123"
            assert result[0]["quantization_type"] == "INT8"

            mock_generate.assert_called_once()
            mock_compute_hash.assert_called_once()
            mock_register.assert_called_once()
            mock_save_state.assert_called_once()