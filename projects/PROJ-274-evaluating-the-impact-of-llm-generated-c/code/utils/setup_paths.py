import os
import sys
from pathlib import Path

def ensure_project_dirs():
    """
    Ensure all required project directories exist.
    Called by various scripts to guarantee paths are ready.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    dirs = [
        project_root / 'code',
        project_root / 'data',
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed',
        project_root / 'data' / 'reports',
        project_root / 'tests',
        project_root / 'tests' / 'unit',
        project_root / 'tests' / 'integration',
        project_root / 'tests' / 'contract',
        project_root / 'specs',
        project_root / 'state',
        project_root / 'config',
        project_root / 'contracts'
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    return str(project_root)

if __name__ == "__main__":
    root = ensure_project_dirs()
    print(f"Project directories ensured at: {root}")
