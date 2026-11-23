import os
import json
import pandas as pd
import pytest

def test_condition_report_creation(monkeypatch, tmp_path):
    # Create temporary raw and interim directories
    raw_dir = tmp_path / "raw"
    interim_dir = tmp_path / "interim"
    raw_dir.mkdir()
    interim_dir.mkdir()

    # Build a minimal valid CSV for rejection and reward
    df = pd.DataFrame({
        "participant_id": [1, 2],
        "condition": ["Rejection", "Control"],
        "reaction_time": [0.5, 0.6],
        "mood_rating": [3, 4]
    })
    df.to_csv(raw_dir / "rejection.csv", index=False)
    df.to_csv(raw_dir / "reward.csv", index=False)

    # Monkey‑patch config.get_path to point to our temporary directories
    import config
    original_get_path = config.get_path
    def fake_get_path(key: str):
        if key == "raw":
            return str(raw_dir)
        if key == "interim":
            return str(interim_dir)
        # fall back to the real implementation for other keys
        return original_get_path(key)
    monkeypatch.setattr(config, "get_path", fake_get_path)

    # Import the ingest module after monkey‑patching
    import ingest
    # Run the condition‑report generation
    report = ingest.process_condition_report()

    # Verify the JSON file was written and contains the expected keys/values
    report_path = os.path.join(str(interim_dir), "condition_report.json")
    assert os.path.exists(report_path), "condition_report.json was not created"

    with open(report_path, "r") as f:
        saved_report = json.load(f)

    assert saved_report["rejection_present"] is True
    assert saved_report["control_present"] is True
    assert saved_report["reward_present"] is True

    # Also verify the function returned the same dict
    assert report == saved_report