import os
import sys
from pathlib import Path

def create_directories():
    """Create the required project directory structure."""
    root = Path.cwd()
    dirs = [
        'code',
        'tests',
        'tests/unit',
        'tests/integration',
        'tests/contract',
        'data',
        'data/raw',
        'data/checkpoints',
        'data/results',
        'data/logs'
    ]
    
    created = []
    for d in dirs:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All directories already exist.")
    return created

def verify_structure():
    """Verify that all required directories exist."""
    root = Path.cwd()
    required = [
        'code', 'tests', 'data', 
        'data/raw', 'data/checkpoints', 'data/results', 'data/logs',
        'tests/unit', 'tests/integration', 'tests/contract'
    ]
    
    missing = []
    for d in required:
        if not (root / d).exists():
            missing.append(d)
    
    if missing:
        print(f"Missing directories: {', '.join(missing)}")
        return False
    print("Project structure verified successfully.")
    return True
