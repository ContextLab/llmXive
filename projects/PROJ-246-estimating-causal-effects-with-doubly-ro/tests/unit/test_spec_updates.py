import re
from pathlib import Path

def test_feature_branch_name_matches_folder():
    # Resolve the spec file path relative to this test file
    spec_path = Path(__file__).resolve().parents[2] / "specs" / "001-estimating-causal-effects-with-doubly-ro" / "spec.md"
    assert spec_path.is_file(), f"Spec file not found at {spec_path}"

    content = spec_path.read_text(encoding="utf-8")

    # Extract the feature branch value
    match = re.search(r"\*\*Feature Branch\*\*:\s*`([^`]+)`", content)
    assert match, "Feature Branch line not found in spec.md"
    branch_name = match.group(1).strip()

    # Expected branch name is the folder name
    expected_branch = "001-estimating-causal-effects-with-doubly-ro"
    assert branch_name == expected_branch, f"Feature branch '{branch_name}' does not match expected '{expected_branch}'"

def test_acceptance_contains_analytically_computed():
    spec_path = Path(__file__).resolve().parents[2] / "specs" / "001-estimating-causal-effects-with-doubly-ro" / "spec.md"
    content = spec_path.read_text(encoding="utf-8")
    # Check that the acceptance scenario includes the phrase "analytically computed"
    assert "analytically computed" in content, (
        "Acceptance scenario does not contain the required phrase 'analytically computed'"
    )