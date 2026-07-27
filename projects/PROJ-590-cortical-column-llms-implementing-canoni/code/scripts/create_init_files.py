"""
Script to ensure all __init__.py files exist in src/ and tests/ directories.
This is a safety script; the files are also created as artifacts in T001b.
"""
import os
from pathlib import Path

def ensure_init_files(base_path: Path, dirs: list[str]):
    for d in dirs:
        target_dir = base_path / d
        target_dir.mkdir(parents=True, exist_ok=True)
        init_file = target_dir / "__init__.py"
        if not init_file.exists():
          # Minimal docstring
          init_file.write_text(f'"""{d}."""\n')
          print(f"Created {init_file}")
        else:
          print(f"Already exists: {init_file}")

def main():
    # Determine project root (assuming script is in code/scripts/)
    # We look for 'code' directory up the tree or assume current dir is code/
    current = Path(__file__).resolve()
    code_root = current.parent
    
    # If running from root, adjust
    if not (code_root / "src").exists():
        if (current.parent.parent / "src").exists():
            code_root = current.parent.parent
        else:
            # Fallback: assume current dir is project root
            code_root = current.parent
    
    src_dirs = [
        "src", "src/data", "src/models", "src/training", "src/experiments", "src/utils",
        "tests", "tests/unit", "tests/integration"
    ]
    
    print(f"Ensuring __init__.py in: {code_root}")
    ensure_init_files(code_root, src_dirs)
    print("Done.")

if __name__ == "__main__":
    main()