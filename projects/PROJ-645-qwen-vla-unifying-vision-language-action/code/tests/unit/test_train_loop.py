import os
import tempfile
import time
from unittest.mock import patch, MagicMock
import pytest
import torch
import numpy as np
import pandas as pd

from src.training.train_loop import (
    auto_adjust_batch_size,
    train_epoch,
    create_dataloader,
    RAM_THRESHOLD_GB,
    MIN_BATCH_SIZE,
)
from src.utils.resource_monitor import ResourceMonitor


class TestAutoAdjustBatchSize:
    def test_no_adjustment_needed(self):
        monitor = MagicMock(spec=ResourceMonitor)
        monitor.get_current_rss_gb.return_value = 4.0  # Below threshold
        assert auto_adjust_batch_size(32, monitor) == 32

    def test_adjustment_needed(self):
        monitor = MagicMock(spec=ResourceMonitor)
        monitor.get_current_rss_gb.return_value = 7.0  # Above threshold
        assert auto_adjust_batch_size(32, monitor) == 16

    def test_min_batch_size_respected(self):
        monitor = MagicMock(spec=ResourceMonitor)
        monitor.get_current_rss_gb.return_value = 10.0  # Very high
        # Even if current is 2, it should not go below MIN_BATCH_SIZE
        assert auto_adjust_batch_size(2, monitor) == MIN_BATCH_SIZE

    def test_already_at_min(self):
        monitor = MagicMock(spec=ResourceMonitor)
        monitor.get_current_rss_gb.return_value = 10.0
        assert auto_adjust_batch_size(MIN_BATCH_SIZE, monitor) == MIN_BATCH_SIZE


class TestCreateDataLoader:
    def test_create_dataloader_basic(self):
        # Create dummy data
        data = pd.DataFrame({
            "inputs": [np.random.rand(10) for _ in range(5)],
            "targets": [np.random.rand(5) for _ in range(5)],
        })
        # Mock tokenizer (not actually used in create_dataloader logic, just passed)
        mock_tokenizer = MagicMock()

        loader = create_dataloader(data, mock_tokenizer, batch_size=2, shuffle=False)
        assert loader.batch_size == 2
        assert len(loader.dataset) == 5


class TestTrainEpoch:
    @patch("src.training.train_loop.QwenVLActionModel")
    def test_epoch_runs_successfully(self, MockModel):
        # Setup mock model
        mock_instance = MagicMock()
        mock_instance.train = MagicMock()
        mock_instance.zero_grad = MagicMock()
        mock_instance.step = MagicMock()
        mock_loss = MagicMock()
        mock_loss.item.return_value = 0.5
        mock_output = MagicMock()
        mock_output.loss = mock_loss
        mock_instance.return_value = mock_output
        MockModel.return_value = mock_instance

        # Create dummy data
        data = pd.DataFrame({
            "inputs": [np.random.rand(10) for _ in range(4)],
            "targets": [np.random.rand(5) for _ in range(4)],
        })
        mock_tokenizer = MagicMock()
        loader = create_dataloader(data, mock_tokenizer, batch_size=2, shuffle=False)

        optimizer = torch.optim.Adam(mock_instance.parameters())
        monitor = MagicMock(spec=ResourceMonitor)
        monitor.get_current_rss_gb.return_value = 4.0

        start_time = time.time()

        stats = train_epoch(
            model=mock_instance,
            dataloader=loader,
            optimizer=optimizer,
            epoch=1,
            resource_monitor=monitor,
            start_time=start_time,
            batch_size=2,
        )

        assert stats["batches_completed"] == 2
        assert stats["avg_loss"] == 0.5

    def test_timeout_handling(self):
        # Create dummy data
        data = pd.DataFrame({
            "inputs": [np.random.rand(10) for _ in range(4)],
            "targets": [np.random.rand(5) for _ in range(4)],
        })
        mock_tokenizer = MagicMock()
        loader = create_dataloader(data, mock_tokenizer, batch_size=2, shuffle=False)

        mock_model = MagicMock()
        mock_model.train = MagicMock()
        mock_model.to = MagicMock()
        mock_loss = MagicMock()
        mock_loss.item.return_value = 0.5
        mock_output = MagicMock()
        mock_output.loss = mock_loss
        mock_model.return_value = mock_output

        optimizer = torch.optim.Adam(mock_model.parameters())
        monitor = MagicMock(spec=ResourceMonitor)
        monitor.get_current_rss_gb.return_value = 4.0

        # Simulate time already passed
        past_start_time = time.time() - 30000  # 8.3 hours ago

        stats = train_epoch(
            model=mock_model,
            dataloader=loader,
            optimizer=optimizer,
            epoch=1,
            resource_monitor=monitor,
            start_time=past_start_time,
            batch_size=2,
        )

        # Should stop immediately due to timeout
        assert stats["batches_completed"] == 0
        assert stats["avg_loss"] == 0.0