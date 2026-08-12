import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.labeling import detect_class_imbalance, label_all_bugs

@pytest.fixture
def mock_defects4j_setup():
    """Mock the defects4j CLI calls to avoid dependency on real environment in unit tests."""
    with patch('src.labeling.get_defects4j_path', return_value='/mock/defects4j'):
        with patch('subprocess.run') as mock_run:
            # Mock successful commit retrieval
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "abc123def456"
            mock_run.return_value = mock_result
            yield mock_run

@pytest.fixture
def sample_project_list():
    return ["Lang", "Time", "Math"]

@pytest.fixture
def sample_java_files_map():
    return [
        "src/main/java/com/example/Lang.java",
        "src/main/java/com/example/Util.java",
        "src/test/java/com/example/LangTest.java"
    ]

class TestDetectClassImbalance:
    def test_detects_zero_buggy(self):
        """Test that a project with 0 buggy files is detected as imbalanced."""
        labels = {
            "file1.java": False,
            "file2.java": False,
            "file3.java": False
        }
        is_imbalanced, n_buggy, n_clean = detect_class_imbalance(labels)
        
        assert is_imbalanced is True
        assert n_buggy == 0
        assert n_clean == 3

    def test_detects_balanced(self):
        """Test that a project with at least one buggy file is NOT flagged as imbalanced."""
        labels = {
            "file1.java": True,
            "file2.java": False,
            "file3.java": False
        }
        is_imbalanced, n_buggy, n_clean = detect_class_imbalance(labels)
        
        assert is_imbalanced is False
        assert n_buggy == 1
        assert n_clean == 2

    def test_detects_all_buggy(self):
        """Test that a project with all buggy files is NOT flagged as imbalanced (edge case)."""
        labels = {
            "file1.java": True,
            "file2.java": True
        }
        is_imbalanced, n_buggy, n_clean = detect_class_imbalance(labels)
        
        assert is_imbalanced is False
        assert n_buggy == 2
        assert n_clean == 0

class TestLabelAllBugs:
    @patch('src.labeling.get_bug_introduction_commit')
    @patch('src.labeling.get_files_changed_in_commit')
    def test_label_all_bugs_with_imbalance(self, mock_get_files, mock_get_commit, sample_java_files_map):
        """Test labeling logic when the result is zero buggy files."""
        mock_get_commit.return_value = "commit123"
        mock_get_files.return_value = set() # No files changed -> 0 buggy files
        
        labels, has_imbalance = label_all_bugs("Lang", ["1", "2"], sample_java_files_map)
        
        assert all(v == False for v in labels.values())
        assert has_imbalance is True

    @patch('src.labeling.get_bug_introduction_commit')
    @patch('src.labeling.get_files_changed_in_commit')
    def test_label_all_bugs_with_buggy_files(self, mock_get_files, mock_get_commit, sample_java_files_map):
        """Test labeling logic when at least one file is buggy."""
        mock_get_commit.return_value = "commit123"
        mock_get_files.return_value = {"src/main/java/com/example/Lang.java"}
        
        labels, has_imbalance = label_all_bugs("Lang", ["1"], sample_java_files_map)
        
        assert labels["src/main/java/com/example/Lang.java"] is True
        assert labels["src/main/java/com/example/Util.java"] is False
        assert has_imbalance is False