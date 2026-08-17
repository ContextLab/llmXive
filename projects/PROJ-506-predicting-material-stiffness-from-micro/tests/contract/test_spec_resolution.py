"""
Contract test for Spec Resolution T004.

Verifies that the spec.md file contains the required resolution text
in the specified locations (FR-001 and US-1 Acceptance Scenario 1).
"""
import pytest
from pathlib import Path
from code.utils.verify_spec import verify_spec

SPEC_PATH = Path("specs/001-predict-stiffness-cnn/spec.md")
REQUIRED_RESOLUTION = "128x128 pixels"

def test_spec_file_exists():
    """Ensure the spec file exists."""
    assert SPEC_PATH.exists(), f"Spec file not found at {SPEC_PATH}"

def test_fr_001_contains_resolution():
    """Verify FR-001 explicitly states 128x128 pixels."""
    content = SPEC_PATH.read_text(encoding="utf-8")
    fr_001_idx = content.find("FR-001")
    assert fr_001_idx != -1, "FR-001 not found in spec.md"
    
    context = content[fr_001_idx : fr_001_idx + 500]
    assert REQUIRED_RESOLUTION in context, \
        f"'{REQUIRED_RESOLUTION}' not found in FR-001 context"

def test_us_1_acceptance_scenario_contains_resolution():
    """Verify US-1 Acceptance Scenario 1 explicitly states 128x128 pixels."""
    content = SPEC_PATH.read_text(encoding="utf-8")
    us_1_idx = content.find("US-1")
    assert us_1_idx != -1, "US-1 not found in spec.md"
    
    us_1_context = content[us_1_idx:]
    scenario_marker = "Acceptance Scenario 1"
    scenario_idx = us_1_context.find(scenario_marker)
    
    # Fallback for alternative formatting
    if scenario_idx == -1:
        scenario_marker = "Acceptance Criteria 1"
        scenario_idx = us_1_context.find(scenario_marker)
    
    assert scenario_idx != -1, \
        "Acceptance Scenario 1 or Acceptance Criteria 1 not found in US-1"
    
    scenario_context = us_1_context[scenario_idx : scenario_idx + 500]
    assert REQUIRED_RESOLUTION in scenario_context, \
        f"'{REQUIRED_RESOLUTION}' not found in US-1 Acceptance Scenario context"

def test_verify_spec_script_returns_true():
    """Run the verification script's logic and ensure it returns True."""
    assert verify_spec(), "verify_spec() returned False. Spec resolution check failed."