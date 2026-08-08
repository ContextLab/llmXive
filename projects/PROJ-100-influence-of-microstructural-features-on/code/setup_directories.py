import os
import sys
from typing import List

# Define all required directories relative to project root
DIRECTORIES = [
    "code",
    "data/raw",
    "data/processed",
    "results",
    "results/plots",
]

def ensure_directories() -> List[str]:
    """
    Create all required project directories if they do not exist.
    
    Returns:
        List[str]: List of directory paths that were created or verified.
    """
    created_or_verified = []
    for dir_path in DIRECTORIES:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            created_or_verified.append(dir_path)
        else:
            created_or_verified.append(dir_path)
    return created_or_verified

if __name__ == "__main__":
    print("Ensuring project directory structure...")
    dirs = ensure_directories()
    print(f"Verified/created directories: {dirs}")