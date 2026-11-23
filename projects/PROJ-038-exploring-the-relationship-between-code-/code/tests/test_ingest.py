import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import sys
import os
from src.ingest import (
    DataFetchError,
    get_defects4j_path,
    run_defects4j_command,
    list_available_projects,
    get_project_size,
    get_current_memory_usage_bytes,
    validate_ram_limit,
    is_generated_or_non_java,
    filter_java_files,
    select_dynamic_subset,
    download_defects4j_subset
)

class TestListAvailableProjects:
    @patch('src.ingest.run_defects4j_command')
    def test_list_projects_success(self, mock_run_cmd):
        """Test successful listing of projects."""
        mock_run_cmd.return_value = (
            "Closure 1.0\nLang 2.0\nMath 3.0\n",
            "",
            0
        )
        
        projects = list_available_projects()
        
        assert len(projects) >= 3
        assert 'Closure' in projects
        assert 'Lang' in projects
        assert 'Math' in projects
    
    @patch('src.ingest.run_defects4j_command')
    def test_list_projects_failure(self, mock_run_cmd):
        """Test failure when Defects4J command fails."""
        mock_run_cmd.return_value = ("", "Error: command failed", 1)
        
        with pytest.raises(DataFetchError):
            list_available_projects()

class TestSelectDynamicSubset:
    def test_select_subset_basic(self):
        """Test basic subset selection."""
        projects = ['Closure', 'Lang', 'Math', 'Time', 'Codec']
        
        selected = select_dynamic_subset(projects, target_files=500)
        
        # Should select at least one project
        assert len(selected) > 0
        # Should be in alphabetical order
        assert selected == sorted(selected)
    
    def test_select_subset_limit(self):
        """Test subset selection with file limit."""
        projects = ['Closure', 'Lang', 'Math', 'Time', 'Codec']
        
        # Set a very low target to force early stopping
        selected = select_dynamic_subset(projects, target_files=100)
        
        # Should select only a few projects
        assert len(selected) <= 3

class TestValidateRamLimit:
    @patch('src.ingest.get_memory_limit_bytes')
    def test_validate_within_limit(self, mock_get_limit):
        """Test validation when within limit."""
        mock_get_limit.return_value = 7 * 1024 * 1024 * 1024  # 7GB
        
        result = validate_ram_limit(5 * 1024 * 1024 * 1024)  # 5GB
        
        assert result is True
    
    @patch('src.ingest.get_memory_limit_bytes')
    def test_validate_exceeds_limit(self, mock_get_limit):
        """Test validation when exceeding limit."""
        mock_get_limit.return_value = 7 * 1024 * 1024 * 1024  # 7GB
        
        result = validate_ram_limit(6.5 * 1024 * 1024 * 1024)  # 6.5GB (85% threshold)
        
        assert result is False

class TestDownloadDefects4jSubset:
    @patch('src.ingest.run_defects4j_command')
    @patch('src.ingest.filter_java_files')
    def test_download_success(self, mock_filter, mock_run_cmd):
        """Test successful download of projects."""
        mock_run_cmd.return_value = ("Checkout successful", "", 0)
        mock_filter.return_value = [Path('/tmp/test.java')]
        
        with patch('src.ingest.Path.exists', return_value=False):
            with patch('src.ingest.Path.mkdir'):
                stats = download_defects4j_subset(
                    ['Closure'],
                    Path('/tmp/output')
                )
        
        assert stats['projects_downloaded'] == 1
        assert stats['total_files'] >= 1
    
    @patch('src.ingest.run_defects4j_command')
    def test_download_failure(self, mock_run_cmd):
        """Test handling of download failure."""
        mock_run_cmd.return_value = ("", "Checkout failed", 1)
        
        with patch('src.ingest.Path.exists', return_value=False):
            with patch('src.ingest.Path.mkdir'):
                stats = download_defects4j_subset(
                    ['Closure'],
                    Path('/tmp/output')
                )
        
        assert stats['projects_downloaded'] == 0
        assert len(stats['failed_projects']) == 1