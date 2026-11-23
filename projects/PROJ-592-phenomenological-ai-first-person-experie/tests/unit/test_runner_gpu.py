"""
Unit tests for the GPU Generation Runner (T009b).

These tests verify the logic of the runner without requiring actual GPU hardware.
They mock the llama-cpp-python interactions to ensure correct data flow.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.generation.runner_gpu import (
    GenerationError,
    HardwareError,
    check_cuda_availability,
    load_prompts,
    generate_sample,
    save_batch,
    run_generation_pipeline
)

class TestCheckCudaAvailability:
    def test_cuda_available(self):
        """Test when CUDA is available."""
        with patch('code.generation.runner_gpu.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.device_count.return_value = 1
            logger = MagicMock()
            result = check_cuda_availability(logger)
            assert result is True
            logger.info.assert_called()

    def test_cuda_not_available(self):
        """Test when CUDA is not available."""
        with patch('code.generation.runner_gpu.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            logger = MagicMock()
            result = check_cuda_availability(logger)
            assert result is False
            logger.warning.assert_called()

    def test_torch_not_installed(self):
        """Test when PyTorch is not installed."""
        with patch('code.generation.runner_gpu.torch', side_effect=ImportError):
            logger = MagicMock()
            result = check_cuda_availability(logger)
            # Should return False or handle gracefully
            assert result is False
            logger.warning.assert_called()

class TestLoadPrompts:
    def test_load_prompts_success(self):
        """Test successful loading of prompts."""
        mock_data = [{"id": "1", "prompt": "Test prompt"}]
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):
            with patch('os.path.exists', return_value=True):
                result = load_prompts("dummy_path.json")
                assert len(result) == 1
                assert result[0]["id"] == "1"

    def test_load_prompts_file_not_found(self):
        """Test handling of missing prompt file."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(GenerationError):
                load_prompts("non_existent.json")

    def test_load_prompts_invalid_json(self):
        """Test handling of invalid JSON."""
        with patch('builtins.open', mock_open(read_data="not json")):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(GenerationError):
                    load_prompts("invalid.json")

class TestGenerateSample:
    def test_generate_sample_success(self):
        """Test successful sample generation."""
        mock_model = MagicMock()
        mock_output = {
            'choices': [{'text': 'This is a generated response.'}]
        }
        mock_model.return_value = mock_output

        with patch.object(mock_model, '__call__', return_value=mock_output):
            sample = generate_sample(
                model=mock_model,
                prompt="Test",
                strategy="Direct",
                seed=42
            )
            assert sample["strategy"] == "Direct"
            assert sample["seed"] == 42
            assert "text" in sample

    def test_generate_sample_failure(self):
        """Test handling of generation failure."""
        mock_model = MagicMock()
        mock_model.side_effect = Exception("GPU OOM")

        with pytest.raises(GenerationError):
            generate_sample(
                model=mock_model,
                prompt="Test",
                strategy="Direct",
                seed=42
            )

class TestSaveBatch:
    def test_save_batch_success(self):
        """Test successful batch saving."""
        samples = [{"id": 1, "text": "test"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_batch.json")
            save_batch(samples, output_path, "Direct", "test_model")
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data["count"] == 1
            assert data["strategy"] == "Direct"

class TestRunGenerationPipeline:
    def test_run_pipeline_cuda_fail(self):
        """Test pipeline fails when CUDA is not available."""
        with patch('code.generation.runner_gpu.check_cuda_availability', return_value=False):
            with pytest.raises(HardwareError):
                run_generation_pipeline()

    def test_run_pipeline_model_not_found(self):
        """Test pipeline fails when model file is missing."""
        with patch('code.generation.runner_gpu.check_cuda_availability', return_value=True):
            with patch('code.generation.runner_gpu.load_prompts', return_value=[{"prompt": "test"}]):
                with patch('os.path.exists', return_value=False):
                    with pytest.raises(FileNotFoundError):
                        run_generation_pipeline()

    @patch('code.generation.runner_gpu.check_cuda_availability', return_value=True)
    @patch('code.generation.runner_gpu.load_prompts', return_value=[{"id": "1", "prompt": "Test"}])
    @patch('code.generation.runner_gpu.load_model')
    @patch('code.generation.runner_gpu.generate_sample')
    @patch('code.generation.runner_gpu.save_batch')
    @patch('builtins.open', new_callable=mock_open)
    def test_run_pipeline_success(
        self, mock_open_file, mock_save_batch, mock_gen_sample, mock_load_model, mock_load_prompts, mock_check_cuda
    ):
        """Test successful pipeline execution."""
        mock_gen_sample.return_value = {"seed": 1, "text": "generated", "strategy": "Direct"}
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model

        config = {
            "prompts_path": "test.json",
            "output_dir": "/tmp",
            "model_path": "/tmp/model.gguf"
        }

        with patch('os.path.exists', return_value=True):
            result = run_generation_pipeline(
                config=config,
                prompts_path="test.json",
                output_dir="/tmp",
                samples_per_prompt=2
            )

            assert result["total"] > 0
            assert "strategy_counts" in result
            mock_save_batch.assert_called()
            mock_open_file.assert_called()
