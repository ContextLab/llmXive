import json
import os
import random
from pathlib import Path
from dataset.injector import inject_failures

def test_deterministic_error_injection():
    """Verify deterministic error injection into success tasks."""
    # Create sample data
    sample_data = [
        {'id': 1, 'ground_truth': 'success', 'tool_output': 'output1'},
        {'id': 2, 'ground_truth': 'success', 'tool_output': 'output2'},
        {'id': 3, 'ground_truth': 'failure', 'tool_output': 'error1'},
        {'id': 4, 'ground_truth': 'success', 'tool_output': 'output3'},
    ]
    
    # Inject failures with fixed seed
    injected = inject_failures(sample_data, num_failures=2, seed=42)
    
    # Verify only success tasks were modified
    assert len(injected) == 2
    for item in injected:
        assert item.get('injected_error_pattern') is True
        assert 'ERROR:' in item.get('tool_output', '')
    
    # Verify determinism
    injected2 = inject_failures(sample_data, num_failures=2, seed=42)
    assert json.dumps(injected) == json.dumps(injected2)
