import os
import json
import pytest
import pandas as pd
from pathlib import Path

from ingestion import (
    generate_validation_report, 
    validate_cue_reward_delay,
    run_ingestion_pipeline
)

@pytest.fixture
def temp_output_dir(tmp_path):
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True)
    return output_dir

def test_generate_validation_report_schema(temp_output_dir):
    """Test that generate_validation_report writes correct JSON schema."""
    report_path = str(temp_output_dir / "validation_report.json")
    
    generate_validation_report(
        total_rows=100,
        valid_rows=90,
        dropped_rows=10,
        sample_size=90,
        confounded_count=5,
        flagged_trial_ids=["t1", "t2", "t3", "t4", "t5"],
        output_path=report_path
    )

    assert os.path.exists(report_path)
    
    with open(report_path, 'r') as f:
        data = json.load(f)

    assert "ingestion_rows_total" in data
    assert "ingestion_rows_valid" in data
    assert "ingestion_rows_dropped" in data
    assert "validated_sample_size" in data
    assert "confounded_trial_count" in data
    assert "flagged_trial_ids" in data

    assert data["ingestion_rows_total"] == 100
    assert data["ingestion_rows_valid"] == 90
    assert data["ingestion_rows_dropped"] == 10
    assert data["validated_sample_size"] == 90
    assert data["confounded_trial_count"] == 5
    assert data["flagged_trial_ids"] == ["t1", "t2", "t3", "t4", "t5"]

def test_validate_cue_reward_delay_flags_confounded():
    """Test that trials with cue_delay < 500ms are flagged."""
    df = pd.DataFrame({
        'trial_id': ['t1', 't2', 't3', 't4'],
        'cue_time_ms': [100, 200, 600, 700],
        'reward_time_ms': [500, 500, 1000, 1200]
    })
    # cue_delay: 400, 300, 400, 500
    # Confounded (< 500): t1, t2, t3. t4 is exactly 500, so not < 500.
    
    df, flagged_ids = validate_cue_reward_delay(df, threshold=500.0)
    
    assert 'confounded' in df.columns
    assert df.loc[0, 'confounded'] == True  # 400 < 500
    assert df.loc[1, 'confounded'] == True  # 300 < 500
    assert df.loc[2, 'confounded'] == True  # 400 < 500
    assert df.loc[3, 'confounded'] == False # 500 is not < 500
    
    assert len(flagged_ids) == 3
    assert 't1' in flagged_ids
    assert 't2' in flagged_ids
    assert 't3' in flagged_ids
    assert 't4' not in flagged_ids