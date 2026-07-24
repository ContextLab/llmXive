"""
Tests for the labeling module.

These tests verify the logic for mapping Defects4J bug-introduction commits
to file-level binary labels.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.labeling import (
    get_bug_introduction_commit,
    get_files_changed_in_commit,
    label_files_for_bug,
    label_all_bugs
)


class TestGetBugIntroductionCommit:
    """Tests for get_bug_introduction_commit function."""

    @patch('src.labeling.run_defects4j_command')
    @patch('src.labeling.validate_defects4j_path')
    def test_returns_commit_hash(self, mock_validate, mock_run):
        """Test that the function returns a valid commit hash."""
        mock_run.return_value = "a1b2c3d4e5f6\n"
        
        result = get_bug_introduction_commit("lang", "1")
        
        assert result == "a1b2c3d4e5f6"
        mock_validate.assert_called_once()
        mock_run.assert_called_once()

    @patch('src.labeling.run_defects4j_command')
    @patch('src.labeling.validate_defects4j_path')
    def test_raises_on_empty_commit(self, mock_validate, mock_run):
        """Test that the function raises on empty commit hash."""
        mock_run.return_value = "\n"
        
        with pytest.raises(RuntimeError, match="Empty commit hash"):
            get_bug_introduction_commit("lang", "1")

    @patch('src.labeling.run_defects4j_command')
    @patch('src.labeling.validate_defects4j_path')
    def test_raises_on_failure(self, mock_validate, mock_run):
        """Test that the function raises on command failure."""
        mock_run.side_effect = Exception("Command failed")
        
        with pytest.raises(RuntimeError, match="Failed to get bug-introduction commit"):
            get_bug_introduction_commit("lang", "1")


class TestGetFilesChangedInCommit:
    """Tests for get_files_changed_in_commit function."""

    def test_repo_not_found(self):
        """Test that the function raises when repo doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Repository not found"):
            get_files_changed_in_commit(Path("/nonexistent/repo"), "abc123")

    @patch('subprocess.run')
    def test_returns_changed_files(self, mock_run):
        """Test that the function returns a set of changed files."""
        mock_run.return_value = MagicMock(
            stdout="src/main/java/Example.java\nsrc/test/java/ExampleTest.java\n",
            stderr=""
        )
        
        repo_path = Path("/tmp/test_repo")
        with patch.object(repo_path, 'exists', return_value=True):
            files = get_files_changed_in_commit(repo_path, "abc123")
        
        assert files == {"src/main/java/Example.java", "src/test/java/ExampleTest.java"}
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_raises_on_git_error(self, mock_run):
        """Test that the function raises on git command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git", stderr="Error")
        
        repo_path = Path("/tmp/test_repo")
        with patch.object(repo_path, 'exists', return_value=True):
            with pytest.raises(RuntimeError, match="Failed to get files changed"):
                get_files_changed_in_commit(repo_path, "abc123")


class TestLabelFilesForBug:
    """Tests for label_files_for_bug function."""

    @patch('src.labeling.get_bug_introduction_commit')
    @patch('src.labeling.get_files_changed_in_commit')
    def test_labels_changed_files_as_buggy(self, mock_get_files, mock_get_commit):
        """Test that changed files are labeled as buggy (1)."""
        mock_get_commit.return_value = "abc123"
        mock_get_files.return_value = {"src/main/java/Buggy.java"}
        
        repo_path = Path("/tmp/repo")
        all_files = [
            "src/main/java/Buggy.java",
            "src/main/java/Other.java",
            "src/test/java/BuggyTest.java"
        ]
        
        labels = label_files_for_bug(repo_path, "lang", "1", all_files)
        
        assert labels["src/main/java/Buggy.java"] == 1
        assert labels["src/main/java/Other.java"] == 0
        assert labels["src/test/java/BuggyTest.java"] == 0

    @patch('src.labeling.get_bug_introduction_commit')
    @patch('src.labeling.get_files_changed_in_commit')
    def test_handles_empty_change_set(self, mock_get_files, mock_get_commit):
        """Test that empty change set results in all non-buggy labels."""
        mock_get_commit.return_value = "abc123"
        mock_get_files.return_value = set()
        
        repo_path = Path("/tmp/repo")
        all_files = ["src/main/java/File.java"]
        
        labels = label_files_for_bug(repo_path, "lang", "1", all_files)
        
        assert labels["src/main/java/File.java"] == 0


class TestLabelAllBugs:
    """Tests for label_all_bugs function."""

    def test_skips_missing_project(self):
        """Test that missing projects are skipped with a warning."""
        project_list = [{"project": "missing", "bugs": [{"bug_id": "1"}]}]
        java_files_map = {"other": ["file.java"]}
        
        with patch('builtins.print') as mock_print:
            result = label_all_bugs(Path("/tmp/d4j"), project_list, java_files_map)
        
        assert result == []
        mock_print.assert_called_once()

    def test_labels_multiple_bugs(self):
        """Test labeling across multiple bugs."""
        project_list = [
            {
                "project": "lang",
                "bugs": [
                    {"bug_id": "1"},
                    {"bug_id": "2"}
                ]
            }
        ]
        java_files_map = {"lang": ["file1.java", "file2.java"]}
        
        # Mock the repository existence and labeling
        with patch('pathlib.Path.exists', return_value=True):
            with patch('src.labeling.label_files_for_bug') as mock_label:
                mock_label.side_effect = [
                    {"file1.java": 1, "file2.java": 0},
                    {"file1.java": 0, "file2.java": 1}
                ]
                
                result = label_all_bugs(Path("/tmp/d4j"), project_list, java_files_map)
        
        assert len(result) == 4
        assert any(r['bug_id'] == '1' and r['is_buggy'] == 1 for r in result)
        assert any(r['bug_id'] == '2' and r['is_buggy'] == 1 for r in result)


@pytest.fixture
def mock_defects4j_setup():
    """Fixture to set up mock Defects4J environment."""
    with patch('src.labeling.get_defects4j_path') as mock_path:
        mock_path.return_value = Path("/tmp/mock_d4j")
        yield mock_path


@pytest.fixture
def sample_project_list():
    """Sample project list for testing."""
    return [
        {
            "project": "lang",
            "bugs": [
                {"bug_id": "1"},
                {"bug_id": "2"}
            ]
        },
        {
            "project": "math",
            "bugs": [
                {"bug_id": "1"}
            ]
        }
    ]


@pytest.fixture
def sample_java_files_map():
    """Sample Java files map for testing."""
    return {
        "lang": [
            "src/main/java/org/apache/lang/Example.java",
            "src/main/java/org/apache/lang/Other.java"
        ],
        "math": [
            "src/main/java/org/apache/math/Calculator.java"
        ]
    }