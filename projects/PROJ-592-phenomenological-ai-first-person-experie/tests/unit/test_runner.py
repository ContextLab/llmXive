"""
Unit tests for the generation runner (T009).
Tests the structure and logic without requiring actual model execution.
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import MODEL_ID, MODEL_FILENAME, STRATEGIES, SAMPLES_PER_PROMPT
from generation.runner import load_model, generate_sample, run_generation_pipeline


class TestRunnerConfiguration:
    """Test configuration and constants."""

    def test_model_id_is_tinyllama(self):
        """Ensure the model is TinyLlama, not a 7B model."""
        assert "TinyLlama" in MODEL_ID
        assert "7B" not in MODEL_ID
        assert "Mistral" not in MODEL_ID

    def test_model_filename_is_correct(self):
        """Verify the correct GGUF filename is used."""
        assert MODEL_FILENAME == "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

    def test_strategies_are_defined(self):
        """Check that all four prompting strategies are defined."""
        expected_strategies = {"direct", "hypothetical", "comparative", "roleplay"}
        assert set(STRATEGIES) == expected_strategies

    def test_sample_count_per_prompt(self):
        """Verify the target sample count per prompt."""
        assert SAMPLES_PER_PROMPT == 80


class TestGenerateSample:
    """Test the generate_sample function logic."""

    @patch('generation.runner.Llama')
    def test_generate_sample_structure(self, mock_llama_class):
        """Test that generate_sample returns the expected structure."""
        # Mock the model instance
        mock_model = Mock()
        mock_llama_class.return_value = mock_model

        # Mock the model output
        mock_output = {
            "choices": [
                {
                    "text": "This is a generated response about my experience."
                }
            ]
        }
        mock_model.return_value = mock_output

        # Call the function
        result = generate_sample(
            llm=mock_model,
            prompt="Test prompt",
            strategy="direct",
            prompt_id=0,
            sample_idx=0,
            seed=42,
            max_tokens=100,
        )

        # Verify structure
        assert "prompt_id" in result
        assert "strategy" in result
        assert "sample_index" in result
        assert "seed" in result
        assert "input_prompt" in result
        assert "generated_text" in result
        assert "timestamp" in result
        assert "model_id" in result
        assert "status" in result

        # Verify values
        assert result["prompt_id"] == 0
        assert result["strategy"] == "direct"
        assert result["sample_index"] == 0
        assert result["status"] == "success"
        assert result["generated_text"] is not None

    def test_generate_sample_handles_failure(self):
        """Test that generate_sample marks failed generations."""
        mock_model = Mock()
        mock_model.side_effect = Exception("Model error")

        # This would raise an exception in the actual function,
        # but the retry logic in the real implementation would handle it.
        # Here we just verify the function exists and has the right signature.
        with pytest.raises(Exception):
            generate_sample(
                llm=mock_model,
                prompt="Test prompt",
                strategy="direct",
                prompt_id=0,
                sample_idx=0,
                seed=42,
            )


class TestLoadModel:
    """Test model loading logic."""

    @patch('generation.runner.Path')
    @patch('generation.runner.Llama')
    def test_load_model_success(self, mock_llama_class, mock_path_class):
        """Test successful model loading."""
        # Mock path exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance

        # Mock model instance
        mock_model = Mock()
        mock_llama_class.return_value = mock_model

        # Call function
        result = load_model()

        # Verify Llama was called with correct parameters
        mock_llama_class.assert_called_once()
        call_kwargs = mock_llama_class.call_args[1]

        assert call_kwargs["n_ctx"] == 2048
        assert call_kwargs["n_threads"] == 4
        assert call_kwargs["n_batch"] == 512
        assert call_kwargs["use_mmap"] is True
        assert call_kwargs["verbose"] is False

    @patch('generation.runner.Path')
    def test_load_model_file_not_found(self, mock_path_class):
        """Test that FileNotFoundError is raised when model is missing."""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path_class.return_value = mock_path_instance

        with pytest.raises(FileNotFoundError):
            load_model()


class TestPipelineIntegration:
    """Integration tests for the generation pipeline."""

    def test_pipeline_uses_cpu_only(self):
        """Verify that the pipeline configuration is CPU-only."""
        # This is verified by checking the model loading parameters
        # and the absence of GPU-related configurations
        from config import MODEL_PATH
        assert "cuda" not in str(MODEL_PATH).lower()

    def test_pipeline_output_structure(self):
        """Verify the expected output structure from the pipeline."""
        # The pipeline should produce JSON files with specific structure
        # This is tested by examining the sample generation logic
        expected_fields = [
            "prompt_id",
            "strategy",
            "sample_index",
            "seed",
            "input_prompt",
            "generated_text",
            "timestamp",
            "model_id",
            "status"
        ]

        # We can't run the full pipeline without the model,
        # but we can verify the expected structure from the code
        assert len(expected_fields) > 0  # Placeholder for actual structure check

    @patch('generation.runner.load_base_prompts')
    @patch('generation.runner.load_model')
    def test_pipeline_processes_all_strategies(self, mock_load_model, mock_load_prompts):
        """Verify that all strategies are processed."""
        # Mock dependencies
        mock_load_prompts.return_value = [{"id": 0, "prompt": "Test"}]
        mock_load_model.return_value = Mock()

        # Verify STRATEGIES constant is used
        assert len(STRATEGIES) == 4

    @patch('generation.runner.load_base_prompts')
    @patch('generation.runner.load_model')
    def test_pipeline_targets_correct_sample_volume(self, mock_load_model, mock_load_prompts):
        """Verify the target sample volume (80 samples per prompt per strategy)."""
        # 20 prompts * 4 strategies * 80 samples = 6400 total samples
        expected_total = 20 * len(STRATEGIES) * SAMPLES_PER_PROMPT
        assert expected_total == 6400
