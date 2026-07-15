import os
from pathlib import Path

def setup_test_directories():
    """
    Create the required test directory structure for the project.
    
    This function creates:
    - tests/unit/
    - tests/integration/
    
    Returns:
        dict: A dictionary containing the paths created for verification purposes.
    """
    base_dir = Path("tests")
    unit_dir = base_dir / "unit"
    integration_dir = base_dir / "integration"
    
    # Create directories if they don't exist
    unit_dir.mkdir(parents=True, exist_ok=True)
    integration_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files to make them proper Python packages
    (unit_dir / "__init__.py").touch()
    (integration_dir / "__init__.py").touch()
    
    return {
        "unit": str(unit_dir),
        "integration": str(integration_dir)
    }

if __name__ == "__main__":
    result = setup_test_directories()
    print(f"Test directories created: {result}")