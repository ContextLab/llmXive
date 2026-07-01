import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add code to path if running standalone
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.generate_metrics_json import run_metric_aggregation
from utils.logging_config import get_logger

logger = get_logger(__name__)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    temp_root = Path(tempfile.mkdtemp())
    data_dir = temp_root / "data" / "processed"
    results_dir = temp_root / "data" / "results"
    data_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    yield temp_root, data_dir, results_dir
    shutil.rmtree(temp_root)

def create_mock_cleaned_data(path: Path, n_rows: int = 105):
    """Generate a mock cleaned_data.csv that meets SC-001 (>=100 rows)."""
    np.random.seed(42)
    data = {
        'participant_id': [f"p{i}" for i in range(n_rows)],
        'latency': np.random.normal(0.2, 0.05, n_rows),
        'smoothness': np.random.normal(0.8, 0.1, n_rows),
        'lead_time': np.random.normal(0.1, 0.02, n_rows),
        'agency_score': np.random.normal(0.6, 0.1, n_rows)
    }
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    logger.info(f"Created mock data at {path} with {n_rows} rows")

def test_run_metric_aggregation_creates_file(temp_data_dir):
    """Test that the aggregation script creates the output JSON file."""
    temp_root, data_dir, results_dir = temp_data_dir
    data_path = data_dir / "cleaned_data.csv"
    output_path = results_dir / "model_metrics.json"

    # Setup mock data
    create_mock_cleaned_data(data_path, n_rows=105)

    # Run aggregation
    run_metric_aggregation(str(data_path), str(output_path))

    # Verify output exists
    assert output_path.exists(), "model_metrics.json was not created"

    # Verify JSON structure
    with open(output_path) as f:
        data = json.load(f)

    assert "metadata" in data
    assert "models" in data
    assert "ols" in data["models"]
    assert "ridge" in data["models"]
    assert "random_forest" in data["models"]

    # Verify OLS has corrected p-values
    assert "pvalues_corrected" in data["models"]["ols"]
    assert "coefficients" in data["models"]["ols"]

    # Verify RF has feature importance
    assert "feature_importance" in data["models"]["random_forest"]
    assert "r_squared" in data["models"]["random_forest"]

def test_run_metric_aggregation_insufficient_data(temp_data_dir):
    """Test that the script fails gracefully with insufficient data."""
    temp_root, data_dir, results_dir = temp_data_dir
    data_path = data_dir / "cleaned_data.csv"
    output_path = results_dir / "model_metrics.json"

    # Create very small dataset
    create_mock_cleaned_data(data_path, n_rows=5)

    with pytest.raises(ValueError, match="Insufficient samples"):
        run_metric_aggregation(str(data_path), str(output_path))

def test_run_metric_aggregation_missing_file(temp_data_dir):
    """Test that the script fails if input file is missing."""
    temp_root, data_dir, results_dir = temp_data_dir
    data_path = data_dir / "cleaned_data.csv"
    output_path = results_dir / "model_metrics.json"

    with pytest.raises(FileNotFoundError):
        run_metric_aggregation(str(data_path), str(output_path))
