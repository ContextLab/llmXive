"""
Tests for the Governance Compliance Checker (Task T000).
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from governance_checker import check_constitution_amendment, GOVERNANCE_ERROR_MSG

class TestGovernanceChecker:
    def test_missing_constitution_returns_false(self, monkeypatch, tmp_path):
        """Test that missing constitution file returns False."""
        # Temporarily change the path used by the module
        # Since the path is global in the module, we need to mock the file existence check
        # or rely on the function's internal logic.
        # The function checks CONSTITUTION_PATH.exists().
        # We can't easily change the global CONSTITUTION_PATH in the module without reloading.
        # Instead, we test the logic by creating a temp dir and ensuring the check fails.
        
        # Mock the path to a non-existent file in a temp directory
        original_path = Path("specs/constitution.md")
        # We can't easily patch the global constant in the imported module without reloading the module.
        # For this test, we assume the default path behavior.
        # If the file doesn't exist in the real repo structure during test, it returns False.
        # To be robust, we rely on the function's behavior: if file missing -> False.
        
        # Simulate missing file by ensuring the specific path doesn't exist
        # This test assumes the test environment doesn't have specs/constitution.md at root
        # If it does, this test might be skipped or need a mock.
        # A better approach: patch the module's CONSTITUTION_PATH.
        
        import governance_checker
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_path = Path(tmpdir) / "non_existent.md"
            original_const_path = governance_checker.CONSTITUTION_PATH
            
            # Patch the global constant
            governance_checker.CONSTITUTION_PATH = mock_path
            
            try:
                result = check_constitution_amendment()
                assert result is False
            finally:
                # Restore original path
                governance_checker.CONSTITUTION_PATH = original_const_path

    def test_amended_constitution_returns_true(self, monkeypatch, tmp_path):
        """Test that an amended constitution returns True."""
        import governance_checker
        
        # Create a mock constitution content that indicates amendment
        amended_content = f"""
        # Constitution of llmXive
        
        ## Principle VII
        {AMENDMENT_MARKER}: This principle has been updated to align with Spec FR-001.
        The model is now CodeLlama-7B.
        """
        
        mock_file = tmp_path / "constitution.md"
        mock_file.write_text(amended_content)
        
        original_path = governance_checker.CONSTITUTION_PATH
        governance_checker.CONSTITUTION_PATH = mock_file
        
        try:
            result = check_constitution_amendment()
            assert result is True
        finally:
            governance_checker.CONSTITUTION_PATH = original_path

    def test_unamended_constitution_returns_false(self, monkeypatch, tmp_path):
        """Test that an unamended constitution returns False."""
        import governance_checker
        
        # Create a mock constitution content WITHOUT the amendment
        unamended_content = f"""
        # Constitution of llmXive
        
        ## Principle VII
        The standard model is StarCoder-15B.
        """
        
        mock_file = tmp_path / "constitution.md"
        mock_file.write_text(unamended_content)
        
        original_path = governance_checker.CONSTITUTION_PATH
        governance_checker.CONSTITUTION_PATH = mock_file
        
        try:
            result = check_constitution_amendment()
            assert result is False
        finally:
            governance_checker.CONSTITUTION_PATH = original_path

    def test_error_message_content(self):
        """Verify the error message is specific."""
        assert "StarCoder-15B" in GOVERNANCE_ERROR_MSG
        assert "CodeLlama-7B" in GOVERNANCE_ERROR_MSG
        assert "Constitution not amended" in GOVERNANCE_ERROR_MSG
