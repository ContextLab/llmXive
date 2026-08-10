"""
Unit tests for T015b: scheduler_execution.py
Tests adaptive chunking, straggler detection, and OOM handling logic.
"""

import pytest
import time
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timezone

from orchestrator.scheduler_execution import (
    SchedulerExecution,
    SchedulerExecutionError,
    OOMError,
    StragglerDetectedError,
    TaskAssignment,
    BASE_CHUNK_SIZE_BYTES,
    MIN_CHUNK_SIZE_BYTES
)
from orchestrator.models import PhysicalNode, TaskChunk, NodeStatus
from orchestrator.node_manager import NodeManager
from orchestrator.completion_feedback import CompletionFeedbackManager


@pytest.fixture
def mock_node_manager():
    manager = MagicMock(spec=NodeManager)
    # Mock get_client to return a mock SSH client
    mock_client = MagicMock()
    manager.get_client.return_value = mock_client
    return manager


@pytest.fixture
def mock_feedback_manager():
    return MagicMock(spec=CompletionFeedbackManager)


@pytest.fixture
def mock_benchmark_runner():
    def runner(node, chunk):
        return {"status": "success", "time": 1.0}
    return runner


@pytest.fixture
def sample_node():
    return PhysicalNode(
        ip="192.168.1.10",
        hostname="node1",
        status=NodeStatus.ONLINE
    )


@pytest.fixture
def sample_chunk():
    return TaskChunk(
        id="chunk-001",
        start=0,
        end=1000,
        iterations=1000
    )


class TestAdaptiveChunking:
    def test_chunk_size_reduction_when_ram_low(self, mock_node_manager, mock_feedback_manager, mock_benchmark_runner, sample_node, sample_chunk):
        """
        Test that chunk size is reduced when available RAM is less than base chunk size.
        """
        # Setup RAM check to return 10MB (10 * 1024 * 1024 bytes)
        # Base chunk is 100MB.
        # Expected result: chunk size should be halved until <= 10MB.
        # 100 -> 50 -> 25 -> 12.5 -> 6.25 (MB). So 6.25MB should be the result.
        available_ram_bytes = 10 * 1024 * 1024
        expected_size = 6 * 1024 * 1024  # 6MB (integer division of 12.5 -> 6.25 -> 6)

        # Mock the SSH output for 'free -m'
        # Mem: total used free shared buff/cache available
        mock_output = "Mem: 1000 200 100 10 50 6000\n" # 6000 MB available? No, we want 10MB.
        # Let's set available to 10 MB.
        mock_output = "Mem: 1000 900 5 10 90 10\n" # available = 10 MB

        mock_client = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(read=lambda: mock_output.encode()), MagicMock())
        mock_node_manager.get_client.return_value = mock_client

        scheduler = SchedulerExecution(
            node_manager=mock_node_manager,
            feedback_manager=mock_feedback_manager,
            benchmark_runner_func=mock_benchmark_runner,
            chunk_size_bytes=BASE_CHUNK_SIZE_BYTES
        )

        # Call assign_chunk
        assignment = scheduler.assign_chunk(sample_chunk, sample_node)

        # Verify effective size is reduced
        assert assignment.chunk.effective_size <= available_ram_bytes
        # Verify it is not below minimum
        assert assignment.chunk.effective_size >= MIN_CHUNK_SIZE_BYTES


    def test_chunk_size_not_reduced_when_ram_high(self, mock_node_manager, mock_feedback_manager, mock_benchmark_runner, sample_node, sample_chunk):
        """
        Test that chunk size remains base size when available RAM is sufficient.
        """
        available_ram_bytes = 200 * 1024 * 1024 # 200 MB

        mock_output = "Mem: 1000 200 500 10 200 200000\n" # available = 200000 MB (enough)

        mock_client = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(read=lambda: mock_output.encode()), MagicMock())
        mock_node_manager.get_client.return_value = mock_client

        scheduler = SchedulerExecution(
            node_manager=mock_node_manager,
            feedback_manager=mock_feedback_manager,
            benchmark_runner_func=mock_benchmark_runner,
            chunk_size_bytes=BASE_CHUNK_SIZE_BYTES
        )

        assignment = scheduler.assign_chunk(sample_chunk, sample_node)

        assert assignment.chunk.effective_size == BASE_CHUNK_SIZE_BYTES


    def test_chunk_size_minimum_floor(self, mock_node_manager, mock_feedback_manager, mock_benchmark_runner, sample_node, sample_chunk):
        """
        Test that chunk size never goes below MIN_CHUNK_SIZE_BYTES.
        """
        # Set available RAM to 0.5 MB (less than min)
        available_ram_bytes = 0.5 * 1024 * 1024

        mock_output = "Mem: 1000 999 0 10 0 500\n" # 500 KB

        mock_client = MagicMock()
        mock_client.exec_command.return_value = (MagicMock(), MagicMock(read=lambda: mock_output.encode()), MagicMock())
        mock_node_manager.get_client.return_value = mock_client

        scheduler = SchedulerExecution(
            node_manager=mock_node_manager,
            feedback_manager=mock_feedback_manager,
            benchmark_runner_func=mock_benchmark_runner,
            chunk_size_bytes=BASE_CHUNK_SIZE_BYTES
        )

        assignment = scheduler.assign_chunk(sample_chunk, sample_node)

        assert assignment.chunk.effective_size == MIN_CHUNK_SIZE_BYTES


