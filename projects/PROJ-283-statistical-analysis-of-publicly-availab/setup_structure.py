import os
from pathlib import Path

def create_project_structure():
    """Create the full project directory structure and __init__.py files."""
    root = Path.cwd()
    
    # Define all directories to create
    directories = [
        "src",
        "src/data",
        "src/data/raw",
        "src/data/processed",
        "src/data/results",
        "src/models",
        "src/reports",
        "src/validation",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
        "specs/contracts",
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py files in all src and tests subdirectories
    init_dirs = [
        "src",
        "src/data",
        "src/data/raw",
        "src/data/processed",
        "src/data/results",
        "src/models",
        "src/reports",
        "src/validation",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
        "specs/contracts",
    ]
    
    for dir_path in init_dirs:
        init_file = root / dir_path / "__init__.py"
        if not init_file.exists():
          # Determine content based on directory type
          content = "# Auto-generated init file\n"
          if "src" in dir_path:
              if "data" in dir_path:
                  content = "# Data ingestion and processing modules\n"
              elif "models" in dir_path:
                  content = "# Modeling and machine learning modules\n"
              elif "reports" in dir_path:
                  content = "# Reporting and visualization modules\n"
              elif "validation" in dir_path:
                  content = "# Validation and contract checking modules\n"
              else:
                  content = "# llmXive Statistical Analysis of Publicly Available Chess Game Data\n"
          elif "tests" in dir_path:
              if "contract" in dir_path:
                  content = "# Contract validation tests\n"
              elif "unit" in dir_path:
                  content = "# Unit tests\n"
              elif "integration" in dir_path:
                  content = "# Integration tests\n"
              else:
                  content = "# Test suite root\n"
          elif "data" in dir_path:
              if "raw" in dir_path:
                  content = "# Raw data storage\n"
              elif "processed" in dir_path:
                  content = "# Processed data storage\n"
              elif "results" in dir_path:
                  content = "# Results and outputs storage\n"
              else:
                  content = "# Data directory root\n"
          elif "specs" in dir_path:
              if "contracts" in dir_path:
                  content = "# Contract schemas\n"
              else:
                  content = "# Specifications root\n"
          
          init_file.write_text(content)
          print(f"Created __init__.py: {init_file}")
    
    print("\nProject structure setup complete!")

if __name__ == "__main__":
    create_project_structure()