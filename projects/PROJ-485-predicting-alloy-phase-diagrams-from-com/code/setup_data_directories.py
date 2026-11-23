import os

def create_directories():
    """Create the required data and artifact directories."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/artifacts",
        "data/artifacts/plots",
        "data/logs",
        "state/PROJ-485"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
