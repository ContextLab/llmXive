"""
Script to create the project test directory structure.
Creates:
  - code/tests/
  - code/tests/contract/
  - code/tests/integration/
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the required test directory structure."""
    # Determine the project root relative to this script
    script_dir = Path(__file__).parent
    project_root = script_dir / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"
    
    test_base = project_root / "tests"
    test_contract = test_base / "contract"
    test_integration = test_base / "integration"
    
    directories = [test_base, test_contract, test_integration]
    
    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(project_root)))
            print(f"Created directory: {directory.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {directory.relative_to(project_root)}")
    
    # Create __init__.py files to make them packages
    for directory in directories:
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Test package\n")
            print(f"Created __init__.py in: {directory.relative_to(project_root)}")
        
    return created

def verify_structure():
    """Verify that all required directories exist."""
    script_dir = Path(__file__).parent
    project_root = script_dir / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"
    
    test_base = project_root / "tests"
    test_contract = test_base / "contract"
    test_integration = test_base / "integration"
    
    required = [test_base, test_contract, test_integration]
    all_exist = True
    
    for directory in required:
        if not directory.exists():
            print(f"MISSING: {directory.relative_to(project_root)}")
            all_exist = False
        else:
            print(f"OK: {directory.relative_to(project_root)}")
    
    return all_exist

def main():
    """Main entry point."""
    print("Creating test directory structure...")
    created = create_directories()
    
    print("\nVerifying structure...")
    if verify_structure():
        print("\n✓ All directories created and verified successfully.")
        return 0
    else:
        print("\n✗ Verification failed. Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
