import os
import tempfile
import pytest
from pathlib import Path

# Import the module under test
from code.data.extract_metrics import (
    FileMetrics,
    compute_file_hash,
    run_lizard_on_file,
    get_file_list_from_directory,
    extract_metrics_for_directory
)
from code.utils.logging import get_logger

@pytest.fixture
def temp_java_file():
    """Create a temporary Java file with known complexity."""
    content = """
    public class Simple {
        public static void main(String[] args) {
            if (true) {
                System.out.println("Hello");
            } else {
                System.out.println("World");
            }
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
        return f.name

@pytest.fixture
def temp_dir_with_java():
    """Create a temporary directory with a Java file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "Test.java")
        with open(file_path, 'w') as f:
            f.write("public class Test {}")
        yield tmpdir

def test_file_metrics_to_dict():
    """Test that FileMetrics serializes correctly."""
    metrics = FileMetrics(
        file_path="test.java",
        project_id="proj1",
        lines_of_code=10,
        cyclomatic_complexity=2,
        token_count=20,
        nesting_depth=1,
        halstead_volume=5.5,
        n_functions=1
    )
    d = metrics.to_dict()
    assert d["file_path"] == "test.java"
    assert d["cyclomatic_complexity"] == 2
    assert d["parse_error"] is None

def test_compute_file_hash(temp_java_file):
    """Test file hashing functionality."""
    hash1 = compute_file_hash(temp_java_file)
    hash2 = compute_file_hash(temp_java_file)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length

def test_run_lizard_on_file_valid(temp_java_file):
    """Test that lizard runs on a valid file and returns metrics."""
    logger = get_logger("test")
    metrics = run_lizard_on_file(temp_java_file, logger)
    
    assert metrics is not None
    assert metrics.file_path == temp_java_file
    assert metrics.parse_error is None
    assert metrics.lines_of_code >= 0
    assert metrics.cyclomatic_complexity >= 0

def test_run_lizard_on_file_invalid(tmp_path):
    """Test handling of a non-existent or invalid file."""
    logger = get_logger("test")
    invalid_path = str(tmp_path / "nonexistent.java")
    metrics = run_lizard_on_file(invalid_path, logger)
    
    # Should return a metrics object with error populated, not crash
    assert metrics is not None
    assert metrics.parse_error is not None

def test_get_file_list_from_directory(temp_dir_with_java):
    """Test file discovery."""
    files = get_file_list_from_directory(temp_dir_with_java, ".java")
    assert len(files) == 1
    assert files[0].endswith(".java")

def test_extract_metrics_for_directory(temp_dir_with_java, tmp_path):
    """Test end-to-end extraction to CSV."""
    output_path = str(tmp_path / "metrics.csv")
    count = extract_metrics_for_directory(
        input_dir=temp_dir_with_java,
        output_path=output_path,
        extension=".java",
        chunk_size=10,
        seed=42
    )
    
    assert count == 1
    assert os.path.exists(output_path)
    
    # Verify CSV content
    with open(output_path, 'r') as f:
        content = f.read()
        assert "file_path" in content
        assert "cyclomatic_complexity" in content
        assert "Test.java" in content