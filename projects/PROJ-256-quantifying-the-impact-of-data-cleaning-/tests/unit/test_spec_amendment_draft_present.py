"""
Unit test to verify the existence of the specification amendment draft.
This test ensures that the required artifact for T1106 is present.
"""
import os
from pathlib import Path

def test_spec_amendment_draft_exists():
    """
    Verify that the spec_amendment_draft.md file exists in the expected location.
    """
    # Define the expected path relative to the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    draft_path = project_root / "specs" / "001-quantifying-the-impact-of-data-cleaning" / "spec_amendment_draft.md"
    
    assert draft_path.exists(), f"Specification amendment draft not found at: {draft_path}"
    
    # Additional check: ensure the file is not empty
    assert draft_path.stat().st_size > 0, "Specification amendment draft is empty."

def test_spec_amendment_draft_content():
    """
    Verify that the spec_amendment_draft.md contains the required sections.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    draft_path = project_root / "specs" / "001-quantifying-the-impact-of-data-cleaning" / "spec_amendment_draft.md"
    
    assert draft_path.exists(), "Specification amendment draft file missing."
    
    content = draft_path.read_text()
    
    # Check for required sections based on the task requirements
    required_sections = [
        "Revised Success Criteria",
        "Deviation from Functional Requirement FR-001",
        "Functional Requirement FR-007",
        "Functional Requirement FR-008",
        "Updated Success Criteria"
    ]
    
    for section in required_sections:
        assert section in content, f"Missing required section: {section}"

if __name__ == "__main__":
    test_spec_amendment_draft_exists()
    test_spec_amendment_draft_content()
    print("All tests passed.")