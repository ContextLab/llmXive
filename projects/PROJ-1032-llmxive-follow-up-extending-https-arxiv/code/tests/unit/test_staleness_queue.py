"""
Unit tests for src/llmxive/staleness_queue.py

Tests verify:
1. Basic push/pop operations
2. Staleness clamping logic (Edge Case: staleness >= buffer_size)
3. Empty/Full state handling
4. Data integrity (tensor cloning)
"""

import pytest
import torch
import sys
import os

# Ensure the src directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.llmxive.staleness_queue import StalenessQueue
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR


class TestStalenessQueue:
    """Test suite for StalenessQueue class."""

    def test_init_positive_buffer_size(self):
        """Test initialization with valid buffer size."""
        queue = StalenessQueue(buffer_size=5)
        assert queue.buffer_size == 5
        assert len(queue) == 0
        assert queue.is_empty()
        assert not queue.is_full()

    def test_init_invalid_buffer_size(self):
        """Test initialization raises error for non-positive buffer size."""
        with pytest.raises(DATA_INTEGRITY_ERROR):
            StalenessQueue(buffer_size=0)
        
        with pytest.raises(DATA_INTEGRITY_ERROR):
            StalenessQueue(buffer_size=-1)

    def test_push_and_pop(self):
        """Test basic push and pop operations."""
        queue = StalenessQueue(buffer_size=3)
        grad = torch.tensor([1.0, 2.0, 3.0])
        
        queue.push(staleness=0, gradient=grad)
        assert len(queue) == 1
        
        staleness, popped_grad = queue.pop()
        assert staleness == 0
        assert torch.equal(popped_grad, grad)
        assert len(queue) == 0

    def test_staleness_clamping_edge_case(self):
        """
        Test that staleness is clamped to buffer_size - 1 if exceeded.
        This is the specific edge case requirement for T007.
        """
        buffer_size = 5
        queue = StalenessQueue(buffer_size=buffer_size)
        grad = torch.tensor([1.0])
        
        # Push a staleness much larger than buffer_size
        huge_staleness = 100
        queue.push(staleness=huge_staleness, gradient=grad)
        
        # Retrieve and verify clamping
        retrieved_staleness, _ = queue.peek()
        expected_max = buffer_size - 1
        
        assert retrieved_staleness == expected_max, (
            f"Expected staleness {expected_max}, got {retrieved_staleness}. "
            f"Clamping failed for huge_staleness={huge_staleness}"
        )

    def test_staleness_not_clamped_when_within_limit(self):
        """Test that valid staleness values are preserved."""
        queue = StalenessQueue(buffer_size=10)
        grad = torch.tensor([1.0])
        
        queue.push(staleness=4, gradient=grad)
        retrieved_staleness, _ = queue.peek()
        
        assert retrieved_staleness == 4

    def test_fifo_order(self):
        """Test that the queue maintains FIFO order."""
        queue = StalenessQueue(buffer_size=5)
        
        for i in range(3):
            queue.push(staleness=i, gradient=torch.tensor([float(i)]))
        
        # Pop and verify order
        for i in range(3):
            s, g = queue.pop()
            assert s == i
            assert g.item() == float(i)

    def test_buffer_overflow_replaces_oldest(self):
        """Test that adding beyond buffer_size removes the oldest item."""
        queue = StalenessQueue(buffer_size=3)
        
        # Fill the queue
        queue.push(0, torch.tensor([0.0]))
        queue.push(1, torch.tensor([1.0]))
        queue.push(2, torch.tensor([2.0]))
        
        assert len(queue) == 3
        assert queue.is_full()
        
        # Push one more
        queue.push(3, torch.tensor([3.0]))
        
        # Oldest (0) should be gone, newest (3) should be present
        # Current items should be 1, 2, 3
        items = queue.get_all()
        assert len(items) == 3
        assert items[0][0] == 1
        assert items[1][0] == 2
        assert items[2][0] == 3

    def test_pop_from_empty_queue(self):
        """Test that popping from an empty queue returns None."""
        queue = StalenessQueue(buffer_size=5)
        result = queue.pop()
        assert result is None

    def test_peek_from_empty_queue(self):
        """Test that peeking from an empty queue returns None."""
        queue = StalenessQueue(buffer_size=5)
        result = queue.peek()
        assert result is None

    def test_gradient_cloning(self):
        """Test that gradients are cloned to prevent external mutation issues."""
        queue = StalenessQueue(buffer_size=2)
        original_grad = torch.tensor([1.0, 2.0], requires_grad=True)
        
        queue.push(0, original_grad)
        _, stored_grad = queue.peek()
        
        # Modify original
        original_grad.data.fill_(999.0)
        
        # Stored gradient should be unchanged
        assert not torch.equal(stored_grad, original_grad)
        assert stored_grad.item() == 1.0

    def test_invalid_gradient_push(self):
        """Test that pushing None or non-tensor raises error."""
        queue = StalenessQueue(buffer_size=5)
        
        with pytest.raises(DATA_INTEGRITY_ERROR):
            queue.push(0, None)
        
        with pytest.raises(DATA_INTEGRITY_ERROR):
            queue.push(0, "not a tensor")
