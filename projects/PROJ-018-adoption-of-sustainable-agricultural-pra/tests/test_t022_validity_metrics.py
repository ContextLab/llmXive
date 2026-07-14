"""Basic sanity test for the T022 implementation.

The test executes ``code/03_engineer_features.py`` on a minimal synthetic
dataset (generated on‑the‑fly) and checks that the required output files
exist and contain plausible values.
"""
import json
import os
import shutil
from pathlib import Path

import pandas as pd
import pytest
import yaml

# Import the module under test.
from code import config, logging_config
from code._03_engineer_features import main as engineer_main  # type: ignore

@pytest.fixture(scope="module")
def temp_project(tmp_path_factory):
    """Create a temporary project layout with minimal required files."""
    root = Path(tmp_path_factory.getbasetemp()) / "proj_temp"
    # Mimic the expected directory structure.
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (root / "results").mkdir(parents=True, exist_ok=True)
    (root / "code").mkdir(parents=True, exist_ok=True)

    # Write a minimal config that points to the temporary locations.
    cfg = {
        "project_root": str(root),
        "random_seed": 123,
        "proxy_variables": ["proxy1", "proxy2", "proxy3"],
    }
    config_path = root / "code" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)

    # Load the configuration so that ``get_config`` sees it.
    config.load_config(config_path)

    # Create a tiny cleaned dataset.
    cleaned = pd.DataFrame(
        {
            "proxy1": [1, 0, 1],
            "proxy2": [0, 1, 1],
            "proxy3": [1, 1, 0],
            "practice_organic": [0, 1, 0],
            "theoretical_construct": [2.5, 3.0, 2.8],
        }
    )
    cleaned_path = root / "data" / "processed" / "cleaned_data.csv"
    cleaned.to_csv(cleaned_path, index=False)

    yield root

    # Cleanup after the test module finishes.
    shutil.rmtree(root, ignore_errors=True)

def test_engineer_features_creates_outputs(temp_project):
    """Run the pipeline and verify output files and basic metric sanity."""
    # Change working directory to the temporary project root so that relative
    # paths inside the module resolve correctly.
    os.chdir(temp_project)

    # Execute the main pipeline.
    engineer_main()

    # Expected output locations.
    engineered_path = temp_project / "data" / "processed" / "engineered_data.csv"
    metrics_path = temp_project / "results" / "validity_metrics.yaml"
    log_path = temp_project / "modeling_log.yaml"

    # All three artefacts must exist.
    assert engineered_path.is_file(), "engineered_data.csv was not created"
    assert metrics_path.is_file(), "validity_metrics.yaml was not created"
    assert log_path.is_file(), "modeling_log.yaml was not created"

    # Load and perform very light sanity checks.
    engineered = pd.read_csv(engineered_path)
    assert "engagement_score" in engineered.columns
    assert "adoption_binary" in engineered.columns

    with metrics_path.open() as f:
        metrics = yaml.safe_load(f)

    # Cronbach's α should be a number between 0 and 1 for a sensible dataset.
    alpha = metrics.get("cronbach_alpha")
    assert isinstance(alpha, float) and 0.0 <= alpha <= 1.0

    # Convergent validity correlation should be a float (could be NaN for tiny data).
    conv = metrics.get("convergent_validity", {})
    assert "pearson_r" in conv
    assert "p_value" in conv

    # The modeling log must contain the status key.
    with log_path.open() as f:
        log_content = yaml.safe_load(f)
    assert log_content.get("validity", {}).get("convergent_validity_status") in {
        "passed",
        "failed",
    }