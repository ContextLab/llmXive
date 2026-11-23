"""
Integration tests for pipeline safety gates.
"""
import pytest
import os
import yaml
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils import check_halt_signal, write_halt_signal

class TestPipelineGates:
    """Integration tests for halt signal logic."""

    def setup_method(self):
        """Set up test environment."""
        self.state_dir = Path("state")
        self.state_dir.mkdir(exist_ok=True)
        self.halt_file = self.state_dir / "HALT_SIGNAL.yaml"
        if self.halt_file.exists():
            self.halt_file.unlink()

    def teardown_method(self):
        """Clean up test environment."""
        if self.halt_file.exists():
            self.halt_file.unlink()
        if self.state_dir.exists():
            self.state_dir.rmdir()

    def test_halt_signal_flow(self):
        """Test the full flow of writing and checking a halt signal."""
        # Initially, no halt signal
        assert check_halt_signal() is False

        # Write a halt signal
        write_halt_signal("Test failure", self.state_dir)
        
        # Verify it is detected
        assert check_halt_signal() is True
        assert check_halt_signal(self.state_dir) is True

    def test_halt_signal_with_path(self):
        """Test writing to one path and checking from another."""
        other_dir = Path("test_state_other")
        other_dir.mkdir(exist_ok=True)
        other_halt = other_dir / "HALT_SIGNAL.yaml"
        
        try:
            write_halt_signal("Test", other_dir)
            
            # Check from the specific path
            assert check_halt_signal(other_dir) is True
            
            # Check from default (should be False)
            assert check_halt_signal() is False
        finally:
            if other_halt.exists():
                other_halt.unlink()
            if other_dir.exists():
                other_dir.rmdir()
