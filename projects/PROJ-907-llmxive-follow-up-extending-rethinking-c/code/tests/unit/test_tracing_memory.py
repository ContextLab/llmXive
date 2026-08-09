import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import torch
import numpy as np
from pathlib import Path

# Add code to path if not already
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from src.tracing import get_memory_usage_gb, trace_routing, log_data_source_verification
from src.utils import memory_guard

class TestTracingMemoryManagement:
    """
    Tests for T037: Memory management in tracing (batch size 1, logging peaks).
    """

    @patch('src.tracing.psutil')
    def test_get_memory_usage_cpu(self, mock_psutil):
        """Test memory usage reporting on CPU."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 2 * (1024 ** 3) # 2GB
        mock_psutil.Process.return_value = mock_process

        mem = get_memory_usage_gb()
        assert abs(mem - 2.0) < 0.01

    def test_memory_guard_pass(self):
        """Test memory guard when usage is below threshold."""
        # Mock get_memory_usage_gb to return 1.0GB
        with patch('src.tracing.get_memory_usage_gb', return_value=1.0):
            assert memory_guard(6.0) is True

    def test_memory_guard_fail(self):
        """Test memory guard raises error when usage exceeds threshold."""
        with patch('src.tracing.get_memory_usage_gb', return_value=7.0):
            with pytest.raises(MemoryError):
                memory_guard(6.0)

    @patch('src.tracing.load_sit_xl_model')
    @patch('src.tracing.load_dataset')
    @patch('src.tracing.ensure_directories_exist')
    def test_trace_routing_batch_size_1(
        self, mock_ensure_dirs, mock_load_dataset, mock_load_model
    ):
        """
        Test that trace_routing processes images in batches of size 1
        and logs memory peaks.
        """
        # Mock model
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model

        # Mock dataset iterator
        mock_dataset = MagicMock()
        mock_dataset.__iter__.return_value = iter([
            {'image': MagicMock(), 'label': 0, 'id': 'img_0001'},
            {'image': MagicMock(), 'label': 1, 'id': 'img_0002'},
        ])
        mock_load_dataset.return_value = mock_dataset

        # Mock preprocess_image
        with patch('src.tracing.preprocess_image', return_value=torch.randn(3, 224, 224)):
            with patch('src.tracing.get_memory_usage_gb', side_effect=[1.0, 1.1, 1.2]): # Simulate rising memory
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Run tracing
                    # We pass a custom iterator to avoid full dataset load
                    def mock_iterator():
                        yield ['img_0001'], [torch.randn(3, 224, 224)]
                        yield ['img_0002'], [torch.randn(3, 224, 224)]

                    stats = trace_routing(
                        model=mock_model,
                        image_iterator=mock_iterator(),
                        num_images=2,
                        output_dir=tmpdir,
                        batch_size=1,
                        memory_threshold_gb=6.0
                    )

                    # Verify stats
                    assert stats['processed'] == 2
                    assert stats['failed'] == 0
                    assert stats['peak_memory_gb'] == 1.2
                    assert len(stats['memory_log']) == 2

                    # Verify files were created
                    assert os.path.exists(os.path.join(tmpdir, 'img_0001.npy'))
                    assert os.path.exists(os.path.join(tmpdir, 'img_0002.npy'))

    @patch('src.tracing.get_memory_usage_gb', return_value=7.0)
    @patch('src.tracing.load_sit_xl_model')
    def test_trace_routing_memory_exceeded(self, mock_load_model, mock_mem_usage):
        """Test that trace_routing fails loudly if memory exceeds threshold."""
        mock_model = MagicMock()
        
        def mock_iterator():
            yield ['img_0001'], [torch.randn(3, 224, 224)]

        with pytest.raises(MemoryError):
            trace_routing(
                model=mock_model,
                image_iterator=mock_iterator(),
                num_images=1,
                output_dir="/tmp/test",
                batch_size=1,
                memory_threshold_gb=6.0
            )

    def test_log_data_source_verification(self, caplog):
        """Test that data source verification logs correct info."""
        with patch('src.tracing.get_seed', return_value=42):
            with caplog.at_level("INFO"):
                log_data_source_verification("imagenet-1k", "validation", 100)
                
                assert "DATA SOURCE VERIFICATION" in caplog.text
                assert "imagenet-1k" in caplog.text
                assert "validation" in caplog.text
                assert "100" in caplog.text
                assert "DATA SOURCE HASH" in caplog.text
                assert "Random Seed" in caplog.text
                assert "42" in caplog.text