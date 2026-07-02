import os
from pathlib import Path

def ensure_dirs():
    """Create required project directories if they don't exist."""
    base_dir = Path(__file__).parent.parent
    dirs = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "tests",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "integration",
        base_dir / "tests" / "contract",
        base_dir / "specs" / "001-predict-sn1-rate-constants" / "contracts",
        base_dir / "artifacts",
        base_dir / "figures",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs
