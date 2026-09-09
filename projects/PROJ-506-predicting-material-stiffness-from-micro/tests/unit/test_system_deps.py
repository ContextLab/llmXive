"""
Unit tests for system dependency checks.
"""
import unittest
from unittest.mock import patch, MagicMock
import subprocess
import platform
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_system_deps import check_fftw3_availability

class TestSystemDeps(unittest.TestCase):

    @patch('setup_system_deps.platform.system')
    @patch('setup_system_deps.subprocess.run')
    def test_fftw3_found(self, mock_run, mock_platform):
        """Test that the function returns True when fftw3 is found."""
        mock_platform.return_value = "Linux"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="... libfftw3.so.3 ... (libc6,x86-64) ...\n"
        )

        result = check_fftw3_availability()
        self.assertTrue(result)

    @patch('setup_system_deps.platform.system')
    @patch('setup_system_deps.subprocess.run')
    def test_fftw3_not_found(self, mock_run, mock_platform):
        """Test that the function returns False when fftw3 is missing."""
        mock_platform.return_value = "Linux"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="... libsomethingelse.so.1 ... (libc6,x86-64) ...\n"
        )

        result = check_fftw3_availability()
        self.assertFalse(result)

    @patch('setup_system_deps.platform.system')
    def test_non_linux_platform(self, mock_platform):
        """Test that the function returns False on non-Linux platforms."""
        mock_platform.return_value = "Darwin"
        
        result = check_fftw3_availability()
        self.assertFalse(result)

    @patch('setup_system_deps.platform.system')
    def test_ldconfig_not_found(self, mock_platform):
        """Test handling of FileNotFoundError for ldconfig."""
        mock_platform.return_value = "Linux"
        
        with patch('setup_system_deps.subprocess.run', side_effect=FileNotFoundError("ldconfig")):
            result = check_fftw3_availability()
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()