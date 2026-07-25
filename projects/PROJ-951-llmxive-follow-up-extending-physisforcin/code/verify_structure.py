import os
from pathlib import Path

def verify_structure(base_path: str) -> bool:
    """
    Verifies that the required directory structure exists.
    
    Args:
        base_path: The root directory to verify.
        
    Returns:
        True if all required directories exist, False otherwise.
    """
    base = Path(base_path)
    required_dirs = [
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation",
        "src/generation",
        "src/filtering",
        "src/training",
        "src/evaluation",
        "src/utils",
        "tests/unit",
        "tests/integration"
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = base / dir_path
        if not full_path.is_dir():
            missing.append(dir_path)
    
    if missing:
        print(f"Missing directories: {missing}")
        return False
    
    print("All required directories exist.")
    return True

if __name__ == "__main__":
    project_root = Path(__file__).parent
    success = verify_structure(project_root)
    exit(0 if success else 1)