import os
from pathlib import Path
import tempfile
import requests

import pandas as pd
import pytest

# Existing test(s) from the original test_metrics.py are retained.
# If there were previously defined tests (e.g., test_correlation_calculation),
# they remain unchanged above this block.

# ----------------------------------------------------------------------
# Integration test: end‑to‑end pilot study data flow
# ----------------------------------------------------------------------
def test_pilot_study_data_flow(tmp_path: Path):
    """
    Verify that the full pilot‑study data pipeline works:
    1. Human ratings CSV is written to the expected location.
    2. Metrics CSV is available.
    3. ``compute_correlation`` can load both files and return a numeric
       Pearson correlation coefficient (and optionally a p‑value).
    """
    # Remember the original working directory and switch to the temporary one.
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # --------------------------------------------------------------
        # 1. Create the directory layout expected by the pipeline.
        # --------------------------------------------------------------
        (Path("data") / "measurements").mkdir(parents=True, exist_ok=True)
        (Path("data") / "processed").mkdir(parents=True, exist_ok=True)

        # --------------------------------------------------------------
        # 2. Write a minimal human‑ratings CSV.
        # --------------------------------------------------------------
        human_ratings = pd.DataFrame(
            {
                "image_id": ["img1", "img2"],
                "participant_id": ["p1", "p2"],
                "complexity_score": [5.0, 8.0],
            }
        )
        human_ratings_path = Path("data/measurements/human_ratings.csv")
        human_ratings.to_csv(human_ratings_path, index=False)

        # --------------------------------------------------------------
        # 3. Write a matching metrics CSV.
        # --------------------------------------------------------------
        metrics = pd.DataFrame(
            {
                "image_id": ["img1", "img2"],
                # The metric column name used by ``pilot_gate`` is
                # ``complexity_metric`` (the exact name is not critical for the
                # integration test as long as it is numeric and aligns on
                # ``image_id``).
                "complexity_metric": [3.0, 9.0],
            }
        )
        metrics_path = Path("data/processed/metrics.csv")
        metrics.to_csv(metrics_path, index=False)

        # --------------------------------------------------------------
        # 4. Import and run the correlation computation.
        # --------------------------------------------------------------
        from src.experiment.pilot_gate import compute_correlation

        result = compute_correlation()

        # ``compute_correlation`` may return either a single float (the r‑value)
        # or a tuple ``(r, p)``.  Normalise the output for the assertions.
        if isinstance(result, tuple):
            r, p = result
        else:
            r = result
            p = None  # type: ignore

        # --------------------------------------------------------------
        # 5. Basic sanity checks.
        # --------------------------------------------------------------
        assert isinstance(r, float), "Correlation coefficient should be a float"
        # With the synthetic data above the relationship is perfectly monotonic,
        # so the correlation must be positive (and close to 1.0).
        assert r > 0.0, "Correlation should be positive for the test data"
    finally:
        # Restore the original working directory so subsequent tests are not affected.
        os.chdir(original_cwd)

# ----------------------------------------------------------------------
# Unit test: entropy calculation
# ----------------------------------------------------------------------
def test_entropy_calculation():
    """
    Verify that ``compute_entropy`` returns a deterministic, non‑negative
    float for a real image downloaded from the internet.
    The test checks basic properties rather than an exact numeric value,
    because the exact entropy depends on the implementation details of
    ``compute_entropy``.
    """
    # Download a small, publicly available image.
    image_url = "https://via.placeholder.com/64.png"
    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = Path(tmpdir) / "test_image.png"
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        image_path.write_bytes(response.content)

        # Import the entropy function from the metrics module.
        from src.metrics.extract import compute_entropy

        # Compute entropy twice to ensure determinism.
        entropy_one = compute_entropy(str(image_path))
        entropy_two = compute_entropy(str(image_path))

        # Basic sanity checks.
        assert isinstance(entropy_one, float), "Entropy should be a float"
        assert entropy_one >= 0.0, "Entropy should be non‑negative"
        # The two computations on the same image must match (within a tiny tolerance).
        assert abs(entropy_one - entropy_two) < 1e-9, "Entropy should be deterministic"

        # Entropy for an 8‑bit image cannot exceed 8.0 bits.
        assert entropy_one <= 8.0, "Entropy should not exceed 8 bits for an 8‑bit image"