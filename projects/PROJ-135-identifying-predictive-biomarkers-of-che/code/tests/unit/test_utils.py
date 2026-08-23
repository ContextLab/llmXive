import pytest
import os
import sys
from unittest.mock import patch, mock_open
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.utils import (
    detect_resources, 
    calculate_caps, 
    check_limits, 
    ResourceWarning,
    calculate_checksum
)

class TestDetectResources:
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="docker\n")
    @patch('os.environ.get')
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_detect_docker_resources(self, mock_mem, mock_cpu, mock_env, mock_open_file, mock_exists):
        """Test detection of Docker resources."""
        mock_exists.return_value = True
        mock_env.side_effect = lambda key: {'DOCKER_CPUS': '4', 'DOCKER_MEMORY': '8.0'}.get(key, None)
        mock_cpu.return_value = 8
        mock_mem.return_value.total = 16 * 1024 * 1024 * 1024
        
        resources = detect_resources()
        
        assert resources['cpus'] == 4
        assert resources['ram_gb'] == 8.0
        assert 'time_limit_hours' in resources

    @patch('os.path.exists')
    @patch('multiprocessing.cpu_count')
    @patch('psutil.virtual_memory')
    def test_detect_system_resources(self, mock_mem, mock_cpu, mock_exists):
        """Test detection of system resources (non-Docker)."""
        mock_exists.return_value = False
        mock_cpu.return_value = 12
        mock_mem.return_value.total = 32 * 1024 * 1024 * 1024
        
        resources = detect_resources()
        
        assert resources['cpus'] == 12
        assert resources['ram_gb'] == 32.0

class TestCalculateCaps:
    def test_calculate_caps_within_limits(self):
        """Test caps calculation when resources are within limits."""
        resources = {'cpus': 4, 'ram_gb': 8.0, 'time_limit_hours': 24}
        caps = calculate_caps(resources)
        
        assert caps['cpus'] == 4
        assert caps['ram_gb'] == 8.0
        assert caps['time_limit_hours'] == 12  # Max time limit

    def test_calculate_caps_exceeds_limits(self):
        """Test caps calculation when resources exceed limits."""
        resources = {'cpus': 16, 'ram_gb': 32.0, 'time_limit_hours': 48}
        caps = calculate_caps(resources)
        
        assert caps['cpus'] == 8  # Max CPUs
        assert caps['ram_gb'] == 16.0  # Max RAM
        assert caps['time_limit_hours'] == 12

class TestCheckLimits:
    def test_check_limits_within_threshold(self):
        """Test limit check when usage is within threshold."""
        current = {'cpus': 4, 'ram_gb': 8.0}
        caps = {'cpus': 8, 'ram_gb': 16.0}
        
        breached = check_limits(current, caps)
        assert breached is False

    def test_check_limits_exceeds_threshold(self):
        """Test limit check when usage exceeds threshold."""
        current = {'cpus': 8, 'ram_gb': 16.0}
        caps = {'cpus': 8, 'ram_gb': 16.0}
        
        breached = check_limits(current, caps)
        assert breached is True

class TestCalculateChecksum:
    def test_calculate_checksum_valid_file(self, tmp_path):
        """Test checksum calculation for a valid file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = calculate_checksum(str(test_file))
        assert len(checksum) == 64  # SHA256 hex length
        assert checksum == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

    def test_calculate_checksum_empty_file(self, tmp_path):
        """Test checksum calculation for an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        
        checksum = calculate_checksum(str(test_file))
        assert checksum == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
