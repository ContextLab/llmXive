"""
Unit test for SC-006 draft presence.
Verifies that the specification amendment draft file exists.
"""
import os
import pytest
from pathlib import Path


def test_spec_amendment_draft_present():
    """
    Asserts that `spec_amendment_draft.md` exists in the project root.
    This file is required for the SC-006 (dataset count limitation) kickback.
    """
    project_root = Path(__file__).parent.parent.parent
    draft_path = project_root / "spec_amendment_draft.md"
    
    assert draft_path.exists(), (
        f"Specification amendment draft not found at {draft_path}. "
        "This file is required to document the SC-006 dataset count limitation "
        "and FR-007/FR-008 amendments."
    )

    # Verify the file is not empty
    assert draft_path.stat().st_size > 0, (
        f"Specification amendment draft at {draft_path} is empty. "
        "It must contain the proposed text for SC-006, FR-007, and FR-008."
    )