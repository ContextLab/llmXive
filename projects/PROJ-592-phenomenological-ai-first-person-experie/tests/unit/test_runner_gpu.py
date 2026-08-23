"""
Unit tests for GPU-Offload Generation Runner (T009b).

These tests verify the logic of the GPU runner without requiring actual GPU hardware.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from code.generation.runner_gpu import (
    GenerationError,
    HardwareError,
    setup_logger,
    check_cuda_availability,
    load_model,
    generate_sample,
    load_prompts,
    save_batch,
    run_generation_pipeline
)


class TestCudaAvailability:
    """Tests for CUDA availability checking."""

    @patch('code.generation.runner_gpu.torch')
    def test_cuda_available(self, mock_torch):
        """Test when CUDA is available."""
        mock_torch.cuda.is_available.return_value = True
        mock_tensor = MagicMock()
        mock_torch.zeros.return_value = mock_tensor
        mock_tensor.cuda.return_value = mock_tensor
        mock_torch.cuda.get_device_name.return_value = "NVIDIA A100"

        assert check_cuda_availability() is True

    @patch('code.generation.runner_gpu.torch')
    def test_cuda_not_available(self, mock_torch):
        """Test when CUDA is not available."""
        mock_torch.cuda.is_available.return_value = False
        assert check_cuda_availability() is False

    @patch('code.generation.runner_gpu.torch')
    def test_cuda_runtime_error(self, mock_torch):
        """Test when CUDA allocation fails."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.zeros.side_effect = RuntimeError("CUDA error")
        assert check_cuda_availability() is False

    def test_torch_not_installed(self):
        """Test when torch is not installed."""
        with patch.dict('sys.modules', {'torch': None}):
            assert check_cuda_availability() is False


class TestLoadModel:
    """Tests for model loading."""

    @patch('code.generation.runner_gpu.check_cuda_availability')
    @patch('code.generation.runner_gpu.Llama')
    def test_load_model_success(self, mock_llama, mock_cuda_check):
        """Test successful model loading."""
        mock_cuda_check.return_value = True
        mock_instance = MagicMock()
        mock_llama.return_value = mock_instance

        model = load_model("test_model.gguf", n_ctx=2048, n_gpu_layers=35)

        mock_llama.assert_called_once_with(
            model_path="test_model.gguf",
            n_ctx=2048,
            n_gpu_layers=35,
            verbose=False
        )
        assert model == mock_instance

    @patch('code.generation.runner_gpu.check_cuda_availability')
    def test_load_model_no_cuda(self, mock_cuda_check):
        """Test model loading fails without CUDA."""
        mock_cuda_check.return_value = False

        with pytest.raises(HardwareError, match="CUDA is not available"):
            load_model("test_model.gguf")

    @patch('code.generation.runner_gpu.check_cuda_availability')
    def test_load_model_import_error(self, mock_cuda_check):
        """Test model loading fails with ImportError."""
        mock_cuda_check.return_value = True
        with patch('code.generation.runner_gpu.Llama', side_effect=ImportError("No module")):
            with pytest.raises(HardwareError, match="llama-cpp-python not installed"):
                load_model("test_model.gguf")


class TestGenerateSample:
    """Tests for sample generation."""

    @patch('code.generation.runner_gpu.log_operation')
    @patch('code.generation.runner_gpu.get_logger')
    def test_generate_sample_success(self, mock_logger, mock_log_op):
        """Test successful sample generation."""
        mock_model = MagicMock()
        mock_model.set_seed = MagicMock()
        mock_output = {
            'choices': [{'text': 'This is a generated response.'}]
        }
        mock_model.return_value = mock_output

        result = generate_sample(
            model=mock_model,
            prompt="Test prompt",
            strategy="Direct",
            prompt_id="p1",
            seed=12345
        )

        assert result['prompt_id'] == "p1"
        assert result['strategy'] == "Direct"
        assert result['seed'] == 12345
        assert 'generated_text' in result
        assert result['model'] == "Mistral-7B-Instruct-v0.2"
        assert result['device'] == "cuda"

    @patch('code.generation.runner_gpu.log_operation')
    @patch('code.generation.runner_gpu.get_logger')
    def test_generate_sample_failure(self, mock_logger, mock_log_op):
        """Test sample generation failure raises error."""
        mock_model = MagicMock()
        mock_model.set_seed = MagicMock()
        mock_model.return_value.side_effect = Exception("Generation failed")

        with pytest.raises(GenerationError, match="Generation failed for prompt"):
            generate_sample(
                model=mock_model,
                prompt="Test prompt",
                strategy="Direct",
                prompt_id="p1",
                seed=12345
            )


