"""
Unit tests for the reproducibility archive module (T049).
"""
import os
import sys
import tempfile
import shutil
import tarfile
from pathlib import Path
import pytest

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.archive_reproducibility import (
    collect_paths_to_archive,
    create_archive,
    setup_logger
)

@pytest.fixture
def temp_project_structure():
    """Create a temporary directory structure mimicking the project."""
    temp_dir = tempfile.mkdtemp()
    base_path = Path(temp_dir)
    
    # Create required directories and files
    (base_path / "data" / "raw").mkdir(parents=True)
    (base_path / "results" / "logs").mkdir(parents=True)
    (base_path / "results" / "analysis").mkdir(parents=True)
    
    # Create dummy files
    (base_path / "requirements.txt").write_text("numpy\nshapely")
    (base_path / "data" / "raw" / "dataset.json").write_text('{"test": true}')
    (base_path / "results" / "logs" / "execution.log").write_text("log content")
    (base_path / "results" / "analysis" / "report.md").write_text("report content")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_collect_paths_to_archive(temp_project_structure):
    """Test that collect_paths_to_archive finds all required files."""
    base_dir = temp_project_structure
    paths = collect_paths_to_archive(base_dir)
    
    path_names = [p.name for p in paths]
    
    assert "requirements.txt" in path_names
    assert "dataset.json" in path_names
    assert "execution.log" in path_names
    assert "report.md" in path_names

def test_create_archive(temp_project_structure):
    """Test that create_archive produces a valid tarball."""
    base_dir = temp_project_structure
    output_dir = os.path.join(temp_project_structure, "output")
    timestamp = "test_123"
    
    paths = collect_paths_to_archive(base_dir)
    archive_path = create_archive(base_dir, output_dir, timestamp, paths)
    
    assert os.path.exists(archive_path)
    assert archive_path.endswith(".tar.gz")
    
    # Verify contents
    with tarfile.open(archive_path, "r:gz") as tar:
        names = tar.getnames()
        assert any("requirements.txt" in n for n in names)
        assert any("dataset.json" in n for n in names)
        assert any("execution.log" in n for n in names)
        assert any("report.md" in n for n in names)

def test_missing_directory_handling(temp_project_structure):
    """Test that missing directories do not crash the collector."""
    # Remove one of the directories
    shutil.rmtree(os.path.join(temp_project_structure, "results", "logs"))
    
    paths = collect_paths_to_archive(temp_project_structure)
    
    # Should still find other files
    path_names = [p.name for p in paths]
    assert "requirements.txt" in path_names
    assert "dataset.json" in path_names
    # execution.log should be missing
    assert "execution.log" not in path_names