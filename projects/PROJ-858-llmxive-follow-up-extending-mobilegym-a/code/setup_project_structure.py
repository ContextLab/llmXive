import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the llmXive pipeline.
    
    Directories created:
    - code/, code/scheduler/, code/training/, code/analysis/, code/utils/
    - data/raw/, data/processed/, data/validation/
    - tests/unit/, tests/integration/
    - contracts/
    """
    base_dir = Path.cwd()
    
    directories = [
        # Code structure
        base_dir / "code",
        base_dir / "code" / "scheduler",
        base_dir / "code" / "training",
        base_dir / "code" / "analysis",
        base_dir / "code" / "utils",
        
        # Data structure
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "validation",
        
        # Test structure
        base_dir / "tests" / "unit",
        base_dir / "tests" / "integration",
        
        # Contracts
        base_dir / "contracts",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory.relative_to(base_dir)}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory.relative_to(base_dir)}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for the script."""
    try:
        create_directories()
        return 0
    except Exception as e:
        print(f"Error creating project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