class TestLoadPrompts:
    """Tests for prompt loading."""

    def test_load_prompts_list_format(self):
        """Test loading prompts in list format."""
        prompts_data = [
            {"id": "p1", "prompt": "First prompt"},
            {"id": "p2", "prompt": "Second prompt"}
        ]

        with patch('builtins.open', mock_open(read_data=json.dumps(prompts_data))):
            prompts = load_prompts("test_prompts.json")

        assert len(prompts) == 2
        assert prompts[0]['id'] == "p1"

    def test_load_prompts_dict_format(self):
        """Test loading prompts in dict format with 'prompts' key."""
        prompts_data = {
            "prompts": [
                {"id": "p1", "prompt": "First prompt"}
            ]
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(prompts_data))):
            prompts = load_prompts("test_prompts.json")

        assert len(prompts) == 1

    def test_load_prompts_file_not_found(self):
        """Test loading prompts from non-existent file."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            with pytest.raises(FileNotFoundError):
                load_prompts("non_existent.json")

    def test_load_prompts_invalid_json(self):
        """Test loading prompts with invalid JSON."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_prompts("test.json")


class TestSaveBatch:
    """Tests for batch saving."""

    def test_save_batch_creates_file(self):
        """Test that save_batch creates a file with correct content."""
        samples = [
            {"id": 1, "text": "Sample 1"},
            {"id": 2, "text": "Sample 2"}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            save_batch(samples, output_path, batch_id=1)

            filepath = output_path / "generation_batch_gpu_mistral_001.json"
            assert filepath.exists()

            with open(filepath, 'r') as f:
                saved_data = json.load(f)

            assert len(saved_data) == 2
            assert saved_data[0]['id'] == 1


class TestRunGenerationPipeline:
    """Tests for the full generation pipeline."""

    @patch('code.generation.runner_gpu.load_prompts')
    @patch('code.generation.runner_gpu.load_model')
    @patch('code.generation.runner_gpu.generate_sample')
    @patch('code.generation.runner_gpu.save_batch')
    def test_run_pipeline_basic(self, mock_save, mock_gen, mock_load_model, mock_load_prompts):
        """Test basic pipeline execution."""
        mock_load_prompts.return_value = [
            {"id": "p1", "prompt": "Test prompt 1"},
            {"id": "p2", "prompt": "Test prompt 2"}
        ]
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        mock_gen.return_value = {
            "prompt_id": "p1",
            "strategy": "Direct",
            "seed": 123,
            "generated_text": "Generated text"
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_generation_pipeline(
                config={"prompts_path": "test.json", "output_dir": tmpdir, "gpu_model_path": "model.gguf"},
                samples_per_prompt=2
            )

            assert len(result) == 2 * 4 * 2  # 2 prompts * 4 strategies * 2 samples
            mock_load_model.assert_called_once()

    @patch('code.generation.runner_gpu.load_prompts')
    @patch('code.generation.runner_gpu.load_model')
    @patch('code.generation.runner_gpu.generate_sample')
    def test_run_pipeline_with_config(self, mock_gen, mock_load_model, mock_load_prompts):
        """Test pipeline with explicit config."""
        mock_load_prompts.return_value = [{"id": "p1", "prompt": "Prompt 1"}]
        mock_load_model.return_value = MagicMock()
        mock_gen.return_value = {"prompt_id": "p1", "strategy": "Direct", "seed": 1, "generated_text": "Text"}

        with tempfile.TemporaryDirectory() as tmpdir:
            run_generation_pipeline(
                config={
                    "prompts_path": "test.json",
                    "output_dir": tmpdir,
                    "gpu_model_path": "model.gguf"
                },
                samples_per_prompt=1
            )

            # Verify output directory was created
            assert Path(tmpdir).exists()
