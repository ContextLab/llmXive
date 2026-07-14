import os
import json
import pytest
from code.config import load_decision_record, save_decision_record, DECISION_RECORD_PATH

@pytest.fixture
def temp_decision_record(tmp_path):
    """Create a temporary decision record for testing."""
    # Note: In a real test environment, we might mock the path,
    # but here we verify the file exists as per task requirements.
    pass

def test_decision_record_exists():
    """Verify that the decision_record.json file exists."""
    assert os.path.exists(DECISION_RECORD_PATH), "decision_record.json must exist"

def test_decision_record_structure():
    """Verify the decision record contains the required fields for FR-001(b) exclusion."""
    record = load_decision_record()
    
    assert "decision_id" in record, "decision_id is required"
    assert "related_requirement" in record, "related_requirement is required"
    assert record["related_requirement"] == "FR-001(b)", "Must reference FR-001(b)"
    assert "decision" in record, "decision field is required"
    assert record["decision"] == "EXCLUDED", "Decision must be EXCLUDED"
    assert "rationale" in record, "rationale is required"
    assert isinstance(record["rationale"], list), "rationale must be a list"
    assert len(record["rationale"]) > 0, "rationale must not be empty"
    
    # Check specific constraints mentioned in the task
    rationale_text = " ".join(record["rationale"])
    assert "external API" in rationale_text.lower() or "api call" in rationale_text.lower(), \
        "Rationale must mention external API constraint"
    assert "public dataset" in rationale_text.lower() or "factorial design" in rationale_text.lower(), \
        "Rationale must mention dataset unavailability"

def test_decision_record_is_valid_json():
    """Ensure the file is valid JSON."""
    with open(DECISION_RECORD_PATH, 'r') as f:
        try:
            json.load(f)
        except json.JSONDecodeError:
            pytest.fail("decision_record.json is not valid JSON")