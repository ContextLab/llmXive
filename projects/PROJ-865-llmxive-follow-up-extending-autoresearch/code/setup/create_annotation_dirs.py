import os
import sys
from pathlib import Path

def main():
    """
    Creates the directory structure for the annotation and distillation phase.
    Specifically creates `code/02_annotation_distillation/`.
    """
    root = Path.cwd()
    target_dir = root / "code" / "02_annotation_distillation"
    
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {target_dir}")
    else:
        print(f"Directory already exists: {target_dir}")
    
    # Ensure the directory is writable and exists
    if not target_dir.is_dir():
        print(f"ERROR: Failed to create or verify directory: {target_dir}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()