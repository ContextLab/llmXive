import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from src.labeling import (
    get_defects4j_file_changes,
    load_bug_introduction_commits,
    map_files_to_bugs,
    label_project_files,
    LabelingError
)

@pytest.fixture
def mock_defects4j_setup(tmp_path):
    """Setup mock Defects4J environment."""
    d4j_data = tmp_path / "d4j_data"
    d4j_data.mkdir()
    bugs_json = d4j_data / "bugs.json"
    
    # Create a mock bugs.json
    mock_bugs = {
        "Lang_1": {"commit": "abc123def456"},
        "Lang_2": {"commit": "xyz789uvw012"}
    }
    with open(bugs_json, 'w') as f:
        json.dump(mock_bugs, f)
        
    return {
        "d4j_data": d4j_data,
        "bugs_json": bugs_json,
        "project_id": "Lang"
    }

@pytest.fixture
def sample_project_list():
    return ["src/main/java/org/example/ClassA.java", "src/main/java/org/example/ClassB.java", "src/test/java/ClassC.java"]

@pytest.fixture
def sample_java_files_map():
    # Map files to bug status
    return {
        "src/main/java/org/example/ClassA.java": True,
        "src/main/java/org/example/ClassB.java": False,
        "src/test/java/ClassC.java": False
    }

def test_load_bug_introduction_commits_valid(mock_defects4j_setup):
    result = load_bug_introduction_commits(mock_defects4j_setup["bugs_json"])
    assert "Lang_1" in result
    assert result["Lang_1"] == "abc123def456"
    assert len(result) == 2

def test_load_bug_introduction_commits_missing_file(tmp_path):
    non_existent = tmp_path / "nope.json"
    with pytest.raises(LabelingError):
        load_bug_introduction_commits(non_existent)

@patch('subprocess.run')
def test_get_defects4j_file_changes_success(mock_run, mock_defects4j_setup):
    # Mock subprocess output
    mock_run.return_value = MagicMock(
        stdout="src/main/java/org/example/ClassA.java\nsrc/main/java/Other.java",
        stderr="",
        returncode=0
    )
    
    files = get_defects4j_file_changes("Lang", "abc123def456")
    
    assert "src/main/java/org/example/ClassA.java" in files
    assert "src/main/java/Other.java" in files
    assert len(files) == 2
    mock_run.assert_called_once()

@patch('subprocess.run')
def test_get_defects4j_file_changes_failure(mock_run, mock_defects4j_setup):
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error")
    
    with pytest.raises(LabelingError):
        get_defects4j_file_changes("Lang", "abc123def456")

def test_map_files_to_bugs(mock_defects4j_setup, sample_project_list):
    # Mock the query function to return specific files for specific commits
    def mock_query(proj, commit):
        if commit == "abc123def456":
            return {"src/main/java/org/example/ClassA.java", "src/main/java/Other.java"}
        elif commit == "xyz789uvw012":
            return {"src/main/java/Unrelated.java"}
        return set()

    with patch('src.labeling.get_defects4j_file_changes', side_effect=mock_query):
        result = map_files_to_bugs(sample_project_list, "Lang", mock_defects4j_setup["bugs_json"])
        
        assert result["src/main/java/org/example/ClassA.java"] is True
        assert result["src/main/java/org/example/ClassB.java"] is False
        assert result["src/test/java/ClassC.java"] is False

def test_label_project_files_integration(mock_defects4j_setup, sample_project_list):
    # Create a temp file list
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        for line in sample_project_list:
            f.write(line + "\n")
        file_list_path = Path(f.name)
    
    output_path = mock_defects4j_setup["d4j_data"] / "labels.json"
    
    # Mock the query to return ClassA as buggy
    def mock_query(proj, commit):
        if commit == "abc123def456":
            return {"src/main/java/org/example/ClassA.java"}
        return set()

    try:
        with patch('src.labeling.get_defects4j_file_changes', side_effect=mock_query):
            result = label_project_files(
                project_id="Lang",
                project_root=Path("/fake"),
                file_list_path=file_list_path,
                output_path=output_path
            )
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved = json.load(f)
            
            assert saved["src/main/java/org/example/ClassA.java"] is True
            assert saved["src/main/java/org/example/ClassB.java"] is False
    finally:
        os.unlink(file_list_path)