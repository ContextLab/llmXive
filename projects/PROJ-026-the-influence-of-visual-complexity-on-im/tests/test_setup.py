import os
from pathlib import Path
import sys

# Add parent directory to path to allow imports if run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_project_root

def test_directory_structure_exists():
    """
    Verify that T001 created the required directory tree:
    code/, data/raw/stimuli, data/raw/responses, data/processed, data/results, tests/
    """
    root = get_project_root()
    
    required_dirs = [
        "code",
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results",
        "tests"
    ]
    
    missing = []
    for rel_path in required_dirs:
        full_path = root / rel_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(rel_path)
    
    if missing:
        raise AssertionError(f"Required directories missing: {missing}")
    
    # Also verify that the nested structure is correct
    assert (root / "data" / "raw" / "stimuli").exists()
    assert (root / "data" / "raw" / "responses").exists()
    assert (root / "data" / "processed").exists()
    assert (root / "data" / "results").exists()

if __name__ == "__main__":
    test_directory_structure_exists()
    print("Directory structure verification passed.")
