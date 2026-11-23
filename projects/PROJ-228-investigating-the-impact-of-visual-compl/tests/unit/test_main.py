"""
Unit tests for the main orchestrator.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.main import get_memory_usage_gb, check_memory_limit, get_subject_list

class TestMemoryFunctions:
    def test_get_memory_usage_gb_returns_number(self):
        """Test that memory usage returns a float."""
        usage = get_memory_usage_gb()
        assert isinstance(usage, float)
        assert usage >= 0.0

    @patch('code.main.get_memory_usage_gb')
    def test_check_memory_limit_passes(self, mock_get_mem):
        """Test that check returns True when under limit."""
        mock_get_mem.return_value = 2.0 # 2GB
        assert check_memory_limit() is True

    @patch('code.main.get_memory_usage_gb')
    def test_check_memory_limit_fails(self, mock_get_mem):
        """Test that check returns False when over limit."""
        mock_get_mem.return_value = 10.0 # 10GB
        assert check_memory_limit() is False

class TestSubjectList:
    @patch('code.main.DATA_RAW_DIR')
    def test_get_subject_list_returns_sorted(self, mock_dir):
        """Test that subject list is sorted and filtered."""
        # Mock directory structure
        mock_dir.exists.return_value = True
        mock_dir.iterdir.return_value = [
            MagicMock(is_dir=lambda: True, name="sub-01"),
            MagicMock(is_dir=lambda: True, name="sub-02"),
            MagicMock(is_dir=lambda: False, name="logs"),
            MagicMock(is_dir=lambda: True, name="sub-10"),
        ]
        
        subjects = get_subject_list()
        
        assert subjects == ["sub-01", "sub-02", "sub-10"]
        assert subjects == sorted(subjects)

    @patch('code.main.DATA_RAW_DIR')
    def test_get_subject_list_empty(self, mock_dir):
        """Test empty list when no subjects."""
        mock_dir.exists.return_value = False
        subjects = get_subject_list()
        assert subjects == []