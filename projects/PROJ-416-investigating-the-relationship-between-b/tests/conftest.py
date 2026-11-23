"""
Pytest configuration and shared fixtures for the Brain Network Dynamics pipeline.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def project_root_path():
    """Returns the path to the project root directory."""
    return project_root

@pytest.fixture(scope="session")
def data_root(project_root_path):
    """Returns the path to the data directory."""
    return project_root_path / "data"

@pytest.fixture(scope="session")
def temp_data_dir(tmp_path, data_root):
    """Creates a temporary directory within the data structure for tests."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir

@pytest.fixture
def mock_config(tmp_path):
    """Creates a mock Config object for testing."""
    from code.config import Config
    
    # Create a minimal config for testing that doesn't require env vars
    config = Config(
        openneuro_id="ds000000",
        n_subjects=2,
        stage="test"
    )
    # Override paths to use temp directory to avoid polluting real data
    config.data_root = tmp_path
    config.reports_root = tmp_path / "reports"
    config.reports_root.mkdir(exist_ok=True)
    return config

@pytest.fixture
def sample_metadata(tmp_path):
    """Creates a sample metadata JSON file for testing."""
    import json
    
    metadata = {
        "dataset_id": "ds000000",
        "study_design": "observational",
        "subjects": [
            {
                "subject_id": "sub-01",
                "pre_treatment_score": 25.0,
                "post_treatment_score": 18.0,
                "age": 30,
                "sex": "F",
                "medication_status": "none",
                "comorbidities": []
            },
            {
                "subject_id": "sub-02",
                "pre_treatment_score": 30.0,
                "post_treatment_score": 22.0,
                "age": 35,
                "sex": "M",
                "medication_status": "ssri",
                "comorbidities": ["depression"]
            }
        ],
        "instruments": [
            {
                "name": "GAD-7",
                "description": "Generalized Anxiety Disorder 7-item scale",
                "validated": True
            }
        ]
    }
    
    metadata_path = tmp_path / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return metadata_path

@pytest.fixture
def sample_network_metrics(tmp_path):
    """Creates a sample network metrics CSV file for testing."""
    import csv
    
    metrics_path = tmp_path / "network_metrics.csv"
    with open(metrics_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["subject_id", "modularity", "global_efficiency", "local_efficiency", "fd"])
        writer.writerow(["sub-01", 0.45, 0.62, 0.58, 0.15])
        writer.writerow(["sub-02", 0.48, 0.65, 0.60, 0.22])
    
    return metrics_path
