import os
import sys
from pathlib import Path

def create_logs_directory():
    """Create logs directory and init."""
    Path('logs').mkdir(parents=True, exist_ok=True)
    Path('logs/archive').mkdir(parents=True, exist_ok=True)
    (Path('logs') / '__init__.py').touch(exist_ok=True)
    (Path('logs/archive') / '__init__.py').touch(exist_ok=True)
    print("Logs directories created.")

def main():
    create_logs_directory()

if __name__ == "__main__":
    main()
