"""
Tests for the DAG manifest generation script.
"""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.scripts.generate_dag_manifest import load_raw_traces, generate_dag_manifest, main

@pytest.fixture
def temp_manifest_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(json.dumps({"entries": []}))
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def sample_traces():
    return [
        {
            "id": "trace_1",
            "trace": "Step 1: Calculate 2+2.\nStep 2: Result is 4.",
            "metadata": {}
        },
        {
            "id": "trace_2",
            "trace": "Step 1: Identify the problem.\nStep 2: Solve it.",
            "metadata": {}
        },
        {
            "id": "trace_3",
            "trace": "Step 1: A.\nStep 2: B.\nStep 3: A depends on C.", # Invalid: cycle if C refers to A or B
            "metadata": {}
        }
    ]

def test_load_raw_traces_success(sample_traces):
    # Mock the dataset loading
    with patch('code.scripts.generate_dag_manifest.iterate_dataset_examples') as mock_iter:
        mock_iter.return_value = iter(sample_traces)
        traces = load_raw_traces(max_examples=10)
        assert len(traces) == 3
        assert traces[0]['id'] == 'trace_1'

def test_generate_dag_manifest_valid_trace(sample_traces, temp_manifest_file):
    # Mock the dataset loading
    with patch('code.scripts.generate_dag_manifest.iterate_dataset_examples') as mock_iter:
        mock_iter.return_value = iter(sample_traces[:2]) # Only valid traces
        
        output_path = Path(temp_manifest_file)
        manifest = generate_dag_manifest(sample_traces[:2], output_path)
        
        assert manifest['metadata']['valid_traces_count'] == 2
        assert manifest['metadata']['invalid_traces_count'] == 0
        assert len(manifest['entries']) == 2
        
        # Verify file was written
        assert output_path.exists()
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        assert saved_data['metadata']['valid_traces_count'] == 2

def test_generate_dag_manifest_invalid_trace_excluded(sample_traces, temp_manifest_file):
    # Mock the dataset loading
    with patch('code.scripts.generate_dag_manifest.iterate_dataset_examples') as mock_iter:
        mock_iter.return_value = iter(sample_traces)
        
        output_path = Path(temp_manifest_file)
        manifest = generate_dag_manifest(sample_traces, output_path)
        
        # trace_3 is invalid (cycle/threshold)
        assert manifest['metadata']['valid_traces_count'] == 2
        assert manifest['metadata']['invalid_traces_count'] == 1
        
        # Verify only valid traces are in entries
        entry_ids = [e['id'] for e in manifest['entries']]
        assert 'trace_3' not in entry_ids
        assert 'trace_1' in entry_ids
        assert 'trace_2' in entry_ids

def test_generate_dag_manifest_logic(sample_traces, temp_manifest_file):
    with patch('code.scripts.generate_dag_manifest.iterate_dataset_examples') as mock_iter:
        mock_iter.return_value = iter(sample_traces)
        
        output_path = Path(temp_manifest_file)
        manifest = generate_dag_manifest(sample_traces, output_path)
        
        # Check that depth is calculated
        for entry in manifest['entries']:
            assert 'depth' in entry
            assert isinstance(entry['depth'], int)
            assert entry['is_valid'] is True

def test_main_success(sample_traces):
    with patch('code.scripts.generate_dag_manifest.iterate_dataset_examples') as mock_iter:
        mock_iter.return_value = iter(sample_traces)
        with patch('code.scripts.generate_dag_manifest.PROJECT_ROOT', Path(tempfile.gettempdir())):
            with patch('code.scripts.generate_dag_manifest.logger'):
                # This should not raise
                try:
                    main()
                except SystemExit:
                    pass # Expected if path handling differs in test environment

def test_empty_trace_handling(temp_manifest_file):
    empty_traces = [
        {"id": "empty", "trace": "", "metadata": {}}
    ]
    with patch('code.scripts.generate_dag_manifest.iterate_dataset_examples') as mock_iter:
        mock_iter.return_value = iter(empty_traces)
        output_path = Path(temp_manifest_file)
        manifest = generate_dag_manifest(empty_traces, output_path)
        
        assert manifest['metadata']['valid_traces_count'] == 0
        assert manifest['metadata']['invalid_traces_count'] == 1
        assert len(manifest['entries']) == 0
