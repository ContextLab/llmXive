import os
import json
import pytest
from pathlib import Path

# Add project root to path if necessary
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config import RESULTS_ROOT
from utils import causal_language_scanner

FINAL_REPORT_PATH = os.path.join(RESULTS_ROOT, "final_report.json")
SCHEMA_PATH = "contracts/output.schema.yaml"

@pytest.fixture
def report_exists():
    if not os.path.exists(FINAL_REPORT_PATH):
        pytest.skip(f"Final report not found at {FINAL_REPORT_PATH}. Run pipeline first.")
    return True

def test_final_report_exists(report_exists):
    """Verify that the final report file is created."""
    assert os.path.exists(FINAL_REPORT_PATH), "Final report file missing."
    assert os.path.getsize(FINAL_REPORT_PATH) > 0, "Final report file is empty."

def test_final_report_valid_json(report_exists):
    """Verify that the final report is valid JSON."""
    with open(FINAL_REPORT_PATH, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in final report: {e}")
    assert isinstance(data, dict), "Final report root must be a dictionary."

def test_final_report_schema_structure(report_exists):
    """Verify that the final report contains required top-level keys."""
    with open(FINAL_REPORT_PATH, 'r') as f:
        data = json.load(f)
    
    required_keys = ['metadata', 'model_summary', 'interpretation', 'diagnostics']
    missing = [k for k in required_keys if k not in data]
    assert not missing, f"Missing required keys in final report: {missing}"

def test_final_report_no_causal_language(report_exists):
    """Verify that the interpretation field does not contain forbidden causal terms."""
    with open(FINAL_REPORT_PATH, 'r') as f:
        data = json.load(f)
    
    interpretation = data.get('interpretation', '')
    assert isinstance(interpretation, str), "Interpretation must be a string."
    
    if causal_language_scanner(interpretation, forbidden_words=['causes', 'leads to', 'impacts', 'determines', 'results in']):
        pytest.fail(f"Causal language detected in interpretation: {interpretation}")