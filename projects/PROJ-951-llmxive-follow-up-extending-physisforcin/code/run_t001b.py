import os
import sys
from pathlib import Path

from create_t001b_directories import create_t001b_directories
from verify_t001b_structure import verify_t001b_structure

def main() -> int:
    """
    Execute T001b: Create subdirectories and verify structure.
    
    Returns:
        0 on success, 1 on failure
    """
    # Determine project root
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent  # projects/PROJ-951-llmxive-follow-up-extending-physisforcin/
    
    print(f"Project root: {project_root}")
    print("=" * 60)
    print("T001b: Creating directory structure...")
    print("=" * 60)
    
    # Step 1: Create directories
    created_count = create_t001b_directories(str(project_root))
    
    print()
    print("=" * 60)
    print("T001b: Verifying directory structure...")
    print("=" * 60)
    
    # Step 2: Verify structure
    is_valid, missing_dirs = verify_t001b_structure(str(project_root))
    
    if is_valid:
        print("\n✓ SUCCESS: All required directories exist.")
        print(f"  Created {created_count} new directories.")
        return 0
    else:
        print(f"\n✗ FAILURE: Missing directories: {missing_dirs}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
