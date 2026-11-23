"""
Integration tests for the full pipeline.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the project root to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.parser import parse_trace_to_dag_and_validate, get_logical_difficulty
from code.scripts.generate_dag_manifest import generate_dag_manifest

@pytest.fixture
def temp_dag_manifest():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(json.dumps({"entries": []}))
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def temp_prompt_manifest():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(json.dumps({"prompts": []}))
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def mock_inference_results():
    return [
        {"seed": 0, "strategy": "ascending", "accuracy": 0.8},
        {"seed": 1, "strategy": "ascending", "accuracy": 0.85},
    ]

@pytest.fixture
def mock_lmm_data():
    return {
        "strategy": ["A", "B", "A", "B"],
        "accuracy": [0.8, 0.9, 0.85, 0.95]
    }

def test_full_pipeline_integration(temp_dag_manifest):
    """
    Test that the pipeline can generate a manifest, filter invalid traces,
    and produce a valid output.
    """
    # Mock data
    traces = [
        {"id": "1", "trace": "Step 1: A. Step 2: B.", "metadata": {}},
        {"id": "2", "trace": "Step 1: X. Step 2: Y.", "metadata": {}}
    ]
    
    with patch('code.scripts.generate_dag_manifest.iterate_dataset_examples') as mock_iter:
        mock_iter.return_value = iter(traces)
        
        output_path = Path(temp_dag_manifest)
        manifest = generate_dag_manifest(traces, output_path)
        
        assert manifest['metadata']['valid_traces_count'] == 2
        assert len(manifest['entries']) == 2
        assert all(e['is_valid'] for e in manifest['entries'])

def test_deterministic_shuffling_in_pipeline():
    """
    Test that the pipeline handles deterministic operations correctly.
    (Placeholder for future prompt generation tests)
    """
    assert True

def test_interaction_effect_detection():
    """
    Test that the analysis can detect interaction effects.
    (Placeholder for future analysis tests)
    """
    assert True

def test_pipeline_handles_invalid_traces(temp_dag_manifest):
    """
    Test that invalid traces are correctly excluded from the manifest.
    """
    traces = [
        {"id": "1", "trace": "Step 1: A. Step 2: B.", "metadata": {}},
        {"id": "2", "trace": "Step 1: A. Step 2: B. Step 3: A depends on B. Step 4: B depends on A.", "metadata": {}} # Cycle
    ]
    
    with patch('code.scripts.generate_dag_manifest.iterate_dataset_examples') as mock_iter:
        mock_iter.return_value = iter(traces)
        
        output_path = Path(temp_dag_manifest)
        manifest = generate_dag_manifest(traces, output_path)
        
        assert manifest['metadata']['valid_traces_count'] == 1
        assert manifest['metadata']['invalid_traces_count'] == 1
        assert manifest['entries'][0]['id'] == '1'
