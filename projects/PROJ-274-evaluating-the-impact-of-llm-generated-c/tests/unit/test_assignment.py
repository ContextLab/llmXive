import pytest
import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.experiment.assignment import load_participant_list, stratified_random_assignment, save_assignment_log

def test_load_participant_list():
    # Create a temporary file with test data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump([{"id": "P1"}, {"id": "P2"}], f)
        temp_path = f.name

    try:
        participants = load_participant_list(temp_path)
        assert len(participants) == 2
        assert participants[0]['id'] == 'P1'
    finally:
        os.unlink(temp_path)

def test_stratified_random_assignment():
    participants = [{"id": f"P{i}"} for i in range(9)]
    # Seed ensures deterministic shuffle for this test
    assigned = stratified_random_assignment(participants, seed=42)
    
    assert len(assigned) == 9
    conditions = [p['condition'] for p in assigned]
    assert conditions.count('LLM') == 3
    assert conditions.count('Human') == 3
    assert conditions.count('None') == 3

def test_save_assignment_log():
    assigned = [{"id": "P1", "condition": "LLM"}, {"id": "P2", "condition": "Human"}]
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "assignment_log.json")
        save_assignment_log(assigned, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]['condition'] == 'LLM'