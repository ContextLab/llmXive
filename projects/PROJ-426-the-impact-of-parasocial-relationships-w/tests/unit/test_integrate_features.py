import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project root is on the import path so that ``src`` can be imported.
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.features.integrate_features import main as integrate_main

@pytest.fixture
def temp_data_dirs():
    """
    Create a temporary ``data`` tree with minimal but realistic parquet files
    for the three input artefacts.  The fixture yields the root path so that
    the test can later verify the output location.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create the required sub‑folders
        (root / "data" / "processed").mkdir(parents=True, exist_ok=True)

        # Matched users – contains demographic columns and a loneliness score.
        matched = pd.DataFrame({
            "user_id": [f"user_{i:04d}" for i in range(5)],
            "loneliness_score": [0.1 * i for i in range(5)],
            "age": [25, 30, 35, 40, 45],
            "timestamp": pd.date_range("2023-01-01", periods=5, freq="M"),
        })
        matched_path = root / "data" / "processed" / "matched_users.parquet"
        matched.to_parquet(matched_path, index=False)

        # Usage metrics – one week per user for simplicity.
        usage = pd.DataFrame({
            "user_id": [f"user_{i:04d}" for i in range(5)],
            "week_start": pd.date_range("2023-01-02", periods=5, freq="W-MON"),
            "usage_frequency": [10, 5, 7, 3, 12],
            "session_duration": [120, 60, 90, 30, 150],
        })
        usage_path = root / "data" / "processed" / "usage_metrics.parquet"
        usage.to_parquet(usage_path, index=False)

        # Attachment scores – deliberately leave one user without scores.
        attachment = pd.DataFrame({
            "user_id": [f"user_{i:04d}" for i in range(4)],  # 4 out of 5 users
            "attachment_anxiety_score": [0.2, 0.4, 0.1, 0.3],
            "attachment_avoidance_score": [0.1, 0.0, 0.2, 0.4],
        })
        attachment_path = root / "data" / "processed" / "attachment_scores.parquet"
        attachment.to_parquet(attachment_path, index=False)

        # Provide the temporary tree to the test.
        yield root

def test_integrate_features_produces_unified_dataset_and_log(temp_data_dirs):
    """
    Run the integration script against the temporary data tree and verify:

    * ``unified_dataset.parquet`` exists and contains the expected columns.
    * ``logs/unified_dataset_validation.log`` exists and contains the text
      ``validation passed``.
    """
    # Patch the project‑root lookup performed inside the script so that it
    # uses the temporary directory instead of the real repository root.
    original_resolve = Path.resolve

    def fake_resolve(self, *args, **kwargs):
        # If the caller is trying to resolve ``__file__`` inside the script,
        # return a path that makes ``parents[2]`` point at ``temp_data_dirs``.
        if "integrate_features.py" in str(self):
            return temp_data_dirs / "code" / "src" / "features" / "integrate_features.py"
        return original_resolve(self, *args, **kwargs)

    Path.resolve = fake_resolve

    try:
        exit_code = integrate_main()
        assert exit_code == 0, "Script should exit with status 0"
    finally:
        # Restore the original method to avoid side‑effects for other tests.
        Path.resolve = original_resolve

    # Verify the unified dataset exists.
    unified_path = temp_data_dirs / "data" / "processed" / "unified_dataset.parquet"
    assert unified_path.exists(), "Unified dataset parquet file not created"

    df = pd.read_parquet(unified_path)

    # Expected columns (order is not important)
    expected_cols = {
        "user_id",
        "loneliness_score",
        "age",
        "timestamp",
        "week_start",
        "usage_frequency",
        "session_duration",
        "attachment_anxiety_score",
        "attachment_avoidance_score",
        "missing_attachment_flag",
    }
    assert expected_cols.issubset(set(df.columns)), "Missing expected columns in unified dataset"

    # Verify the validation log.
    log_path = temp_data_dirs / "logs" / "unified_dataset_validation.log"
    assert log_path.exists(), "Validation log file not created"
    content = log_path.read_text(encoding="utf-8").strip()
    assert content == "validation passed", "Log does not indicate successful validation"