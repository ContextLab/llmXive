"""
Utility script to create a dummy file for testing the state manager.
"""

import os
from pathlib import Path

def main():
    """Create a dummy text file in data/raw/ for hashing tests."""
    data_raw_dir = Path("data/raw")
    data_raw_dir.mkdir(parents=True, exist_ok=True)

    dummy_file = data_raw_dir / "dummy.txt"
    content = "This is a dummy file created for state manager testing.\n"
    content += "It contains simple text to generate a reproducible hash.\n"

    with open(dummy_file, "w") as f:
        f.write(content)

    print(f"Created dummy file: {dummy_file}")
    print(f"Content:\n{content}")

if __name__ == "__main__":
    main()