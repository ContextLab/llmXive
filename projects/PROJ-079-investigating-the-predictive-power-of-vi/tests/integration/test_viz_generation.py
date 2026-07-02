import os
import json
import pytest
from pathlib import Path

# Ensure we can import from the project root (src, tests)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.model import run_pipeline as run_model_pipeline
from src.viz import run_viz_pipeline
from src.config import DATA_PROCESSED_PATH, ARTIFACTS_PATH


def test_viz_generation():
    """
    Integration test verifying that plot generation produces the required files:
    - data/artifacts/plots/coefficients.png
    - data/artifacts/plots/pdp_top5.png

    This test assumes that the upstream pipeline (data processing and model training)
    has already been executed successfully, producing the necessary artifacts
    (aggregated dataset, trained model, p-values).
    """
    # Define expected output paths
    plots_dir = Path(ARTIFACTS_PATH) / "plots"
    coefficients_path = plots_dir / "coefficients.png"
    pdp_path = plots_dir / "pdp_top5.png"

    # Ensure the plots directory exists (it should, but be safe)
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Check if the model artifacts exist. If not, the test cannot proceed
    # without running the full pipeline. For an integration test, we assume
    # the pipeline has run. If files are missing, we assert failure to indicate
    # the prerequisite steps are not met.
    model_path = Path(ARTIFACTS_PATH) / "models" / "elastic_net.pkl"
    pvalues_path = Path(ARTIFACTS_PATH) / "pvalues_exploratory.json"
    aggregated_path = Path(DATA_PROCESSED_PATH) / "aggregated_dataset.csv"

    if not aggregated_path.exists():
        pytest.fail(f"Prerequisite file missing: {aggregated_path}. Run the data pipeline first.")
    
    if not model_path.exists():
        pytest.fail(f"Prerequisite file missing: {model_path}. Run the model training first.")
    
    if not pvalues_path.exists():
        pytest.fail(f"Prerequisite file missing: {pvalues_path}. Run the debiased lasso step first.")

    # Run the visualization pipeline
    # This function should load the model, data, and p-values, then generate plots.
    try:
        run_viz_pipeline()
    except Exception as e:
        pytest.fail(f"Visualization pipeline failed to execute: {e}")

    # Verify files exist
    assert coefficients_path.exists(), f"File not found: {coefficients_path}"
    assert pdp_path.exists(), f"File not found: {pdp_path}"

    # Verify files are non-empty
    assert coefficients_path.stat().st_size > 0, f"File is empty: {coefficients_path}"
    assert pdp_path.stat().st_size > 0, f"File is empty: {pdp_path}"

    # Optional: Verify they look like valid images (basic header check for PNG)
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    with open(coefficients_path, 'rb') as f:
        header = f.read(8)
        assert header == b'\x89PNG\r\n\x1a\n', f"Invalid PNG header in {coefficients_path}"

    with open(pdp_path, 'rb') as f:
        header = f.read(8)
        assert header == b'\x89PNG\r\n\x1a\n', f"Invalid PNG header in {pdp_path}"
