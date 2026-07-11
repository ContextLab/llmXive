"""
Pytest configuration and fixtures for edge case tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))


@pytest.fixture(scope="session")
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def sample_dataset(temp_data_dir):
    """Create a sample dataset for testing."""
    dataset_dir = temp_data_dir / "sample_dataset"
    dataset_dir.mkdir()
    
    # Create sample CSV
    csv_content = """id,text,image_path,target
    1,hello world,path/to/img1.jpg,0
    2,goodbye world,path/to/img2.jpg,1
    3,testing text,path/to/img3.jpg,0
    """
    (dataset_dir / "data.csv").write_text(csv_content)
    
    # Create metadata
    import json
    metadata = {
        "dataset_id": "sample",
        "task_type": "classification",
        "num_rows": 3,
        "has_text": True,
        "has_image": True
    }
    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)
    
    return dataset_dir


@pytest.fixture(scope="function")
def empty_dataset(temp_data_dir):
    """Create an empty dataset for testing."""
    dataset_dir = temp_data_dir / "empty_dataset"
    dataset_dir.mkdir()
    
    # Create empty CSV
    (dataset_dir / "data.csv").write_text("id,text,image_path,target\n")
    
    # Create metadata
    import json
    metadata = {
        "dataset_id": "empty",
        "task_type": "classification",
        "num_rows": 0,
        "has_text": True,
        "has_image": True
    }
    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)
    
    return dataset_dir


@pytest.fixture(scope="function")
def single_row_dataset(temp_data_dir):
    """Create a single-row dataset for testing."""
    dataset_dir = temp_data_dir / "single_row_dataset"
    dataset_dir.mkdir()
    
    # Create single-row CSV
    csv_content = """id,text,image_path,target
    1,single row text,path/to/img.jpg,1
    """
    (dataset_dir / "data.csv").write_text(csv_content)
    
    # Create metadata
    import json
    metadata = {
        "dataset_id": "single_row",
        "task_type": "classification",
        "num_rows": 1,
        "has_text": True,
        "has_image": True
    }
    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)
    
    return dataset_dir


@pytest.fixture(scope="function")
def zero_variance_dataset(temp_data_dir):
    """Create a dataset with zero-variance features."""
    dataset_dir = temp_data_dir / "zero_variance_dataset"
    dataset_dir.mkdir()
    
    # Create CSV with constant feature
    csv_content = """id,constant_feature,variable_feature,target
    1,5.0,1.0,0
    2,5.0,2.0,1
    3,5.0,3.0,0
    4,5.0,4.0,1
    """
    (dataset_dir / "data.csv").write_text(csv_content)
    
    # Create metadata
    import json
    metadata = {
        "dataset_id": "zero_variance",
        "task_type": "classification",
        "num_rows": 4,
        "has_text": False,
        "has_image": False
    }
    with open(dataset_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)
    
    return dataset_dir