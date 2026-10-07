import os
from pathlib import Path

def ensure_dir(dir_path: Path) -> None:
    """Ensure directory exists."""
    dir_path.mkdir(parents=True, exist_ok=True)

def main():
    """Entry point for ingestion utils script."""
    pass

if __name__ == "__main__":
    main()