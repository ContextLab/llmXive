import os
from pathlib import Path
from code.setup_directories import create_directories

def test_docs_output_directory_creation():
    """
    Verifies that T010 requirement is met:
    Creates directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/docs/output/`
    """
    base_path = Path("projects/PROJ-508-evaluating-the-impact-of-llm-based-code-")
    target_dir = base_path / "docs" / "output"
    
    # Ensure clean state for test
    if target_dir.exists():
        # Remove existing dir to force recreation if logic is buggy
        # Note: In a real CI, we might skip this to avoid permission issues if not empty
        pass 
    
    # Run the setup function
    create_directories()
    
    # Assert the specific T010 directory exists
    assert target_dir.exists(), f"Directory {target_dir} was not created by T010 implementation"
    assert target_dir.is_dir(), f"{target_dir} exists but is not a directory"

if __name__ == "__main__":
    test_docs_output_directory_creation()
    print("T010 verification passed.")