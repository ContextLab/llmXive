import os
from pathlib import Path

def setup_directories():
    """
    Helper function to setup directories. 
    Called by setup_project_structure.py or directly.
    """
    project_name = "PROJ-118-investigating-the-neural-correlates-of-p"
    base_path = Path(project_name)
    base_path.mkdir(exist_ok=True)
    
    dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results"
    ]
    
    for d in dirs:
        (base_path / d).mkdir(parents=True, exist_ok=True)
        
    return base_path