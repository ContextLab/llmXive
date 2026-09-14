import os
import sys
from pathlib import Path
from datetime import datetime

def create_directory_structure():
    """Creates the project directory structure."""
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "artifacts",
        "artifacts/models",
        "artifacts/plots",
        "artifacts/reports",
        "logs",
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def write_setup_log():
    """Writes a success confirmation message with timestamp to logs/setup.log."""
    log_file_path = Path("logs/setup.log")
    with open(log_file_path, "w") as f:
        f.write(f"Project setup completed successfully at {datetime.now()}\n")

def main():
    create_directory_structure()
    write_setup_log()

if __name__ == "__main__":
    main()
