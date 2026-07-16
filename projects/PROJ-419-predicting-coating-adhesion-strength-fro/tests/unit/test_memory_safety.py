import pytest
import os
import psutil
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    check_memory_limit, 
    get_memory_usage_mb, 
    MemoryLimitError,
    check_halt_signal
)

class TestMemorySafety:
    
    def test_check_memory_limit_safe(self):
        """Test that check_memory_limit returns True when usage is safe."""
        # Mock a low memory usage
        with patch('utils.psutil.Process') as MockProcess:
            mock_process = MagicMock()
            mock_process.memory_info.return_value = MagicMock(rss=100 * 1024 * 1024) # 100 MB
            MockProcess.return_value = mock_process
            
            # Should return True for 100MB usage with 7GB limit
            assert check_memory_limit(limit_gb=7, raise_error=True) is True
            
    def test_check_memory_limit_exceeded_raises(self):
        """Test that check_memory_limit raises MemoryLimitError when exceeded."""
        # Mock a high memory usage (8 GB)
        with patch('utils.psutil.Process') as MockProcess:
            mock_process = MagicMock()
            mock_process.memory_info.return_value = MagicMock(rss=8 * 1024 * 1024 * 1024) # 8 GB
            MockProcess.return_value = mock_process
            
            # Should raise error for 8GB usage with 7GB limit
            with pytest.raises(MemoryLimitError):
                check_memory_limit(limit_gb=7, raise_error=True)
                
    def test_check_memory_limit_exceeded_returns_false(self):
        """Test that check_memory_limit returns False when exceeded and raise_error=False."""
        # Mock a high memory usage
        with patch('utils.psutil.Process') as MockProcess:
            mock_process = MagicMock()
            mock_process.memory_info.return_value = MagicMock(rss=8 * 1024 * 1024 * 1024)
            MockProcess.return_value = mock_process
            
            # Should return False, not raise
            assert check_memory_limit(limit_gb=7, raise_error=False) is False

    def test_get_memory_usage_mb(self):
        """Test that get_memory_usage_mb returns a positive float."""
        usage = get_memory_usage_mb()
        assert isinstance(usage, float)
        assert usage > 0

    def test_check_halt_signal_backward_compatibility(self):
        """Test that check_halt_signal works without arguments."""
        # Create a temporary state dir if needed
        os.makedirs("state", exist_ok=True)
        
        # Ensure no signal exists
        signal_path = os.path.join("state", "HALT_SIGNAL.yaml")
        if os.path.exists(signal_path):
            os.remove(signal_path)
            
        # Should return False without error
        assert check_halt_signal() is False
        
    def test_check_halt_signal_with_arg(self):
        """Test that check_halt_signal works with state_dir argument."""
        os.makedirs("state", exist_ok=True)
        signal_path = os.path.join("state", "HALT_SIGNAL.yaml")
        if os.path.exists(signal_path):
            os.remove(signal_path)
            
        assert check_halt_signal("state") is False
        
        # Now create the signal
        with open(signal_path, 'w') as f:
            f.write("status: HALT\n")
            
        assert check_halt_signal("state") is True
        
        # Cleanup
        os.remove(signal_path)