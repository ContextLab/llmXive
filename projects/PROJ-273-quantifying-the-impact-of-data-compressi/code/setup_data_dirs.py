import os
from pathlib import Path

def setup_data_directories():
    """
    Specifically creates the data directory hierarchy:
    data/raw, data/interim, data/processed, data/external.
    This is a helper for T006 but included here to satisfy T001 structure creation.
    """
    root = Path(__file__).parent.parent
    data_dirs = [
        "data/raw",
        "data/interim",
        "data/processed",
        "data/external"
    ]

    created = []
    for d in data_dirs:
        full_path = root / d
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path.relative_to(root)))
    
    # Ensure __init__.py for package consistency if needed, though data is usually not a package
    # We keep data as a plain directory structure as per standard ML/Data practices,
    # but if src/data is the package, data/ itself doesn't strictly need __init__.py
    # unless imported as a module. We'll leave data/ as plain dirs for storage.
    
    return created

if __name__ == "__main__":
    print("Setting up data directories...")
    dirs = setup_data_directories()
    print(f"Created data directories: {dirs}")