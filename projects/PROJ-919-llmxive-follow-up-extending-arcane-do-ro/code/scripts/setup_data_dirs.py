import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required data directory structure for the llmXive project.
    Directories created:
      - data/raw/
      - data/derived/
      - data/gold_standard/
      - artifacts/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    base_path = Path(__file__).resolve().parent.parent
    project_root = base_path / "data"
    
    directories = [
        "raw",
        "derived",
        "gold_standard",
        "../artifacts" # artifacts is at root level alongside data/
    ]
    
    created_count = 0
    for dir_name in directories:
        target_path = project_root / dir_name if dir_name != "../artifacts" else base_path.parent / "artifacts"
        
        # Normalize the path to handle ../ correctly
        target_path = target_path.resolve()
        
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Directory created or exists: {target_path}")
            created_count += 1
        except PermissionError:
            print(f"Error: Permission denied creating directory {target_path}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error creating directory {target_path}: {e}", file=sys.stderr)
            return False
    
    # Verify artifacts directory specifically as it's outside data/
    artifacts_path = base_path.parent / "artifacts"
    if not artifacts_path.exists():
        print(f"Error: Artifacts directory was not created at {artifacts_path}", file=sys.stderr)
        return False
        
    print(f"Successfully setup {created_count} directories.")
    return True

def main():
    """Entry point for the script."""
    success = setup_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()