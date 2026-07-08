"""
Tests for the ingest module.

These tests verify the core logic of the ingest module without
requiring actual Defects4J installation.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import (
    list_available_projects,
    get_project_size,
    select_dynamic_subset,
    download_defects4j_subset,
    validate_ram_limit,
    DEFECTS4J_SIZE_LIMIT_GB
)


class TestListAvailableProjects:
    def test_list_available_projects_success(self):
        """Test successful listing of projects."""
        with patch('src.ingest.run_defects4j_command') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Lang (50 bugs)\nChart (25 bugs)\nClosure (10 bugs)"
            )
            
            projects = list_available_projects()
            
            assert len(projects) == 3
            assert "Lang" in projects
            assert "Chart" in projects
            assert "Closure" in projects

    def test_list_available_projects_empty(self):
        """Test handling of empty project list."""
        with patch('src.ingest.run_defects4j_command') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=""
            )
            
            projects = list_available_projects()
            
            assert len(projects) == 0

    def test_list_available_projects_failure(self):
        """Test handling of command failure."""
        with patch('src.ingest.run_defects4j_command') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Command failed"
            )
            
            with pytest.raises(RuntimeError, match="Failed to list projects"):
                list_available_projects()


class TestSelectDynamicSubset:
    def test_select_subset_within_limit(self):
        """Test selection when all projects fit within limit."""
        projects = ["Lang", "Chart", "Closure"]
        
        with patch('src.ingest.get_project_size') as mock_size:
            mock_size.side_effect = [100, 200, 300]  # Small sizes
            with patch('src.ingest.validate_ram_limit') as mock_ram:
                mock_ram.return_value = True
                
                selected = select_dynamic_subset(projects, Path("/tmp"))
                
                assert len(selected) == 3
                assert selected == projects

    def test_select_subset_exceeds_limit(self):
        """Test selection stops when limit is reached."""
        projects = ["Lang", "Chart", "Closure", "Time"]
        
        with patch('src.ingest.get_project_size') as mock_size:
            # First two fit, third would exceed
            mock_size.side_effect = [100, 200, 1000000000, 50]
            with patch('src.ingest.validate_ram_limit') as mock_ram:
                mock_ram.return_value = True
                
                selected = select_dynamic_subset(projects, Path("/tmp"))
                
                # Should only select first two
                assert len(selected) == 2
                assert selected == ["Lang", "Chart"]

    def test_select_subset_ram_limit_reached(self):
        """Test selection stops when RAM limit is reached."""
        projects = ["Lang", "Chart"]
        
        with patch('src.ingest.get_project_size') as mock_size:
            mock_size.side_effect = [100, 200]
            with patch('src.ingest.validate_ram_limit') as mock_ram:
                # First check passes, second fails
                mock_ram.side_effect = [True, False]
                
                selected = select_dynamic_subset(projects, Path("/tmp"))
                
                assert len(selected) == 1
                assert selected == ["Lang"]


class TestValidateRamLimit:
    @patch('src.ingest.get_memory_limit_bytes')
    @patch('src.ingest.get_current_memory_usage_bytes')
    def test_validate_ram_limit_success(self, mock_usage, mock_limit):
        """Test successful RAM validation."""
        mock_limit.return_value = 8 * 1024**3  # 8GB limit
        mock_usage.return_value = 2 * 1024**3  # 2GB usage
        
        assert validate_ram_limit(Path("/tmp")) is True

    @patch('src.ingest.get_memory_limit_bytes')
    @patch('src.ingest.get_current_memory_usage_bytes')
    def test_validate_ram_limit_failure(self, mock_usage, mock_limit):
        """Test failed RAM validation."""
        mock_limit.return_value = 4 * 1024**3  # 4GB limit
        mock_usage.return_value = 3.5 * 1024**3  # 3.5GB usage (90%)
        
        assert validate_ram_limit(Path("/tmp")) is False

class TestDownloadDefects4jSubset:
    def test_download_subset_success(self):
        """Test successful download of subset."""
        with patch('src.ingest.get_defects4j_path') as mock_path:
            mock_path.return_value = Path("/fake/defects4j")
            with patch('src.ingest.validate_defects4j_path') as mock_validate:
                mock_validate.return_value = True
                with patch('src.ingest.list_available_projects') as mock_list:
                    mock_list.return_value = ["Lang", "Chart"]
                    with patch('src.ingest.select_dynamic_subset') as mock_select:
                        mock_select.return_value = ["Lang"]
                        with patch('src.ingest.run_defects4j_command') as mock_run:
                            mock_run.return_value = MagicMock(returncode=0)
                            with patch('src.ingest.Path.mkdir'):
                                with patch('src.ingest.Path.rglob') as mock_rglob:
                                    mock_file = MagicMock()
                                    mock_file.is_file.return_value = True
                                    mock_file.stat.return_value.st_size = 100
                                    mock_rglob.return_value = [mock_file]
                                    
                                    stats = download_defects4j_subset(
                                        Path("/tmp/output"),
                                        max_projects=1
                                    )
                                    
                                    assert stats['total_projects'] == 1
                                    assert stats['total_size_bytes'] == 100
                                    assert len(stats['projects']) == 1

    def test_download_subset_no_projects(self):
        """Test handling of no available projects."""
        with patch('src.ingest.get_defects4j_path') as mock_path:
            mock_path.return_value = Path("/fake/defects4j")
            with patch('src.ingest.validate_defects4j_path') as mock_validate:
                mock_validate.return_value = True
                with patch('src.ingest.list_available_projects') as mock_list:
                    mock_list.return_value = []
                    
                    with pytest.raises(RuntimeError, match="No projects available"):
                        download_defects4j_subset(Path("/tmp/output"))

    def test_download_subset_exceeds_size_limit(self):
        """Test handling of size limit exceeded."""
        with patch('src.ingest.get_defects4j_path') as mock_path:
            mock_path.return_value = Path("/fake/defects4j")
            with patch('src.ingest.validate_defects4j_path') as mock_validate:
                mock_validate.return_value = True
                with patch('src.ingest.list_available_projects') as mock_list:
                    mock_list.return_value = ["Lang"]
                    with patch('src.ingest.select_dynamic_subset') as mock_select:
                        mock_select.return_value = ["Lang"]
                        with patch('src.ingest.run_defects4j_command') as mock_run:
                            mock_run.return_value = MagicMock(returncode=0)
                            with patch('src.ingest.Path.mkdir'):
                                with patch('src.ingest.Path.rglob') as mock_rglob:
                                    # Return a huge file to exceed limit
                                    mock_file = MagicMock()
                                    mock_file.is_file.return_value = True
                                    mock_file.stat.return_value.st_size = 10**10  # 10GB
                                    mock_rglob.return_value = [mock_file]
                                    
                                    with pytest.raises(RuntimeError, match="exceeds.*limit"):
                                        download_defects4j_subset(Path("/tmp/output"))