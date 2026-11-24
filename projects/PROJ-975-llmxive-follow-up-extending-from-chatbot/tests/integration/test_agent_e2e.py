import os
import json
import pandas as pd
import pytest
from pathlib import Path

def test_agent_outputs_exist():
    # Check CSV
    csv_path = Path("data/results/experiment_log.csv")
    assert csv_path.exists(), "CSV log file should exist"
    df = pd.read_csv(csv_path)
    assert len(df) >= 100, "Should have at least 100 rows from the sample run"
    
    # Check JSON-L
    log_dir = Path("data/results/execution_logs")
    assert log_dir.exists(), "Execution logs directory should exist"
    log_files = list(log_dir.glob("*.jsonl"))
    assert len(log_files) > 0, "At least one JSON-L log file should exist"
    
    with open(log_files[0], 'r') as f:
        lines = f.readlines()
        assert len(lines) >= 100, "JSON-L file should have at least 100 entries"
        first_entry = json.loads(lines[0])
        assert "log_id" in first_entry
        assert "task_id" in first_entry
        assert "success" in first_entry