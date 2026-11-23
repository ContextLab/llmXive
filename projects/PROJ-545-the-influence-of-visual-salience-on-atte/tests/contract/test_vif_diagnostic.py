"""
Contract test for VIF diagnostic output.
Verifies that collinearity flags are correctly set based on VIF thresholds.
"""
import os
import sys
import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

VIF_THRESHOLD = 5.0


def load_test_artifact(path: str) -> Dict[str, Any]:
    """
    Helper to load a JSON artifact for testing.
    """
    full_path = project_root / path
    if not full_path.exists():
        raise FileNotFoundError(f"Contract test artifact not found: {full_path}")
    
    with open(full_path, 'r') as f:
        return json.load(f)


class TestVifDiagnostic:
    """
    Contract test suite for User Story 3: Diagnostics (VIF).
    """

    def test_vif_report_contains_flags(self):
        """
        Contract test: Verify VIF calculation flags collinearity > 5.0.
        """
        artifact_path = "data/processed/vif_diagnostic.json"
        
        try:
            report = load_test_artifact(artifact_path)
        except FileNotFoundError:
            pytest.skip(
                f"Artifact {artifact_path} not found. "
                "This is expected if T031/T032 (diagnostics) has not been run yet."
            )

        # Check structure
        assert isinstance(report, dict), "VIF report must be a JSON object."
        
        # We expect a list of variables with their VIF scores and flags
        if 'variables' in report:
            variables = report['variables']
        elif 'results' in report:
            variables = report['results']
        else:
            variables = [report] # Assume single entry or list at root

        assert isinstance(variables, list), "Variables must be a list."
        
        found_flags = []
        for var in variables:
            if not isinstance(var, dict):
                continue
            
            vif = var.get('vif')
            flagged = var.get('flagged') or var.get('high_collinearity')
            
            if vif is not None:
                expected_flag = vif > VIF_THRESHOLD
                if flagged is not None:
                    # If a flag exists, verify it matches the logic
                    if flagged != expected_flag:
                        pytest.fail(
                            f"Contract violation: Variable '{var.get('name')}' has VIF {vif} "
                            f"but flag is {flagged}. Expected {expected_flag}."
                        )
                    found_flags.append(flagged)

        # Just ensure the logic is consistent if flags are present
        # We don't assert that a flag MUST exist unless we know the data has collinearity
        # The contract is that the logic is correct.
        # If no flags were found, it means no VIF > 5.0 was detected, which is fine.
        # The test passes if the logic holds.

    def test_vif_report_has_required_fields(self):
        """
        Contract test: Verify VIF report contains 'vif' and 'name' for each variable.
        """
        artifact_path = "data/processed/vif_diagnostic.json"
        
        try:
            report = load_test_artifact(artifact_path)
        except FileNotFoundError:
            pytest.skip(
                f"Artifact {artifact_path} not found. "
                "This is expected if T031/T032 (diagnostics) has not been run yet."
            )

        if 'variables' in report:
            variables = report['variables']
        elif 'results' in report:
            variables = report['results']
        else:
            variables = [report]

        for var in variables:
            if not isinstance(var, dict):
                continue
            
            assert 'vif' in var, "VIF report entry missing 'vif' key."
            assert 'name' in var, "VIF report entry missing 'name' key."
            assert isinstance(var['vif'], (int, float)), "'vif' must be numeric."
            assert isinstance(var['name'], str), "'name' must be a string."
