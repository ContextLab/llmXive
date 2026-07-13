import os
import yaml
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from amendment_prs import (
    load_state_file,
    save_state_file,
    update_state_file,
    ensure_docs_directory,
    STATE_FILE_PATH
)

def test_update_state_file():
    """Test that update_state_file correctly writes PR URLs to the state YAML."""
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    original_state_dir = Path(__file__).parent.parent.parent / "state" / "projects"
    
    # Backup original state if it exists
    original_state_file = original_state_dir / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"
    backup_exists = original_state_file.exists()
    backup_content = None
    if backup_exists:
        with open(original_state_file, 'r') as f:
            backup_content = f.read()

    try:
        # Point to temp directory
        test_state_dir = Path(temp_dir) / "state" / "projects"
        test_state_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the global path (this is a bit hacky for testing without refactoring)
        # In a real scenario, we'd pass the path as an argument
        # For this test, we assume the function uses the global path, 
        # so we temporarily move the file or use a different approach.
        # Instead, let's just verify the logic by reading the file after writing.
        
        # We will manually test the logic by creating a temp file and using the functions
        # But since the functions use global constants, we need to be careful.
        # Let's assume the environment allows us to run this against the actual file.
        
        # To be safe and isolated, we will just verify the structure of the update
        # by checking the file content after the update.
        
        # For this specific task, we assume the state file is writable.
        # We will update with dummy URLs and verify they are there.
        
        test_urls = {
            "vi": "https://github.com/test/pr/1",
            "vii": "https://github.com/test/pr/2"
        }
        
        update_state_file(test_urls, status="pending")
        
        # Read back and verify
        state = load_state_file()
        
        assert "amendment_status" in state, "amendment_status key missing"
        assert "vi" in state["amendment_status"], "amendment vi missing"
        assert "vii" in state["amendment_status"], "amendment vii missing"
        
        assert state["amendment_status"]["vi"]["url"] == test_urls["vi"]
        assert state["amendment_status"]["vii"]["url"] == test_urls["vii"]
        assert state["amendment_status"]["vi"]["status"] == "pending"
        assert "updated_at" in state["amendment_status"]["vi"]
        
        print("Test passed: State file updated correctly.")
        
    finally:
        # Restore original state if it existed
        if backup_exists:
            with open(original_state_file, 'w') as f:
                f.write(backup_content)
        else:
            if original_state_file.exists():
                original_state_file.unlink()
        
        # Cleanup temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_update_state_file()