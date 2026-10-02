"""
Unit tests for the extract_features module (Task T019).
These tests verify the logic of filtering unparseable tasks and calculating basic metrics.
"""

import sys
import os
import pytest
from pathlib import Path
import pandas as pd
import tempfile
import json

# Add code/ to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.extract_features import (
    load_ground_truth,
    filter_unparseable,
    get_lines_of_code,
    get_cyclomatic_complexity,
    get_dependency_depth,
    calculate_semantic_complexity_score,
    extract_graph_and_metrics,
    serialize_graph
)


class TestFilterUnparseable:
    def test_filter_removes_unparseable(self):
        data = {
            'task_id': ['t1', 't2', 't3', 't4'],
            'code_diff': ['x=1', 'y=2', 'z=3', 'w=4'],
            'dynamic_execution_outcome': ['Pass', 'Unparseable', 'Fail', 'Unparseable']
        }
        df = pd.DataFrame(data)
        
        cleaned_df, count = filter_unparseable(df)
        
        assert count == 2
        assert len(cleaned_df) == 2
        assert 'Unparseable' not in cleaned_df['dynamic_execution_outcome'].values
        assert list(cleaned_df['task_id']) == ['t1', 't3']

    def test_filter_no_unparseable(self):
        data = {
            'task_id': ['t1', 't2'],
            'code_diff': ['x=1', 'y=2'],
            'dynamic_execution_outcome': ['Pass', 'Fail']
        }
        df = pd.DataFrame(data)
        
        cleaned_df, count = filter_unparseable(df)
        
        assert count == 0
        assert len(cleaned_df) == 2


class TestBasicMetrics:
    def test_lines_of_code(self):
        assert get_lines_of_code("x=1\ny=2") == 2
        assert get_lines_of_code("x=1\n\ny=2") == 2 # Empty lines ignored
        assert get_lines_of_code("") == 0
        assert get_lines_of_code(None) == 0

    def test_cyclomatic_complexity_simple(self):
        code = "x = 1"
        assert get_cyclomatic_complexity(code) == 0 # No branches

    def test_cyclomatic_complexity_branch(self):
        code = "if x:\n    pass"
        # radon usually counts the base + 1 for if
        cc = get_cyclomatic_complexity(code)
        assert cc >= 1

    def test_dependency_depth(self):
        code = "def f():\n    if x:\n        pass"
        depth = get_dependency_depth(code)
        assert depth >= 1


class TestGraphExtraction:
    def test_extract_graph_valid_code(self):
        code = "def hello():\n    print('world')"
        metrics = extract_graph_and_metrics(code, "test_task_1")
        
        assert metrics['task_id'] == "test_task_1"
        assert metrics['lines_of_code'] > 0
        assert 'graph_nodes' in metrics
        assert 'graph_edges' in metrics
        # Should have at least a function definition node
        assert len(metrics['graph_nodes']) > 0

    def test_serialize_graph(self):
        code = "x = 1"
        metrics = extract_graph_and_metrics(code, "test_serialize")
        
        # Create a temp directory for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override the global GRAPHS_DIR for this test
            import scripts.extract_features as ef
            original_dir = ef.GRAPHS_DIR
            ef.GRAPHS_DIR = Path(tmpdir)
            
            try:
                serialize_graph(metrics)
                output_file = Path(tmpdir) / "test_serialize.json"
                assert output_file.exists()
                
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                assert data['task_id'] == "test_serialize"
                assert 'graph' in data
            finally:
                ef.GRAPHS_DIR = original_dir

    def test_extract_graph_empty_code(self):
        metrics = extract_graph_and_metrics("", "test_empty")
        assert metrics['lines_of_code'] == 0
        assert metrics['cyclomatic_complexity'] == 0
        assert len(metrics['graph_nodes']) == 0