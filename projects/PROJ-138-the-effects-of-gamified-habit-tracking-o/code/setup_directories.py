import os
import sys
from pathlib import Path

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/consent",
    "code/data",
    "code/analysis",
    "code/reports",
    "code/utils",
    "code/tests"
]

def create_directories():
    """Create all required directories and .gitkeep files."""
    root = Path(".")
    created_count = 0
    
    for dir_path in REQUIRED_DIRS:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            created_count += 1
        
        print(f"Created/Verified: {full_path}")
    
    print(f"\nDirectory setup complete. Created {created_count} new .gitkeep files.")
    return True

def verify_structure():
    """Verify all required directories exist."""
    root = Path(".")
    missing = []
    
    for dir_path in REQUIRED_DIRS:
        full_path = root / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
        elif not (full_path / ".gitkeep").exists():
            missing.append(f"{full_path}/.gitkeep")
    
    if missing:
        print("Verification FAILED. Missing:")
        for item in missing:
            print(f"  - {item}")
        return False
    
    print("Verification PASSED. All directories and .gitkeep files exist.")
    return True

def main():
    """Main entry point for directory setup."""
    print("=== Setting up Project Directory Structure ===\n")
    
    if not create_directories():
        sys.exit(1)
    
    if not verify_structure():
        sys.exit(1)
    
    print("\n=== Setup Complete ===")

if __name__ == "__main__":
    main()