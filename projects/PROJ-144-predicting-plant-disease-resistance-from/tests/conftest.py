"""
Pytest configuration and shared fixtures for the plant disease resistance
prediction pipeline tests.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide a temporary directory for test data files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session")
def sample_metabolite_data(test_data_dir):
    """Create a sample metabolite intensity matrix for testing."""
    # Create a small sample dataset
    np.random.seed(42)
    n_samples = 50
    n_features = 20

    data = np.random.rand(n_samples, n_features) * 100
    df = pd.DataFrame(
        data,
        columns=[f"Metabolite_{i:03d}" for i in range(n_features)]
    )
    df.insert(0, "sample_id", [f"sample_{i:03d}" for i in range(n_samples)])

    output_path = test_data_dir / "sample_metabolites.csv"
    df.to_csv(output_path, index=False)
    return output_path


@pytest.fixture(scope="session")
def sample_labels(test_data_dir):
    """Create sample resistance labels for testing."""
    np.random.seed(42)
    n_samples = 50

    labels = pd.DataFrame({
        "sample_id": [f"sample_{i:03d}" for i in range(n_samples)],
        "binary_label": np.random.choice([0, 1], size=n_samples),
        "harmonized_score": np.random.rand(n_samples) * 10
    })

    output_path = test_data_dir / "sample_labels.csv"
    labels.to_csv(output_path, index=False)
    return output_path


@pytest.fixture(scope="session")
def sample_study_manifest(test_data_dir):
    """Create a sample study manifest for testing."""
    manifest = {
        "studies": [
            {
                "study_id": "C00001",
                "title": "Sample Study 1",
                "has_pre_challenge": True,
                "has_resistance_data": True
            },
            {
                "study_id": "C00002",
                "title": "Sample Study 2",
                "has_pre_challenge": True,
                "has_resistance_data": True
            }
        ]
    }

    output_path = test_data_dir / "study_manifest.json"
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return output_path


@pytest.fixture
def mock_download_url():
    """Provide a mock URL for download testing."""
    return "https://www.metabolomicsworkbench.org/data/study_textformat.php?STUDY_ID=ST000001"


@pytest.fixture
def mock_study_data(test_data_dir):
    """Create mock study data files for testing."""
    # Create mock intensity file
    intensity_data = pd.DataFrame({
        "sample_id": ["s1", "s2", "s3"],
        "Metabolite_001": [100.5, 200.3, 150.2],
        "Metabolite_002": [50.1, 75.4, 60.8]
    })
    intensity_path = test_data_dir / "intensity_data.csv"
    intensity_data.to_csv(intensity_path, index=False)

    # Create mock phenotype file
    phenotype_data = pd.DataFrame({
        "sample_id": ["s1", "s2", "s3"],
        "germplasm_id": ["G1", "G1", "G2"],
        "resistance_score": [7.5, 8.2, 6.1],
        "timepoint": ["pre-challenge", "pre-challenge", "pre-challenge"]
    })
    phenotype_path = test_data_dir / "phenotype_data.csv"
    phenotype_data.to_csv(phenotype_path, index=False)

    return {
        "intensity": intensity_path,
        "phenotype": phenotype_path
    }
