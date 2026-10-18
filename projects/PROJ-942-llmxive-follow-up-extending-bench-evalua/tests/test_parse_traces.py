import pytest
import pandas as pd
import json
from pathlib import Path
import shutil
from code.pipelines.parse_traces import parse_json_file, main as parse_main
import sys
from unittest.mock import patch

@pytest.fixture
def mock_raw_data(tmp_path):
    """Creates a temporary directory with sample pi-Bench JSON files."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    # Task 1: Standard list of turns
    task1 = [
        {"speaker": "user", "utterance": "Hello", "intent": "greeting"},
        {"speaker": "agent", "utterance": "Hi there!", "intent": None}
    ]
    # Task 2: Dict with 'dialogue' key
    task2 = {
        "task_id": "task_02",
        "dialogue": [
            {"speaker": "user", "text": "Book a flight", "hidden_intent": "travel"},
            {"speaker": "agent", "text": "Where to?", "hidden_intent": None}
        ]
    }
    
    with open(raw_dir / "task_01.json", "w") as f:
        json.dump(task1, f)
    with open(raw_dir / "task_02.json", "w") as f:
        json.dump(task2, f)
        
    return raw_dir

def test_parse_json_file_list(mock_raw_data):
    file_path = mock_raw_data / "task_01.json"
    turns = parse_json_file(file_path)
    assert len(turns) == 2
    assert turns[0]['task_id'] == "task_01"
    assert turns[0]['utterance'] == "Hello"
    assert turns[0]['ground_truth_intent'] == "greeting"

def test_parse_json_file_dict(mock_raw_data):
    file_path = mock_raw_data / "task_02.json"
    turns = parse_json_file(file_path)
    assert len(turns) == 2
    assert turns[0]['task_id'] == "task_02"
    assert turns[0]['utterance'] == "Book a flight"
    assert turns[0]['ground_truth_intent'] == "travel"

def test_full_pipeline(mock_raw_data, tmp_path):
    out_csv = tmp_path / "normalized.csv"
    
    # Mock sys.argv for the main() function
    test_args = ["parse_traces.py", "--raw-dir", str(mock_raw_data), "--out-csv", str(out_csv)]
    with patch.object(sys, 'argv', test_args):
        parse_main()
    
    assert out_csv.exists()
    df = pd.read_csv(out_csv)
    
    # 2 tasks * 2 turns = 4 rows
    assert len(df) == 4
    assert list(df.columns) == ['task_id', 'turn_index', 'speaker', 'utterance', 'ground_truth_intent']
    assert df['task_id'].nunique() == 2
    assert df['turn_index'].isin([0, 1]).all()