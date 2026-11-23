import os
from pathlib import Path

def setup_directories():
    """
    Creates the required project directory structure for llmXive.
    Specifically creates the 'code/' directory as per task T001a.
    Also creates other foundational directories to ensure the project tree is valid.
    """
    root = Path(".")
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results/plots",
        "results/reports",
        "tests/unit",
        "tests/integration",
        "specs"
    ]
    
    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {full_path}")
    
    # Log creation for verification
    if created:
        print(f"Created directories: {created}")
    else:
        print("All required directories already exist.")
    
    return created

if __name__ == "__main__":
    setup_directories()
