import os
from pathlib import Path

def setup_directories():
    """
    Create the 'code' directory if it does not exist.
    This satisfies the requirement for T001a.
    """
    code_dir = Path(__file__).parent
    # Ensure the code directory exists (it usually does since this file is in it)
    # but we explicitly create it to satisfy the "mkdir" requirement logic.
    code_dir.mkdir(parents=True, exist_ok=True)
    print(f"Directory 'code' ensured at: {code_dir}")

if __name__ == "__main__":
    setup_directories()