class TestStragglerHandling:
    def test_straggler_detection(self, mock_node_manager, mock_feedback_manager, sample_node, sample_chunk):
        """
        Test that a task exceeding the time limit is detected as a straggler.
        """
        # Create a benchmark runner that sleeps for 10 seconds
        def slow_runner(node, chunk):
            time.sleep(10)
            return {"status": "success"}

        scheduler = SchedulerExecution(
            node_manager=mock_node_manager,
            feedback_manager=mock_feedback_manager,
            benchmark_runner_func=slow_runner,
            chunk_size_bytes=BASE_CHUNK_SIZE_BYTES
        )

        # Set a very low median time to trigger straggler detection quickly
        scheduler.median_task_time = 1.0 # Threshold will be 2.0s

        assignment = scheduler.assign_chunk(sample_chunk, sample_node)

        # Mock the feedback manager to avoid errors
        mock_feedback_manager.receive_task_status = MagicMock()

        with pytest.raises(StragglerDetectedError):
            scheduler._monitor_task(assignment)

    def test_normal_task_completion(self, mock_node_manager, mock_feedback_manager, mock_benchmark_runner, sample_node, sample_chunk):
        """
        Test that a normal task completes without straggler error.
        """
        scheduler = SchedulerExecution(
            node_manager=mock_node_manager,
            feedback_manager=mock_feedback_manager,
            benchmark_runner_func=mock_benchmark_runner,
            chunk_size_bytes=BASE_CHUNK_SIZE_BYTES
        )

        scheduler.median_task_time = 100.0 # High threshold

        assignment = scheduler.assign_chunk(sample_chunk, sample_node)

        # This should complete without raising an exception
        scheduler._monitor_task(assignment)

        assert assignment.status.name == "COMPLETED"


class TestOOMHandling:
    def test_oom_detection(self, mock_node_manager, mock_feedback_manager, sample_node, sample_chunk):
        """
        Test that an OOM error is raised and handled.
        """
        def oom_runner(node, chunk):
            return {"status": "failed", "oom_detected": True}

        scheduler = SchedulerExecution(
            node_manager=mock_node_manager,
            feedback_manager=mock_feedback_manager,
            benchmark_runner_func=oom_runner,
            chunk_size_bytes=BASE_CHUNK_SIZE_BYTES
        )

        assignment = scheduler.assign_chunk(sample_chunk, sample_node)

        with pytest.raises(OOMError):
            scheduler._monitor_task(assignment)