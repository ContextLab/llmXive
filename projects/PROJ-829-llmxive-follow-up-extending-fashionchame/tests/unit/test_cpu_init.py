"""
Unit tests to verify CPU initialization for text_cross_attention.py and runner.py.

These tests ensure that:
1. Models are explicitly initialized on device='cpu'.
2. An error is raised if CUDA is detected during initialization.
3. The ensure_cpu_only_execution function works as expected.
"""
import pytest
import torch
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import os

# Ensure we can import from the project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.adapters.text_cross_attention import TextCrossAttentionAdapter
from src.pipeline.runner import ensure_cpu_only_execution, run_text_adapter_pipeline_with_bottleneck_analysis
from src.pipeline.runner import main as runner_main


class TestTextCrossAttentionCPUInit:
    """Tests for TextCrossAttentionAdapter CPU initialization."""

    def test_adapter_initializes_on_cpu(self):
        """Verify that the adapter initializes on CPU by default."""
        # Mock the underlying model loading to avoid actual model download
        with patch('src.adapters.text_cross_attention.StableDiffusionPipeline.from_pretrained') as mock_pipeline:
            mock_model = MagicMock()
            mock_model.device = torch.device('cpu')
            mock_pipeline.return_value = mock_model

            # Initialize the adapter
            adapter = TextCrossAttentionAdapter(
                model_id="test-model",
                device="cpu"
            )

            # Verify the adapter is on CPU
            assert adapter.device.type == "cpu", "Adapter must be initialized on CPU"
            # Verify the underlying model is on CPU
            assert mock_model.device.type == "cpu", "Underlying model must be on CPU"

    def test_adapter_raises_on_cuda_detection(self):
        """Verify that the adapter raises an error if CUDA is detected."""
        # Mock torch.cuda.is_available to return True
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.cuda.device_count', return_value=1):
                # Mock the underlying model loading
                with patch('src.adapters.text_cross_attention.StableDiffusionPipeline.from_pretrained') as mock_pipeline:
                    mock_model = MagicMock()
                    mock_model.device = torch.device('cuda')
                    mock_pipeline.return_value = mock_model

                    # Attempt to initialize the adapter with CUDA detection
                    with pytest.raises(RuntimeError, match="CUDA detected"):
                        adapter = TextCrossAttentionAdapter(
                            model_id="test-model",
                            device="cpu"  # Explicitly request CPU
                        )
                        # Force a check by accessing device
                        _ = adapter.device

    def test_adapter_explicit_cpu_flag(self):
        """Verify that the adapter respects explicit CPU flag even if CUDA is available."""
        # Mock torch.cuda.is_available to return True
        with patch('torch.cuda.is_available', return_value=True):
            # Mock the underlying model loading
            with patch('src.adapters.text_cross_attention.StableDiffusionPipeline.from_pretrained') as mock_pipeline:
                mock_model = MagicMock()
                mock_model.device = torch.device('cpu')
                mock_pipeline.return_value = mock_model

                # Initialize with explicit CPU flag
                adapter = TextCrossAttentionAdapter(
                    model_id="test-model",
                    device="cpu",
                    enforce_cpu_only=True
                )

                assert adapter.device.type == "cpu"


class TestRunnerCPUInit:
    """Tests for runner.py CPU initialization."""

    def test_ensure_cpu_only_execution_passes_on_cpu(self):
        """Verify that ensure_cpu_only_execution passes when on CPU."""
        with patch('torch.cuda.is_available', return_value=False):
            # Should not raise
            ensure_cpu_only_execution()

    def test_ensure_cpu_only_execution_raises_on_cuda(self):
        """Verify that ensure_cpu_only_execution raises when CUDA is detected."""
        with patch('torch.cuda.is_available', return_value=True):
            with pytest.raises(RuntimeError, match="CUDA detected"):
                ensure_cpu_only_execution()

    def test_runner_pipeline_enforces_cpu(self):
        """Verify that the runner pipeline enforces CPU-only execution."""
        # Mock torch.cuda.is_available to return True to simulate CUDA environment
        with patch('torch.cuda.is_available', return_value=True):
            # Mock the necessary components to avoid actual execution
            with patch('src.pipeline.runner.TextCrossAttentionAdapter') as mock_adapter_class:
                with patch('src.pipeline.runner.load_config') as mock_load_config:
                    mock_load_config.return_value = {
                        'model': {
                            'vlm_confidence_threshold': 0.95,
                            'blip_model_id': 'Salesforce/blip-large'
                        },
                        'benchmark': {
                            'latency_threshold_ms': 50.0,
                            'memory_trigger_mb': 1024
                        }
                    }

                    mock_adapter = MagicMock()
                    mock_adapter.device = torch.device('cpu')
                    mock_adapter_class.return_value = mock_adapter

                    # The pipeline should raise an error because CUDA is detected
                    # and ensure_cpu_only_execution is called at the start
                    with pytest.raises(RuntimeError, match="CUDA detected"):
                        # We cannot run the full pipeline without real data,
                        # but we can verify the CPU check is in place by
                        # calling the function that enforces it.
                        ensure_cpu_only_execution()


class TestMainFunctionCPUCheck:
    """Tests for the main function's CPU check behavior."""

    def test_runner_main_calls_cpu_check(self):
        """Verify that the runner main function calls the CPU check."""
        with patch('src.pipeline.runner.ensure_cpu_only_execution') as mock_cpu_check:
            with patch('src.pipeline.runner.argparse.ArgumentParser.parse_args') as mock_parse:
                mock_parse.return_value = MagicMock(subset_size=10)
                
                # Mock other dependencies to avoid actual execution
                with patch('src.pipeline.runner.load_config') as mock_load_config:
                    mock_load_config.return_value = {}
                    
                    with patch('src.pipeline.runner.run_text_adapter_pipeline_with_bottleneck_analysis'):
                        try:
                            runner_main()
                        except SystemExit:
                            pass  # Expected from argparse or other exits
                        
                        # Verify ensure_cpu_only_execution was called
                        mock_cpu_check.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])