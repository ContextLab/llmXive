import os
from pathlib import Path

def main():
    """
    Creates the 'outputs' directory at the project root if it does not already exist.
    This script is idempotent.
    """
    project_root = Path(__file__).resolve().parent.parent
    outputs_dir = project_root / "outputs"

    if not outputs_dir.exists():
        outputs_dir.mkdir(parents=True, exist_ok=True)
        print(f"Directory created: {outputs_dir}")
    else:
        print(f"Directory already exists: {outputs_dir}")

    # Ensure the directory is writable (optional check, but good practice)
    try:
        test_file = outputs_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        print(f"Warning: No write permission for {outputs_dir}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())