import pytest
import os
from pathlib import Path
import sys
from setup_directories import create_directories

class TestDirectoryCreation:
    def test_create_directories(self):
        """Test directory creation."""
        create_directories()
        # Check if directories exist
        assert Path("data").exists()
        assert Path("results").exists()