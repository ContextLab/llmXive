"""
Integration test for T035b: Verify vif_diagnostic_log.json content.

This test asserts that:
1. The file `data/processed/vif_diagnostic_log.json` exists.
2. The file contains the key `flagged_features`.
3. The `flagged_features` key maps to a list (even if empty).
"""
import json
import os
import pytest
from pathlib import Path

# Import the project root helper to locate data directories dynamically
# Assuming code/analyze.py is in code/analyze.py, we import from there or derive root
# Since we cannot import from code/analyze directly without ensuring path, we derive root from this file's context
# or rely on standard project structure assumptions if not imported.
# However, the prompt says we can import from existing API surface.
# Let's assume the test runs from the project root or code/ is in sys.path.
# To be safe and robust, we derive the path relative to the test file or use a helper.

# Attempt to import the helper from code/analyze as per the provided API surface
try:
    from analyze import get_project_root
except ImportError:
    # Fallback if running as standalone script without code in path
    # Derive root from test location (tests/integration/) -> ../../
    import sys
    from pathlib import Path
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Re-attempt import or define helper locally
    def get_project_root():
        return project_root

def test_vif_diagnostic_log_exists_and_has_flagged_features():
    """
    Verify that vif_diagnostic_log.json exists and contains the 'flagged_features' key.
    """
    root = get_project_root()
    log_path = root / "data" / "processed" / "vif_diagnostic_log.json"

    # Assertion 1: File must exist
    assert log_path.exists(), f"File {log_path} does not exist. T035a (VIF calculation) may not have run or failed."

    # Assertion 2: File must be valid JSON
    with open(log_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"File {log_path} is not valid JSON: {e}")

    # Assertion 3: Must contain 'flagged_features' key
    assert "flagged_features" in data, \
        "Key 'flagged_features' not found in vif_diagnostic_log.json. T035a implementation may be missing this field."

    # Assertion 4: The value must be a list (as per diagnostic log structure)
    flagged = data["flagged_features"]
    assert isinstance(flagged, list), \
        f"'flagged_features' must be a list, got {type(flagged)}."

    # Optional: Log the content for debugging
    print(f"VIF Diagnostic Log Content: {data}")
    print(f"Flagged Features: {flagged}")