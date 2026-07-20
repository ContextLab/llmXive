"""
Integration tests for execution trace generation (T024).

These tests verify that the `generate_execution_traces.py` script correctly
processes execution logs and produces a valid `execution_traces.csv` file
with the expected schema and content.
"""
import os
import sys
import json
import csv
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import Paths
from analysis.generate_execution_traces import (
    load_execution_logs,
    extract_trace_data,
    load_filtered_tasks_map,
    write_traces_csv,
    main
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Mimic project structure
        (tmp_path / 'data' / 'processed').mkdir(parents=True)
        (tmp_path / 'data' / 'processed' / 'agent_logs').mkdir(parents=True)

        # Create a dummy filtered_tasks.csv
        tasks_file = tmp_path / 'data' / 'processed' / 'filtered_tasks.csv'
        tasks_data = [
            {'task_id': 'task_001', 'constraint_count': 5, 'progressive_constraints': '[]'},
            {'task_id': 'task_002', 'constraint_count': 7, 'progressive_constraints': '[]'},
            {'task_id': 'task_003', 'constraint_count': 6, 'progressive_constraints': '[]'},
        ]
        pd.DataFrame(tasks_data).to_csv(tasks_file, index=False)

        # Create dummy execution logs
        logs_dir = tmp_path / 'data' / 'processed' / 'agent_logs'

        # Dual track log with violation
        log1 = {
            'task_id': 'task_001',
            'agent_type': 'dual_track',
            'violations': [{'constraint': 'C1', 'reason': 'Mismatch'}],
            'result': {'score': 0.5},
            'file': 'log1.json'
        }
        with open(logs_dir / 'log1.json', 'w') as f:
            json.dump(log1, f)

        # Monolithic log without violation
        log2 = {
            'task_id': 'task_002',
            'agent_type': 'monolithic',
            'violations': [],
            'result': {'score': 1.0},
            'file': 'log2.json'
        }
        with open(logs_dir / 'log2.json', 'w') as f:
            json.dump(log2, f)

        # Dual track log with no score (edge case)
        log3 = {
            'task_id': 'task_003',
            'agent_type': 'dual_track',
            'violations': [],
            'result': {},
            'file': 'log3.json'
        }
        with open(logs_dir / 'log3.json', 'w') as f:
            json.dump(log3, f)

        yield tmp_path


def test_load_filtered_tasks_map(temp_data_dir):
    """Test loading the filtered tasks map."""
    # Temporarily override Paths.PROCESSED_DIR for this test
    original_processed_dir = Paths.PROCESSED_DIR
    Paths.PROCESSED_DIR = temp_data_dir / 'data' / 'processed'

    try:
        tasks_map = load_filtered_tasks_map()
        assert 'task_001' in tasks_map
        assert tasks_map['task_001']['constraint_count'] == 5
        assert tasks_map['task_002']['constraint_count'] == 7
    finally:
        Paths.PROCESSED_DIR = original_processed_dir


def test_load_execution_logs(temp_data_dir):
    """Test loading execution logs."""
    logs_dir = temp_data_dir / 'data' / 'processed' / 'agent_logs'
    logs = load_execution_logs(logs_dir)
    assert len(logs) == 3
    task_ids = {log['task_id'] for log in logs}
    assert task_ids == {'task_001', 'task_002', 'task_003'}


def test_extract_trace_data(temp_data_dir):
    """Test extracting trace data from logs."""
    # Setup
    logs_dir = temp_data_dir / 'data' / 'processed' / 'agent_logs'
    logs = load_execution_logs(logs_dir)

    # Temporarily override Paths.PROCESSED_DIR
    original_processed_dir = Paths.PROCESSED_DIR
    Paths.PROCESSED_DIR = temp_data_dir / 'data' / 'processed'

    try:
        tasks_map = load_filtered_tasks_map()
        traces = extract_trace_data(logs, tasks_map)

        assert len(traces) == 3

        # Check task_001 (dual_track, violation)
        t1 = next(t for t in traces if t['task_id'] == 'task_001')
        assert t1['architecture'] == 'dual_track'
        assert t1['constraint_count'] == 5
        assert t1['violation'] is True
        assert t1['final_score'] == 0.5

        # Check task_002 (monolithic, no violation)
        t2 = next(t for t in traces if t['task_id'] == 'task_002')
        assert t2['architecture'] == 'monolithic'
        assert t2['constraint_count'] == 7
        assert t2['violation'] is False
        assert t2['final_score'] == 1.0

        # Check task_003 (dual_track, no score)
        t3 = next(t for t in traces if t['task_id'] == 'task_003')
        assert t3['architecture'] == 'dual_track'
        assert t3['constraint_count'] == 6
        assert t3['violation'] is False
        assert t3['final_score'] == 0.0  # Default for missing score

    finally:
        Paths.PROCESSED_DIR = original_processed_dir


def test_write_traces_csv(temp_data_dir):
    """Test writing traces to CSV."""
    traces = [
        {'task_id': 't1', 'architecture': 'dual_track', 'constraint_count': 5, 'violation': True, 'final_score': 0.5},
        {'task_id': 't2', 'architecture': 'monolithic', 'constraint_count': 7, 'violation': False, 'final_score': 1.0},
    ]

    output_file = temp_data_dir / 'data' / 'processed' / 'test_traces.csv'
    write_traces_csv(traces, output_file)

    assert output_file.exists()

    df = pd.read_csv(output_file)
    assert len(df) == 2
    assert list(df.columns) == ['task_id', 'architecture', 'constraint_count', 'violation', 'final_score']
    assert df.iloc[0]['task_id'] == 't1'
    assert df.iloc[0]['violation'] == True
    assert df.iloc[1]['architecture'] == 'monolithic'


def test_main_integration(temp_data_dir, monkeypatch):
    """Test the full main() pipeline."""
    # Mock sys.argv to simulate running the script
    # We don't need to change Paths here because the function uses global Paths
    # which we will temporarily override if needed, but the script uses global Paths.
    # To make the script use our temp dir, we need to patch Paths.PROCESSED_DIR
    # inside the function or before calling main.
    # Since main() uses global Paths, we patch it before calling main.

    original_processed_dir = Paths.PROCESSED_DIR
    Paths.PROCESSED_DIR = temp_data_dir / 'data' / 'processed'

    try:
        result = main()
        assert result == 0

        output_file = Paths.PROCESSED_DIR / 'execution_traces.csv'
        assert output_file.exists()

        df = pd.read_csv(output_file)
        assert len(df) == 3
        assert 'task_id' in df.columns
        assert 'architecture' in df.columns
        assert 'constraint_count' in df.columns
        assert 'violation' in df.columns
        assert 'final_score' in df.columns
    finally:
        Paths.PROCESSED_DIR = original_processed_dir
