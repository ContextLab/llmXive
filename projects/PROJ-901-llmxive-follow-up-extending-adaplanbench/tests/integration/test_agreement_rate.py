import json
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.agreement_rate import (
    load_execution_traces, 
    load_human_annotations, 
    compute_agreement, 
    run_agreement_analysis
)
from code.config import Paths


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_execution_traces(temp_data_dir):
    """Test loading of execution traces."""
    traces_path = temp_data_dir / "execution_traces.csv"
    data = {
        'task_id': ['t1', 't2', 't3'],
        'architecture': ['dual', 'mono', 'dual'],
        'violation': [True, False, True]
    }
    df = pd.DataFrame(data)
    df.to_csv(traces_path, index=False)
    
    loaded = load_execution_traces(traces_path)
    assert len(loaded) == 3
    assert loaded['violation'].dtype == bool
    assert list(loaded['task_id']) == ['t1', 't2', 't3']


def test_load_human_annotations(temp_data_dir):
    """Test loading of human annotations."""
    annot_path = temp_data_dir / "human_annotations.csv"
    data = {
        'task_id': ['t1', 't2', 't3'],
        'human_violation': [True, True, False]
    }
    df = pd.DataFrame(data)
    df.to_csv(annot_path, index=False)
    
    loaded = load_human_annotations(annot_path)
    assert len(loaded) == 3
    assert loaded['human_violation'].dtype == bool


def test_compute_agreement(temp_data_dir):
    """Test agreement computation logic."""
    # t1: match (True, True)
    # t2: mismatch (False, True)
    # t3: mismatch (True, False)
    # Expected: 1/3 agreement
    
    traces_df = pd.DataFrame({
        'task_id': ['t1', 't2', 't3'],
        'architecture': ['dual', 'mono', 'dual'],
        'violation': [True, False, True]
    })
    
    annot_df = pd.DataFrame({
        'task_id': ['t1', 't2', 't3'],
        'human_violation': [True, True, False]
    })
    
    result = compute_agreement(traces_df, annot_df)
    
    assert result['total_tasks'] == 3
    assert result['agreed_count'] == 1
    assert abs(result['agreement_rate'] - (1/3)) < 0.001
    assert 0 <= result['ci_lower'] <= result['agreement_rate'] <= result['ci_upper'] <= 1


def test_run_agreement_analysis_integration(temp_data_dir):
    """Integration test for the full analysis pipeline."""
    # Prepare data
    traces_path = temp_data_dir / "execution_traces.csv"
    annot_path = temp_data_dir / "human_annotations.csv"
    output_path = temp_data_dir / "agreement_report.json"
    
    # 4 tasks: 2 match, 2 mismatch -> 50% agreement
    traces_df = pd.DataFrame({
        'task_id': ['t1', 't2', 't3', 't4'],
        'architecture': ['dual'] * 4,
        'violation': [True, False, True, False]
    })
    traces_df.to_csv(traces_path, index=False)
    
    annot_df = pd.DataFrame({
        'task_id': ['t1', 't2', 't3', 't4'],
        'human_violation': [True, True, False, False]
    })
    # t1: T==T (match)
    # t2: F!=T (mismatch)
    # t3: T!=F (mismatch)
    # t4: F==F (match)
    annot_df.to_csv(annot_path, index=False)
    
    result = run_agreement_analysis(traces_path, annot_path, output_path)
    
    assert result['total_tasks'] == 4
    assert result['agreed_count'] == 2
    assert abs(result['agreement_rate'] - 0.5) < 0.001
    
    assert output_path.exists()
    with open(output_path) as f:
        saved = json.load(f)
    assert saved['agreement_rate'] == result['agreement_rate']
    assert 'ci_lower' in saved
    assert 'ci_upper' in saved
