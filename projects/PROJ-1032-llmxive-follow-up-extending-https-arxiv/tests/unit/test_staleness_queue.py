"""Unit tests for StalenessQueue."""
import pytest
import torch
import sys
import os
from src.llmxive.staleness_queue import StalenessQueue
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR

class TestStalenessQueue:
    """Tests for StalenessQueue."""
    
    def test_initialization(self):
        """Test queue initialization."""
        queue = StalenessQueue(buffer_size=5)
        assert len(queue) == 0
        assert queue.is_empty()
    
    def test_push_and_pop(self):
        """Test pushing and popping gradients."""
        queue = StalenessQueue(buffer_size=5)
        grad = torch.randn(10)
        queue.push(grad, staleness=1)
        
        assert len(queue) == 1
        assert not queue.is_empty()
        
        popped = queue.pop_oldest()
        assert popped is not None
        assert torch.equal(popped[0], grad)
        assert popped[1] == 1
    
    def test_clamping_logic(self):
        """Test that staleness is clamped to buffer_size - 1."""
        queue = StalenessQueue(buffer_size=3)
        grad = torch.randn(10)
        
        # Push with staleness larger than buffer
        queue.push(grad, staleness=10)
        
        # Get oldest - staleness should be clamped to 2 (buffer_size - 1)
        oldest = queue.get_oldest()
        assert oldest is not None
        assert oldest[1] == 2  # Clamped value
    
    def test_buffer_overflow(self):
        """Test that queue respects buffer size."""
        queue = StalenessQueue(buffer_size=3)
        
        for i in range(5):
            queue.push(torch.randn(10), staleness=i)
        
        assert len(queue) == 3  # Max size
    
    def test_invalid_buffer_size(self):
        """Test that negative buffer size raises error."""
        with pytest.raises(DATA_INTEGRITY_ERROR):
            StalenessQueue(buffer_size=0)
        
        with pytest.raises(DATA_INTEGRITY_ERROR):
            StalenessQueue(buffer_size=-1)
