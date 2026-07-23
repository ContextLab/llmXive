import pytest
import os
import yaml
from pathlib import Path
from constitution import check_by_amendment_ratification, enforce_gate, ConstitutionalError

def test_check_pending():
    # Create a temporary state file with 'pending' status
    state_file = Path("test_state_pending.yaml")
    with open(state_file, 'w') as f:
        yaml.dump({"amendment_status": "pending"}, f)
    
    status = check_by_amendment_ratification(str(state_file))
    assert status == "pending"
    os.remove(state_file)

def test_check_ratified():
    state_file = Path("test_state_ratified.yaml")
    with open(state_file, 'w') as f:
        yaml.dump({"amendment_status": "ratified"}, f)
    
    status = check_by_amendment_ratification(str(state_file))
    assert status == "ratified"
    os.remove(state_file)

def test_check_missing_file():
    status = check_by_amendment_ratification("non_existent_file.yaml")
    assert status == "pending"

def test_enforce_gate_ratified():
    state_file = Path("test_gate_ratified.yaml")
    with open(state_file, 'w') as f:
        yaml.dump({"amendment_status": "ratified"}, f)
    
    result = enforce_gate(str(state_file))
    assert result is True
    os.remove(state_file)

def test_enforce_gate_pending():
    state_file = Path("test_gate_pending.yaml")
    with open(state_file, 'w') as f:
        yaml.dump({"amendment_status": "pending"}, f)
    
    with pytest.raises(ConstitutionalError):
        enforce_gate(str(state_file))
    os.remove(state_file)

def test_enforce_gate_missing():
    with pytest.raises(ConstitutionalError):
        enforce_gate("non_existent_gate.yaml")