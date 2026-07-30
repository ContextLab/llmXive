"""
Integration tests for the code/analyze.py module.

Tests the full pipeline of running Bandit and aggregating results.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

from code.analyze import (
    find_python_files,
    run_bandit_scan,
    parse_bandit_report,
    extract_task_id_and_source_type,
    count_lines_of_code,
    aggregate_vulnerability_counts,
    main
)
from code.config import get_config, get_paths, ensure_directories


class TestFindPythonFiles:
    """Tests for find_python_files function."""
    
    def test_find_python_files_in_temp_dir(self, tmp_path):
        """Test finding Python files in a temporary directory."""
        # Create some test files
        (tmp_path / "test1.py").write_text("print('hello')")
        (tmp_path / "test2.py").write_text("print('world')")
        (tmp_path / "readme.txt").write_text("not a python file")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.pyc").write_text("cache")
        
        files = find_python_files(tmp_path)
        
        assert len(files) == 2
        assert all(f.suffix == ".py" for f in files)
        assert not any("__pycache__" in str(f) for f in files)
    
    def test_find_python_files_empty_dir(self, tmp_path):
        """Test finding Python files in an empty directory."""
        files = find_python_files(tmp_path)
        assert len(files) == 0
    
    def test_find_python_files_nonexistent_dir(self):
        """Test finding Python files in a nonexistent directory."""
        files = find_python_files(Path("/nonexistent/path"))
        assert len(files) == 0


class TestExtractTaskIdAndSourceType:
    """Tests for extract_task_id_and_source_type function."""
    
    def test_extract_from_generated_path(self):
        """Test extraction from generated code path."""
        file_path = Path("data/generated/starcoder/humaneval/HumanEval_0/samples/sample_1.py")
        base_dirs = {"generated": Path("data/generated")}
        
        task_id, source_type = extract_task_id_and_source_type(file_path, base_dirs)
        
        assert task_id == "HumanEval_0"
        assert source_type == "generated_starcoder"
    
    def test_extract_from_human_path(self):
        """Test extraction from human code path."""
        file_path = Path("data/human/humaneval/HumanEval_0/sample_1.py")
        base_dirs = {"human": Path("data/human")}
        
        task_id, source_type = extract_task_id_and_source_type(file_path, base_dirs)
        
        assert task_id == "HumanEval_0"
        assert source_type == "human"
    
    def test_extract_with_invalid_path(self):
        """Test extraction from an invalid path."""
        file_path = Path("some/random/path/file.py")
        base_dirs = {"generated": Path("data/generated")}
        
        task_id, source_type = extract_task_id_and_source_type(file_path, base_dirs)
        
        assert task_id is None
        assert source_type is None


class TestCountLinesOfCode:
    """Tests for count_lines_of_code function."""
    
    def test_count_loc_simple(self, tmp_path):
        """Test counting lines of code in a simple file."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
        def hello():
            print("Hello")
        
        # This is a comment
        x = 1
        """)
        
        loc = count_lines_of_code(file_path)
        assert loc == 3  # def, print, x = 1
    
    def test_count_loc_empty_lines(self, tmp_path):
        """Test that empty lines are not counted."""
        file_path = tmp_path / "test.py"
        file_path.write_text("""
        
        def hello():
        
            print("Hello")
        
        """)
        
        loc = count_lines_of_code(file_path)
        assert loc == 2  # def, print


class TestAggregateVulnerabilityCounts:
    """Tests for aggregate_vulnerability_counts function."""
    
    def test_aggregate_single_file(self):
        """Test aggregation for a single file with multiple vulnerabilities."""
        report_items = [
            {
                "filename": "data/generated/starcoder/humaneval/HumanEval_0/samples/sample_1.py",
                "issue_text": "Vulnerability 1",
                "cwe": "CWE-78"
            },
            {
                "filename": "data/generated/starcoder/humaneval/HumanEval_0/samples/sample_1.py",
                "issue_text": "Vulnerability 2",
                "cwe": "CWE-89"
            }
        ]
        
        base_dirs = {"generated": Path("data/generated")}
        df = aggregate_vulnerability_counts(report_items, base_dirs)
        
        assert len(df) == 1
        assert df.iloc[0]["task_id"] == "HumanEval_0"
        assert df.iloc[0]["source_type"] == "generated_starcoder"
        assert df.iloc[0]["vulnerability_count"] == 2


class TestMain:
    """Tests for the main function."""
    
    @patch("code.analyze.run_bandit_scan")
    @patch("code.analyze.parse_bandit_report")
    @patch("code.analyze.find_python_files")
    def test_main_with_files(self, mock_find, mock_parse, mock_run, tmp_path, monkeypatch):
        """Test main function with simulated files and bandit output."""
        # Setup mock data
        mock_find.return_value = [tmp_path / "test.py"]
        mock_parse.return_value = [
            {
                "filename": str(tmp_path / "test.py"),
                "issue_text": "Test vulnerability",
                "cwe": "CWE-123"
            }
        ]
        mock_run.return_value = True
        
        # Create a temporary directory structure
        test_dir = tmp_path / "data"
        generated_dir = test_dir / "generated" / "starcoder" / "humaneval" / "HumanEval_0" / "samples"
        generated_dir.mkdir(parents=True)
        
        (generated_dir / "sample_1.py").write_text("print('hello')")
        
        # Mock paths
        with patch("code.analyze.get_paths") as mock_paths, \
             patch("code.analyze.get_config") as mock_config, \
             patch("code.analyze.ensure_directories"):
            
            mock_paths.return_value = {
                "generated": generated_dir,
                "human": tmp_path / "data" / "human",
                "processed": tmp_path / "data" / "processed",
                "raw_reports": tmp_path / "data" / "processed" / "raw_vulnerability_reports.json",
                "raw_counts": tmp_path / "data" / "processed" / "raw_vulnerability_counts.csv",
                "bandit_config": tmp_path / "code" / "config" / "bandit_config.yaml"
            }
            
            # Create bandit config file
            mock_paths.return_value["bandit_config"].parent.mkdir(parents=True, exist_ok=True)
            mock_paths.return_value["bandit_config"].write_text("exclude_dirs: []")
            
            # Run main
            main()
            
            # Verify outputs were created
            assert mock_paths.return_value["raw_reports"].exists()
            assert mock_paths.return_value["raw_counts"].exists()
            
            # Verify CSV has correct columns
            df = pd.read_csv(mock_paths.return_value["raw_counts"])
            assert list(df.columns) == ["task_id", "source_type", "file_path", "lines_of_code", "vulnerability_count"]
    
    @patch("code.analyze.find_python_files")
    def test_main_no_files(self, mock_find, tmp_path, monkeypatch):
        """Test main function when no files are found."""
        mock_find.return_value = []
        
        with patch("code.analyze.get_paths") as mock_paths, \
             patch("code.analyze.get_config"), \
             patch("code.analyze.ensure_directories"):
            
            mock_paths.return_value = {
                "generated": tmp_path / "data" / "generated",
                "human": tmp_path / "data" / "human",
                "processed": tmp_path / "data" / "processed",
                "raw_reports": tmp_path / "data" / "processed" / "raw_vulnerability_reports.json",
                "raw_counts": tmp_path / "data" / "processed" / "raw_vulnerability_counts.csv",
                "bandit_config": tmp_path / "code" / "config" / "bandit_config.yaml"
            }
            
            main()
            
            # Verify empty outputs were created
            assert mock_paths.return_value["raw_reports"].exists()
            assert mock_paths.return_value["raw_counts"].exists()