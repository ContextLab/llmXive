import os
from pathlib import Path

def main():
    """
    Create the source directory structure for the llmXive project.
    Creates: src/generators, src/inference, src/analysis
    """
    base_dir = Path(__file__).resolve().parent.parent
    src_dir = base_dir / "src"
    
    # Define required subdirectories
    subdirs = [
        "generators",
        "inference",
        "analysis"
    ]
    
    created_dirs = []
    for subdir in subdirs:
        target_path = src_dir / subdir
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            # Create __init__.py to make them proper Python packages
            init_file = target_path / "__init__.py"
            init_file.touch()
            created_dirs.append(str(target_path.relative_to(base_dir)))
        else:
            created_dirs.append(str(target_path.relative_to(base_dir)))
    
    print(f"Source directory structure created/verified:")
    for d in created_dirs:
        print(f"  - {d}")
    
    # Verify all directories exist
    for subdir in subdirs:
        target_path = src_dir / subdir
        if not target_path.exists() or not target_path.is_dir():
            raise RuntimeError(f"Failed to create directory: {target_path}")
    
    return 0

if __name__ == "__main__":
    exit(main())
