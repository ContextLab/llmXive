"""
Integration test for T023 – ensures that cleaned metrics are produced when cleaned
CSV files exist.
"""

import os
import json
import tempfile
import pandas as pd

from utils import setup_logging
from config import Config, get_config
from t023_reanalyze_cleaned_variants import main as run_t023


def _create_dummy_cleaned_csv(dir_path: str, name: str) -> str:
    """Create a minimal cleaned CSV file with numeric columns for analysis."""
    df = pd.DataFrame(
        {
            "feature1": [1.0, 2.0, 3.0, 4.0],
            "feature2": [2.0, 3.0, 4.0, 5.0],
            "outcome": [0, 1, 0, 1],
        }
    )
    csv_path = os.path.join(dir_path, f"{name}.csv")
    df.to_csv(csv_path, index=False)
    return csv_path


def test_cleaned_metrics_generated(tmp_path):
    # Arrange: create a temporary processed directory with a cleaned CSV
    processed_dir = os.path.join(tmp_path, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    _create_dummy_cleaned_csv(processed_dir, "dummy_cleaned")

    # Patch configuration to point to the temporary processed directory
    cfg = Config()
    cfg._overrides = {
        "PROCESSED_DATA_PATH": processed_dir,
        "CLEANED_METRICS_PATH": os.path.join(processed_dir, "cleaned_metrics.json"),
    }

    # Act: run the script
    run_t023()

    # Assert: cleaned_metrics.json exists and contains at least one dataset entry
    output_path = cfg.get("CLEANED_METRICS_PATH")
    assert os.path.isfile(output_path), "cleaned_metrics.json was not created"

    with open(output_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    assert "datasets" in metrics
    assert isinstance(metrics["datasets"], list)
    assert len(metrics["datasets"]) == 1
    entry = metrics["datasets"][0]
    assert entry["dataset_name"] == "dummy_cleaned"
    assert "analysis" in entry
    # Basic sanity checks on the analysis result structure
    assert "t_test" in entry["analysis"]
    assert "regression" in entry["analysis"]