import os
from pathlib import Path

def main():
    """
    Execute Test Directory Creation:
    Run `mkdir -p tests/unit tests/integration`.
    
    Creates the required directory structure for unit and integration tests
    relative to the project root.
    """
    # Determine project root (assuming script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    
    test_base = project_root / "tests"
    unit_dir = test_base / "unit"
    integration_dir = test_base / "integration"
    
    # Create directories if they don't exist
    unit_dir.mkdir(parents=True, exist_ok=True)
    integration_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created directory: {unit_dir}")
    print(f"Created directory: {integration_dir}")
    
    # Verify creation
    if unit_dir.exists() and unit_dir.is_dir():
        print(f"Verified: {unit_dir} exists")
    else:
        raise RuntimeError(f"Failed to create {unit_dir}")
        
    if integration_dir.exists() and integration_dir.is_dir():
        print(f"Verified: {integration_dir} exists")
    else:
        raise RuntimeError(f"Failed to create {integration_dir}")

if __name__ == "__main__":
    main()