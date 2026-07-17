import os
import sys
from pathlib import Path

def create_directory_structure(base_path: str = None) -> list[str]:
    """
    Create the directory structure required for the specs contracts.
    
    Specifically creates:
    - specs/001-llmxive-followup/contracts/
    
    Args:
        base_path: Optional base path. If None, uses current working directory.
        
    Returns:
        List of created directory paths as strings.
    """
    if base_path is None:
        base_path = os.getcwd()
    
    base = Path(base_path)
    target_dir = base / "specs" / "001-llmxive-followup" / "contracts"
    
    created_dirs = []
    
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(target_dir))
    
    return created_dirs

def main():
    """Main entry point for creating the specs contracts directory."""
    print("Creating specs contracts directory structure...")
    created = create_directory_structure()
    
    if created:
        for d in created:
            print(f"Created: {d}")
    else:
        print("Directory structure already exists.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())