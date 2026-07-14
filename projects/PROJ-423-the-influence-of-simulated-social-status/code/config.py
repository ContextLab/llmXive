import os
import json
from typing import Any, Dict, Optional

DECISION_RECORD_PATH = "code/decision_record.json"

def load_decision_record() -> Dict[str, Any]:
    """
    Load the decision record from disk.
    If file doesn't exist, return an empty dictionary.
    """
    if not os.path.exists(DECISION_RECORD_PATH):
        return {}
    
    with open(DECISION_RECORD_PATH, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_decision_record(record: Dict[str, Any]) -> None:
    """
    Save the decision record to disk.
    """
    with open(DECISION_RECORD_PATH, 'w') as f:
        json.dump(record, f, indent=2, default=str)
