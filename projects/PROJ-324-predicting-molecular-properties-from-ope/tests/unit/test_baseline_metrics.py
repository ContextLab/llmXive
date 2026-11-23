import os
import sys
import pandas as pd
from pathlib import Path

# Ensure the project root is on the path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from code.analysis.stats import compute_baseline_metrics, ensure_dirs

def test_compute_baseline_metrics_creates_files(tmp_path, monkeypatch):
    """
    Verify that compute_baseline_metrics writes the expected CSV and PNG,
    that the CSV has exactly three rows (one per property), the header is correct,
    and that MAE values are non‑negative.
    """
    # Prepare a minimal but realistic baseline_test_predictions.csv if it does not exist.
    # This avoids fabricating data beyond the required schema; the test will only
    # run if the real file is present. If not, we skip the test with a clear message.
    predictions_path = Path('data/derived/baseline_test_predictions.csv')
    if not predictions_path.is_file():
        # Skip test – the upstream pipeline must generate this file.
        import pytest
        pytest.skip("Baseline test predictions file not found; upstream task must create it.")
    
    # Run the metric computation
    compute_baseline_metrics()
    
    # Check CSV existence and content
    metrics_path = Path('data/derived/baseline_metrics.csv')
    assert metrics_path.is_file(), "baseline_metrics.csv was not created"
    
    metrics_df = pd.read_csv(metrics_path)
    expected_columns = ['property', 'mae', 'rmse', 'n']
    assert list(metrics_df.columns) == expected_columns, f"CSV header mismatch: {list(metrics_df.columns)}"
    assert len(metrics_df) == 3, f"Expected 3 rows (one per property), got {len(metrics_df)}"
    assert (metrics_df['mae'] >= 0).all(), "MAE values must be non‑negative"
    
    # Check PNG existence
    png_path = Path('data/derived/baseline_residuals.png')
    assert png_path.is_file(), "baseline_residuals.png was not created"
    # Verify that the image can be opened (PIL import is safe here)
    from PIL import Image
    img = Image.open(png_path)
    assert img.size[0] >= 200 and img.size[1] >= 200, "Image dimensions are smaller than required"
    img.close()