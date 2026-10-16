import json
from pathlib import Path

import pandas as pd

from code.generate_synthetic_data import (
    check_download_status,
    generate_synthetic_data,
    main,
)

def test_generate_synthetic_data_structure(tmp_path, monkeypatch):
    """
    Verify that the synthetic generator produces a DataFrame with the
    required columns, the correct number of rows, and that the trigger
    column is independent of the agency score.
    """
    # Force the status file to indicate 'unavailable'
    status_path = Path("data/raw/download_status.json")
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(
            {
                "status": "unavailable",
                "instrument_valid": False,
                "use_synthetic": False,
            }
        )
    )

    # Run the script (it will generate the CSV)
    main()

    csv_path = Path("data/raw/synthetic_data.csv")
    assert csv_path.exists(), "Synthetic CSV was not created"

    df = pd.read_csv(csv_path)
    # Required columns
    expected_cols = {
        "participant_id",
        "latency",
        "smoothness",
        "lead_time",
        "agency_score",
        "user_response_trigger",
    }
    assert set(df.columns) == expected_cols

    # Row count
    assert len(df) >= 150

    # Independence check (Pearson |r| < 0.05)
    corr = df["user_response_trigger"].corr(df["agency_score"])
    assert abs(corr) < 0.05, f"Trigger correlated with agency (|r|={corr})"

    # Verify status JSON was updated
    updated_status = json.loads(status_path.read_text())
    assert updated_status["use_synthetic"] is True
    assert updated_status["status"] == "synthetic"