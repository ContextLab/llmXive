"""
Unit tests for the generate_requirements script.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Import the module to test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
from generate_requirements import (
    get_installed_packages,
    filter_packages,
    generate_requirements
)

class TestGetInstalledPackages:
    """Tests for get_installed_packages function."""
    
    @patch('generate_requirements.subprocess.run')
    def test_successful_package_list(self, mock_run):
        """Test successful retrieval of package list."""
        mock_run.return_value = MagicMock(
            stdout='numpy==1.24.0\npandas==2.0.0\n',
            stderr='',
            returncode=0
        )
        
        packages = get_installed_packages()
        
        assert len(packages) == 2
        assert 'numpy==1.24.0' in packages
        assert 'pandas==2.0.0' in packages
        mock_run.assert_called_once()
    
    @patch('generate_requirements.subprocess.run')
    def test_handles_empty_output(self, mock_run):
        """Test handling of empty package list."""
        mock_run.return_value = MagicMock(
            stdout='',
            stderr='',
            returncode=0
        )
        
        packages = get_installed_packages()
        
        assert packages == []
    
    @patch('generate_requirements.subprocess.run')
    def test_raises_on_error(self, mock_run):
        """Test that error is raised when subprocess fails."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, 'pip list')
        
        with pytest.raises(CalledProcessError):
            get_installed_packages()

class TestFilterPackages:
    """Tests for filter_packages function."""
    
    def test_filters_excluded_packages(self):
        """Test that packages matching exclusion patterns are removed."""
        packages = [
            'numpy==1.24.0',
            'pytest==7.0.0',
            'pandas==2.0.0',
            'black==23.0.0'
        ]
        
        filtered = filter_packages(packages, ['pytest', 'black'])
        
        assert len(filtered) == 2
        assert 'numpy==1.24.0' in filtered
        assert 'pandas==2.0.0' in filtered
        assert 'pytest==7.0.0' not in filtered
        assert 'black==23.0.0' not in filtered
    
    def test_case_insensitive_filtering(self):
        """Test that filtering is case-insensitive."""
        packages = ['PyTest==7.0.0', 'BLACK==23.0.0']
        
        filtered = filter_packages(packages, ['pytest', 'black'])
        
        assert filtered == []
    
    def test_empty_exclude_list(self):
        """Test that empty exclude list returns all packages."""
        packages = ['numpy==1.24.0', 'pandas==2.0.0']
        
        filtered = filter_packages(packages, [])
        
        assert filtered == packages
    
    def test_handles_empty_packages(self):
        """Test handling of empty strings in package list."""
        packages = ['numpy==1.24.0', '', 'pandas==2.0.0']
        
        filtered = filter_packages(packages, [])
        
        assert len(filtered) == 2
        assert '' not in filtered

class TestGenerateRequirements:
    """Tests for generate_requirements function."""
    
    @patch('generate_requirements.get_installed_packages')
    def test_creates_file_with_packages(self, mock_get_packages, tmp_path):
        """Test that requirements file is created with packages."""
        mock_get_packages.return_value = [
            'numpy==1.24.0',
            'pandas==2.0.0'
        ]
        
        output_path = tmp_path / 'requirements.txt'
        result_path = generate_requirements(str(output_path), include_all=True)
        
        assert result_path == output_path
        assert output_path.exists()
        
        content = output_path.read_text()
        assert 'numpy==1.24.0' in content
        assert 'pandas==2.0.0' in content
        assert 'Auto-generated' in content
    
    @patch('generate_requirements.get_installed_packages')
    def test_excludes_packages(self, mock_get_packages, tmp_path):
        """Test that excluded packages are not in output."""
        mock_get_packages.return_value = [
            'numpy==1.24.0',
            'pytest==7.0.0',
            'pandas==2.0.0'
        ]
        
        output_path = tmp_path / 'requirements.txt'
        generate_requirements(str(output_path), exclude_patterns=['pytest'], include_all=False)
        
        content = output_path.read_text()
        assert 'numpy==1.24.0' in content
        assert 'pandas==2.0.0' in content
        assert 'pytest==7.0.0' not in content
    
    @patch('generate_requirements.get_installed_packages')
    def test_creates_parent_directories(self, mock_get_packages, tmp_path):
        """Test that parent directories are created if they don't exist."""
        mock_get_packages.return_value = ['numpy==1.24.0']
        
        nested_path = tmp_path / 'nested' / 'dir' / 'requirements.txt'
        result_path = generate_requirements(str(nested_path), include_all=True)
        
        assert result_path == nested_path
        assert nested_path.exists()
    
    @patch('generate_requirements.get_installed_packages')
    def test_sorts_packages(self, mock_get_packages, tmp_path):
        """Test that packages are sorted alphabetically."""
        mock_get_packages.return_value = [
            'zlib==1.0.0',
            'numpy==1.24.0',
            'alpha==1.0.0'
        ]
        
        output_path = tmp_path / 'requirements.txt'
        generate_requirements(str(output_path), include_all=True)
        
        content = output_path.read_text()
        lines = [line for line in content.split('\n') if line and not line.startswith('#')]
        
        # Check that packages are sorted
        package_lines = [line for line in lines if '==' in line]
        assert package_lines == sorted(package_lines)