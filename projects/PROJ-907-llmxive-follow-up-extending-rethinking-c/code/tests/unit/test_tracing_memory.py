import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import torch
import numpy as np
from pathlib import Path

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.tracing import get_memory_usage_gb, trace_single_image, trace_routing_batch

class TestTracingMemoryManagement:
    @patch('src.tracing.get_memory_usage_gb')
    def test_memory_guard_in_trace(self, mock_mem_usage):
        """Test that trace_routing_batch skips images when memory is high."""
        # Mock memory usage to be high
        mock_mem_usage.return_value = 7.0  # Above threshold

        # Mock model and dataset
        mock_model = MagicMock()
        mock_model.eval = MagicMock()
        mock_model.forward_with_trace = MagicMock(return_value=(None, []))

        mock_dataset_item = {'image': torch.zeros(3, 224, 224)}
        mock_iterator = [mock_dataset_item] * 5

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / 'cache'
            cache_dir.mkdir()
            results_log = Path(tmpdir) / 'log.jsonl'
            memory_log = Path(tmpdir) / 'mem.jsonl'

            trace_routing_batch(
                model=mock_model,
                dataset_iterator=iter(mock_dataset_item for _ in range(5)),
                num_images=5,
                timestep_schedule=list(range(10)),
                cache_dir=cache_dir,
                results_log_path=results_log,
                memory_log_path=memory_log,
                seed=42
            )

            # Verify that no files were created because memory was high
            assert len(list(cache_dir.glob('*.npz'))) == 0

    def test_get_memory_usage_gb_cpu(self):
        """Test memory usage function on CPU."""
        # This should not raise an error
        mem = get_memory_usage_gb()
        assert isinstance(mem, float)
        assert mem >= 0

    @patch('src.tracing.trace_single_image')
    def test_trace_single_image_error_handling(self, mock_trace):
        """Test that trace_single_image handles errors gracefully."""
        mock_trace.side_effect = Exception("Test error")

        mock_model = MagicMock()
        mock_image = torch.zeros(3, 224, 224)
        timestep_schedule = list(range(10))

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / 'cache'
            cache_dir.mkdir()

            # This should raise an exception
            with pytest.raises(Exception):
                trace_single_image(
                    model=mock_model,
                    image=mock_image,
                    timestep_schedule=timestep_schedule,
                    image_index=0,
                    cache_dir=cache_dir,
                    seed=42
                )
