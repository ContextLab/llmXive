"""
Unit tests for T036: Spec update for R² threshold.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from code.spec_update_t036 import update_spec_md
import re

# Note: We cannot easily test the actual file modification on the live spec
# without modifying the repository state in the test environment.
# Instead, we test the logic with a temporary file.

@pytest.fixture
def temp_spec_file():
    """Create a temporary spec file with the old R² threshold."""
    temp_dir = tempfile.mkdtemp()
    spec_path = Path(temp_dir) / "spec.md"
    
    # Create a mock spec content with FR-008 and R² threshold = 0.99
    content = """
    # Specification Document

    ## FR-008: Linearity Validation

    The Mean Squared Displacement (MSD) trajectory must exhibit linear behavior
    to ensure the validity of the diffusion coefficient calculation.
    
    Requirement: R² threshold = 0.99
    
    ## Other Sections
    
    Some other text with 0.99 that should NOT be changed if possible,
    but the regex is specific to R² threshold.
    """
    spec_path.write_text(content)
    yield spec_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_update_spec_r2_threshold(temp_spec_file):
    """Test that the R² threshold is updated from 0.99 to 0.95."""
    # Temporarily patch the SPEC_PATH constant in the module
    import code.spec_update_t036 as module
    original_spec_path = module.SPEC_PATH
    module.SPEC_PATH = temp_spec_file

    try:
        success = update_spec_md()
        assert success, "update_spec_md should return True"

        content = temp_spec_file.read_text()
        # Check that 0.99 is gone from the R² context
        assert "R² threshold = 0.95" in content or "R^2 threshold = 0.95" in content
        # Check that 0.99 is not in the R² context anymore
        # We use a negative lookahead/lookbehind or simple check
        assert not re.search(r'R[²^2]\s*threshold\s*[=:]\s*0\.99', content, re.IGNORECASE)
        
        # Verify other 0.99 values (if any) might remain, but the specific one is changed.
        # In our mock, there is another 0.99. The regex is specific, so it should remain.
        assert "0.99" in content # The other 0.99 should remain
        
    finally:
        module.SPEC_PATH = original_spec_path

def test_update_spec_no_change_if_not_found():
    """Test behavior when the pattern is not found."""
    temp_dir = tempfile.mkdtemp()
    spec_path = Path(temp_dir) / "spec.md"
    spec_path.write_text("No R² threshold here, just 0.99.")
    
    import code.spec_update_t036 as module
    original_spec_path = module.SPEC_PATH
    module.SPEC_PATH = spec_path

    try:
        success = update_spec_md()
        assert not success, "update_spec_md should return False if pattern not found"
        
        content = spec_path.read_text()
        assert "0.99" in content # Should remain unchanged
    finally:
        module.SPEC_PATH = original_spec_path
        shutil.rmtree(temp_dir)