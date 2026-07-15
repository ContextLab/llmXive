"""Script to initialize all required project directories."""
import os
from pathlib import Path

def main():
    """Create all required directories for the project."""
    # Data directories
    data_raw = Path("data/raw")
    data_processed = Path("data/processed")
    
    # Code directories
    code_dataset = Path("code/dataset")
    code_agent = Path("code/agent")
    code_analysis = Path("code/analysis")
    
    # Test directories
    tests_unit = Path("tests/unit")
    tests_integration = Path("tests/integration")
    
    # Initialize __init__.py files for Python packages
    init_files = [
        tests_unit / "__init__.py",
        tests_integration / "__init__.py",
    ]
    
    for dir_path in [
        data_raw, data_processed,
        code_dataset, code_agent, code_analysis,
        tests_unit, tests_integration
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    for init_file in init_files:
        init_file.touch(exist_ok=True)
        print(f"Created package marker: {init_file}")

if __name__ == "__main__":
    main()
