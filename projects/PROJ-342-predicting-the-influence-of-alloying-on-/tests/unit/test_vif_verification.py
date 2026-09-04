import os
import json
import pytest
from pathlib import Path

# Import the project root helper to ensure we look in the right place
# We assume the test is run from the project root or code/ is in sys.path
from code.analyze import get_project_root

def test_vif_diagnostic_log_exists_and_has_flagged_features():
    """
    T035b Verification: Assert file exists and contains `flagged_features` key.
    """
    project_root = get_project_root()
    log_path = project_root / "data" / "processed" / "vif_diagnostic_log.json"

    # 1. Assert file exists
    assert log_path.exists(), f"VIF diagnostic log not found at {log_path}. " \
                              "Ensure T035a has run successfully to generate this file."

    # 2. Load and parse JSON
    try:
        with open(log_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"VIF diagnostic log is not valid JSON: {e}")

    # 3. Assert required key exists
    assert "flagged_features" in data, \
        f"Key 'flagged_features' missing in {log_path}. " \
        "The VIF calculation (T035a) must populate this key."

    # 4. Assert the key is a list (structure expectation)
    flagged = data["flagged_features"]
    assert isinstance(flagged, list), \
        f"'flagged_features' must be a list, got {type(flagged)}."

    # Optional: If the list is empty, that's valid (no multicollinearity),
    # but the key must exist. If the task implies specific features should be
    # flagged based on the data, we could add checks here, but the spec
    # only mandates the key existence.
    print(f"VIF Diagnostic Log verified at {log_path}")
    print(f"Flagged features count: {len(flagged)}")
    if flagged:
        print(f"Flagged: {flagged}")
