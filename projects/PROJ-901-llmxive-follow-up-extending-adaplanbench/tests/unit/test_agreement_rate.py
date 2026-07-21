"""
Unit tests for agreement_rate module.
"""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.agreement_rate import (
    load_execution_traces,
    load_human_annotations,
    simulate_human_annotation,
    compute_agreement,
    compute_confidence_interval,
    run_agreement_analysis
)


@pytest.fixture
def sample_traces():
    """Sample execution traces data."""
    return [
        {
            'task_id': 'task_001',
            'architecture': 'dual_track',
            'constraint_count': '5',
            'violation_boolean': 'True',
            'violation_reason': 'Constraint A violated',
            'final_score': '0.85'
        },
        {
            'task_id': 'task_002',
            'architecture': 'monolithic',
            'constraint_count': '6',
            'violation_boolean': 'False',
            'violation_reason': None,
            'final_score': '0.92'
        },
        {
            'task_id': 'task_003',
            'architecture': 'dual_track',
            'constraint_count': '7',
            'violation_boolean': 'True',
            'violation_reason': 'Constraint B violated',
            'final_score': '0.78'
        },
        {
            'task_id': 'task_004',
            'architecture': 'monolithic',
            'constraint_count': '8',
            'violation_boolean': 'False',
            'violation_reason': None,
            'final_score': '0.95'
        }
    ]


@pytest.fixture
def sample_annotations():
    """Sample annotation data."""
    return [
        {
            'task_id': 'task_001',
            'raw_prompt': 'Plan a trip...',
            'constraint_list': '["Constraint A", "Constraint B"]'
        },
        {
            'task_id': 'task_002',
            'raw_prompt': 'Plan a meeting...',
            'constraint_list': '["Constraint C"]'
        },
        {
            'task_id': 'task_003',
            'raw_prompt': 'Organize event...',
            'constraint_list': '["Constraint D", "Constraint E"]'
        },
        {
            'task_id': 'task_004',
            'raw_prompt': 'Schedule call...',
            'constraint_list': '["Constraint F"]'
        }
    ]


@pytest.fixture
def temp_csv_files(sample_traces, sample_annotations):
    """Create temporary CSV files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Write traces
        traces_path = tmpdir / 'execution_traces.csv'
        with open(traces_path, 'w', newline='') as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=sample_traces[0].keys())
            writer.writeheader()
            writer.writerows(sample_traces)
        
        # Write annotations
        annotations_path = tmpdir / 'annotation_sample.csv'
        with open(annotations_path, 'w', newline='') as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=sample_annotations[0].keys())
            writer.writeheader()
            writer.writerows(sample_annotations)
        
        yield traces_path, annotations_path


def test_load_execution_traces(temp_csv_files):
    """Test loading execution traces from CSV."""
    traces_path, _ = temp_csv_files
    traces = load_execution_traces(traces_path)
    
    assert len(traces) == 4
    assert traces[0]['task_id'] == 'task_001'
    assert traces[0]['violation_boolean'] == 'True'


def test_load_human_annotations(temp_csv_files):
    """Test loading human annotations from CSV."""
    _, annotations_path = temp_csv_files
    annotations = load_human_annotations(annotations_path)
    
    assert len(annotations) == 4
    assert annotations[0]['task_id'] == 'task_001'


def test_simulate_human_annotation_deterministic():
    """Test that simulation is deterministic for same task_id."""
    trace = {
        'task_id': 'test_task_123',
        'violation_boolean': True
    }
    annotation = {
        'task_id': 'test_task_123',
        'raw_prompt': 'test',
        'constraint_list': '[]'
    }
    
    # Run twice with same seed
    result1 = simulate_human_annotation(trace, annotation)
    result2 = simulate_human_annotation(trace, annotation)
    
    # Should be identical due to seeding
    assert result1 == result2


def test_compute_agreement(temp_csv_files):
    """Test agreement computation."""
    traces_path, annotations_path = temp_csv_files
    traces = load_execution_traces(traces_path)
    annotations = load_human_annotations(annotations_path)
    
    agreement_rate, rule_preds, human_labels = compute_agreement(traces, annotations)
    
    assert 0.0 <= agreement_rate <= 1.0
    assert len(rule_preds) == len(human_labels)
    assert len(rule_preds) == 4


def test_compute_confidence_interval():
    """Test confidence interval calculation."""
    # Perfect agreement
    lower, upper = compute_confidence_interval(1.0, 100)
    assert lower >= 0.95
    assert upper == 1.0
    
    # 50% agreement
    lower, upper = compute_confidence_interval(0.5, 100)
    assert lower < 0.5
    assert upper > 0.5
    
    # Zero sample
    lower, upper = compute_confidence_interval(0.5, 0)
    assert lower == 0.0
    assert upper == 0.0


def test_run_agreement_analysis(temp_csv_files):
    """Test full analysis pipeline."""
    traces_path, annotations_path = temp_csv_files
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'agreement_report.json'
        
        results = run_agreement_analysis(traces_path, annotations_path, output_path)
        
        # Check output file exists
        assert output_path.exists()
        
        # Check results structure
        assert 'agreement_rate' in results
        assert 'confidence_interval_lower' in results
        assert 'confidence_interval_upper' in results
        assert 'sample_size' in results
        
        # Check values are reasonable
        assert 0.0 <= results['agreement_rate'] <= 1.0
        assert results['sample_size'] == 4
        
        # Verify JSON file content
        with open(output_path, 'r') as f:
            file_results = json.load(f)
        
        assert file_results == results


def test_file_not_found():
    """Test error handling for missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_path = Path(tmpdir) / 'nonexistent.csv'
        
        with pytest.raises(FileNotFoundError):
            load_execution_traces(missing_path)
        
        with pytest.raises(FileNotFoundError):
            load_human_annotations(missing_path)
