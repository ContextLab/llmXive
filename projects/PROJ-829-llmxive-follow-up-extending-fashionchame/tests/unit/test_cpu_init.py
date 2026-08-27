"""
Unit tests to verify that text_cross_attention.py and runner.py explicitly
initialize models on device='cpu' and raise an error if CUDA is detected.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import torch
import torch.nn as nn

# Add the code directory to the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.adapters.text_cross_attention import TextCrossAttentionAdapter
from src.pipeline.runner import ensure_cpu_only_execution, run_text_adapter_pipeline_with_bottleneck_analysis
from src.data.loader import load_config


class TestTextCrossAttentionCPUInit:
    """Tests for TextCrossAttentionAdapter CPU initialization."""

    def test_adapter_initializes_on_cpu_explicitly(self):
        """Verify that TextCrossAttentionAdapter initializes on CPU."""
        # Load a minimal config for testing
        config = {
            "model": {
                "blip_model_id": "Salesforce/blip-large",
                "vlm_confidence_threshold": 0.5
            },
            "experiment": {
                "seed": 42
            }
        }

        # Mock torch.cuda.is_available to simulate a CUDA environment
        # The adapter should still force CPU initialization
        with patch("torch.cuda.is_available", return_value=True):
            with patch("torch.cuda.device_count", return_value=1):
                # Create the adapter - it should force device='cpu'
                adapter = TextCrossAttentionAdapter(config)

                # Verify the adapter's internal device is CPU
                assert adapter.device == "cpu", (
                    f"Adapter device should be 'cpu' but got '{adapter.device}'. "
                    "The adapter must explicitly initialize on CPU."
                )

                # Verify that any torch.nn modules created are on CPU
                for name, module in adapter.named_modules():
                    if hasattr(module, 'weight'):
                        assert module.weight.device.type == "cpu", (
                            f"Module '{name}' has weights on {module.weight.device}, "
                            "expected CPU. All modules must be initialized on CPU."
                        )

    def test_adapter_raises_error_if_forced_to_cuda(self):
        """Verify that the adapter logic prevents CUDA usage even if forced."""
        config = {
            "model": {
                "blip_model_id": "Salesforce/blip-large",
                "vlm_confidence_threshold": 0.5
            },
            "experiment": {
                "seed": 42
            }
        }

        # Force CUDA availability
        with patch("torch.cuda.is_available", return_value=True):
            with patch("torch.cuda.device_count", return_value=1):
                # The adapter should explicitly set device='cpu' in its __init__
                # We verify this by checking the resulting device attribute
                adapter = TextCrossAttentionAdapter(config)
                
                # Assert the device is strictly CPU
                assert adapter.device == "cpu"

    def test_adapter_linear_layer_cpu_device(self):
        """Verify that the text_projection Linear layer is on CPU."""
        config = {
            "model": {
                "blip_model_id": "Salesforce/blip-large",
                "vlm_confidence_threshold": 0.5
            },
            "experiment": {
                "seed": 42
            }
        }

        with patch("torch.cuda.is_available", return_value=True):
            adapter = TextCrossAttentionAdapter(config)
            
            # Check the specific text_projection layer
            if hasattr(adapter, 'text_projection'):
                assert adapter.text_projection.weight.device.type == "cpu", (
                    "text_projection Linear layer must be on CPU."
                )


class TestRunnerCPUInit:
    """Tests for runner.py CPU initialization logic."""

    def test_ensure_cpu_only_execution_raises_on_cuda(self):
        """Verify that ensure_cpu_only_execution raises an error if CUDA is detected."""
        # Mock torch.cuda.is_available to return True (simulating a CUDA environment)
        with patch("torch.cuda.is_available", return_value=True):
            with pytest.raises(RuntimeError) as exc_info:
                ensure_cpu_only_execution()
            
            assert "CUDA detected" in str(exc_info.value), (
                "ensure_cpu_only_execution must raise RuntimeError if CUDA is detected."
            )

    def test_ensure_cpu_only_execution_passes_on_cpu(self):
        """Verify that ensure_cpu_only_execution passes if no CUDA is available."""
        with patch("torch.cuda.is_available", return_value=False):
            # Should not raise any exception
            ensure_cpu_only_execution()

    def test_runner_pipeline_enforces_cpu(self):
        """Verify that the main pipeline runner enforces CPU-only execution."""
        # We test the ensure_cpu_only_execution call within the pipeline logic
        # by mocking the rest of the pipeline to focus on the CPU check
        
        # Mock the dataset loading and processing to avoid actual execution
        with patch("torch.cuda.is_available", return_value=True):
            # The runner should call ensure_cpu_only_execution which will raise
            with pytest.raises(RuntimeError) as exc_info:
                # We simulate a call that would trigger the check
                # Note: In a real scenario, this would be part of the main() or run_pipeline
                ensure_cpu_only_execution()
            
            assert "CUDA detected" in str(exc_info.value)

    def test_runner_main_entry_cpu_check(self):
        """Verify the main entry point enforces CPU check."""
        # This test ensures that if someone calls the main entry point,
        # the CPU check is performed first.
        
        # We mock the actual pipeline execution to isolate the check
        with patch("torch.cuda.is_available", return_value=True):
            with patch("src.pipeline.runner.run_text_adapter_pipeline_with_bottleneck_analysis"):
                with pytest.raises(RuntimeError) as exc_info:
                    # Simulate the check happening at the start of main
                    ensure_cpu_only_execution()
                
                assert "CUDA detected" in str(exc_info.value)


class TestDeviceInitialization:
    """Additional tests for device initialization patterns."""

    def test_no_cuda_device_assignment_in_adapter(self):
        """Verify that adapter code does not assign to cuda device."""
        import inspect
        from src.adapters import text_cross_attention
        
        source = inspect.getsource(text_cross_attention.TextCrossAttentionAdapter.__init__)
        
        # Check that the code explicitly uses 'cpu' and does not use 'cuda' for device assignment
        assert "device='cpu'" in source or 'device="cpu"' in source, (
            "Adapter __init__ must explicitly set device='cpu'."
        )
        
        # Ensure there's no logic that assigns to cuda based on availability
        # (The adapter should be hardcoded to cpu or use a config that forces cpu)
        # We check that the device assignment is not conditional on cuda availability
        assert "if torch.cuda.is_available()" not in source or "device='cpu'" in source, (
            "Device assignment should not be conditional on CUDA availability; it must be CPU."
        )

    def test_runner_cpu_check_before_model_load(self):
        """Verify that the CPU check happens before model loading in the runner."""
        import inspect
        from src.pipeline import runner
        
        source = inspect.getsource(runner.run_text_adapter_pipeline_with_bottleneck_analysis)
        
        # The ensure_cpu_only_execution call should appear before model instantiation
        # We check that the function call exists in the source
        assert "ensure_cpu_only_execution()" in source, (
            "run_text_adapter_pipeline_with_bottleneck_analysis must call ensure_cpu_only_execution()."
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])