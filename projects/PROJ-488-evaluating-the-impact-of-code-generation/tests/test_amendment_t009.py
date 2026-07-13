import pytest
import yaml
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from amendment_prs import ensure_docs_directory, update_state_file, main as amendment_main
from state_tracker import load_state_file, STATE_FILE_PATH

class TestAmendmentT009:
    
    def test_docs_directory_creation(self, tmp_path):
        """Test that ensure_docs_directory creates the docs folder."""
        # Mock the global DOCS_DIR to use tmp_path
        import amendment_prs
        original_docs_dir = amendment_prs.DOCS_DIR
        amendment_prs.DOCS_DIR = tmp_path / "docs"
        
        result = ensure_docs_directory()
        
        assert result.exists()
        assert result.is_dir()
        assert result.name == "docs"
        
        # Restore original
        amendment_prs.DOCS_DIR = original_docs_dir

    def test_amendment_vi_file_exists(self):
        """Test that the docs/amendment-vi.md file exists and contains required sections."""
        docs_dir = Path(__file__).parent.parent / "docs"
        amendment_file = docs_dir / "amendment-vi.md"
        
        assert amendment_file.exists(), "docs/amendment-vi.md must exist for T009"
        
        content = amendment_file.read_text()
        
        # Check for required sections
        assert "Proposed Text Modification" in content, "Missing Proposed Text Modification section"
        assert "Justification" in content, "Missing Justification section"
        assert "Impact Analysis" in content, "Missing Impact Analysis section"
        assert "CodeParrot/CodeGen" in content, "Must mention CodeParrot/CodeGen"
        assert "n≥1000" in content or "n>=1000" in content, "Must mention sample size requirement"
        assert "statistical power" in content, "Must mention statistical power"

    def test_state_file_update(self):
        """Test that update_state_file correctly updates the amendment status."""
        # We assume the state file exists or is created by the function
        # For this test, we just verify the function doesn't crash and updates the file
        try:
            update_state_file("T009", "draft", pr_url="https://example.com/pr/123")
            
            # Verify the file was updated
            assert STATE_FILE_PATH.exists(), "State file should be created/updated"
            
            state = load_state_file()
            assert "amendment_status" in state, "State must have amendment_status key"
            assert "T009" in state["amendment_status"], "T009 must be in amendment_status"
            assert state["amendment_status"]["T009"]["status"] == "draft"
            assert state["amendment_status"]["T009"]["pr_url"] == "https://example.com/pr/123"
            
        except Exception as e:
            pytest.fail(f"update_state_file failed: {e}")

    def test_main_entry_point(self, capsys):
        """Test that main() runs without error."""
        amendment_main()
        captured = capsys.readouterr()
        assert "Amendment PR Management System" in captured.out

if __name__ == "__main__":
    pytest.main([__file__, "-v"])