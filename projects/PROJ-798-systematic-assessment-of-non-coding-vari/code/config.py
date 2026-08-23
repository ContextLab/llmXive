"""
Configuration module for the project.
"""
import os
from pathlib import Path

def ensure_data_dirs():
    """
    Ensure all required data directories exist.
    Creates: code/, data/raw/, data/derived/, tests/
    """
    base_dir = Path(__file__).parent.parent
    directories = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "derived",
        base_dir / "tests",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "integration",
        base_dir / "tests" / "contract",
        base_dir / "figures",
        base_dir / "specs" / "001-gene-regulation" / "contracts"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep in data directories to ensure they are tracked
        if "data" in str(directory):
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
    
    return True

# Configuration constants
RANDOM_SEED = 42
MAF_THRESHOLD = 0.01
DEFAULT_WINDOW = 100  # Fallback only, actual window derived from PWM length
