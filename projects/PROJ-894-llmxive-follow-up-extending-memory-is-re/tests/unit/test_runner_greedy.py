"""
Unit tests for the Greedy Runner (T019b).
"""

import os
import sys
import json
import tempfile
import csv
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runner import TimeoutHandler, TaskResult, load_graph, load_tasks
from strategies.greedy_runner import evaluate_task, save_results_to_csv, normalize_answer

class MockGraph:
    def __init__(self):
        self.nodes = ['A', 'B', 'C']
        self.edges = [('A', 'B'), ('B', 'C')]
        self.number_of_nodes = lambda: 3
        self.number_of_edges = lambda: 2
        self.successors = lambda n: []
        self.predecessors = lambda n: []
    
class MockStrategy:
    def __init__(self, result=None):
        self.result = result or {'nodes_visited': 10, 'accuracy': 1.0, 'resolved': True, 'evidence_threshold': 0.8}
    
    def __call__(self, **kwargs):
        return self.result

def test_normalize_answer():
    assert normalize_answer("  Hello World  ") == "hello world"
    assert normalize_answer("") == ""
    assert normalize_answer(None) == ""

def test_evaluate_task_success():
    task = {
        'task_id': 'test_1',
        'question': 'What is 2+2?',
        'context': '2+2 is 4.',
        'answer': '4'
    }
    graph = MockGraph()
    mock_strategy = MockStrategy()
    handler = TimeoutHandler(duration=10)
    
    result = evaluate_task(task, graph, mock_strategy, handler)
    
    assert result.task_id == 'test_1'
    assert result.status == 'COMPLETED'
    assert result.accuracy == 1.0
    assert result.nodes_visited == 10
    assert result.evidence_threshold == 0.8

def test_evaluate_task_timeout():
    def slow_strategy(**kwargs):
        import time
        time.sleep(100) # Should trigger timeout
        return {'nodes_visited': 0}
    
    task = {'task_id': 'test_timeout', 'question': 'Wait', 'context': '', 'answer': ''}
    graph = MockGraph()
    handler = TimeoutHandler(duration=1) # 1 second timeout
    
    # Note: In a real signal-based environment, this would raise TimeoutError.
    # For unit testing without signals, we simulate the exception handling if needed,
    # but here we test the structure.
    # We will mock the strategy to raise the custom TimeoutError to test the handler logic
    from runner import TimeoutError as RunnerTimeoutError
    
    def failing_strategy(**kwargs):
        raise RunnerTimeoutError("Simulated timeout")
    
    result = evaluate_task(task, graph, failing_strategy, handler)
    assert result.status == 'TIMEOUT'

def test_save_results_to_csv(tmp_path):
    output_file = tmp_path / "test_results.csv"
    results = [
        TaskResult("t1", 0.9, 5, 100.0, "COMPLETED", 100, 0.7),
        TaskResult("t2", 0.0, 2, 50.0, "UNRESOLVED", 50, 0.0)
    ]
    
    save_results_to_csv(results, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['task_id'] == 't1'
        assert rows[0]['status'] == 'COMPLETED'
        assert rows[1]['status'] == 'UNRESOLVED'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])