import os
import tempfile
import pytest
from pathlib import Path

from viz.validator import (
    count_generated_visualizations,
    validate_visualization_count,
    REQUIRED_VISUALIZATION_FILES
)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_count_generated_visualizations_empty_dir(temp_output_dir):
    """Test counting when no files exist."""
    count, found, missing = count_generated_visualizations(temp_output_dir)
    assert count == 0
    assert found == []
    assert len(missing) == len(REQUIRED_VISUALIZATION_FILES)
    assert set(missing) == set(REQUIRED_VISUALIZATION_FILES)

def test_count_generated_visualizations_partial_files(temp_output_dir):
    """Test counting when some files exist."""
    # Create only the scatter plot
    scatter_path = os.path.join(temp_output_dir, "scatter_plot.png")
    Path(scatter_path).touch()

    count, found, missing = count_generated_visualizations(temp_output_dir)
    assert count == 1
    assert "scatter_plot.png" in found
    assert "residuals.png" in missing

def test_count_generated_visualizations_all_files(temp_output_dir):
    """Test counting when all required files exist."""
    # Create all required files
    for filename in REQUIRED_VISUALIZATION_FILES:
        file_path = os.path.join(temp_output_dir, filename)
        Path(file_path).touch()

    count, found, missing = count_generated_visualizations(temp_output_dir)
    assert count == len(REQUIRED_VISUALIZATION_FILES)
    assert len(found) == len(REQUIRED_VISUALIZATION_FILES)
    assert missing == []

def test_validate_visualization_count_pass(temp_output_dir):
    """Test validation passes when all files exist."""
    for filename in REQUIRED_VISUALIZATION_FILES:
        file_path = os.path.join(temp_output_dir, filename)
        Path(file_path).touch()

    result = validate_visualization_count(temp_output_dir)
    assert result is True

def test_validate_visualization_count_fail(temp_output_dir):
    """Test validation fails when files are missing."""
    # Create only one file
    file_path = os.path.join(temp_output_dir, "scatter_plot.png")
    Path(file_path).touch()

    with pytest.raises(FileNotFoundError) as excinfo:
        validate_visualization_count(temp_output_dir)
    
    assert "validation failed" in str(excinfo.value).lower()
    assert "scatter_plot.png" in str(excinfo.value) or "residuals.png" in str(excinfo.value)

def test_validate_visualization_count_nonexistent_dir():
    """Test validation fails when directory does not exist."""
    with pytest.raises(FileNotFoundError):
        validate_visualization_count("/nonexistent/path/12345")

def test_validate_visualization_count_custom_min(temp_output_dir):
    """Test validation with custom minimum count."""
    # Create one file
    file_path = os.path.join(temp_output_dir, "scatter_plot.png")
    Path(file_path).touch()

    # Should pass with min_count=1
    result = validate_visualization_count(temp_output_dir, min_count=1)
    assert result is True

    # Should fail with min_count=2
    with pytest.raises(FileNotFoundError):
        validate_visualization_count(temp_output_dir, min_count=2)