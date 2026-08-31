"""
Setup script to initialize the project directory structure and core files.
Creates all required directories and placeholder files as per T001.
"""
import os
import sys
from pathlib import Path

def main():
    """Create directory structure and core files."""
    root = Path(__file__).resolve().parent.parent
    
    # Define required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/explanation_tiers",
        "data/simulation_results",
        "code",
        "tests",
        "docs"
    ]
    
    # Create directories
    print(f"Creating directories in: {root}")
    for dir_name in required_dirs:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")
    
    # Define core files to ensure existence
    core_files = {
        "code/__init__.py": """\"\"\"
Code module for the Cognitive Load Optimization project.
Contains data loading, model training, tier generation, simulation, and analysis modules.
\"\"\"
""",
        "tests/__init__.py": """\"\"\"Test package for the Cognitive Load Optimization project.\"\"\"
""",
        "README.md": """# Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning

This project implements an adaptive learning system that adjusts explanation complexity based on estimated cognitive load.

## Project Structure

- `code/`: Source code for data loading, model training, tier generation, and simulation.
- `data/`: Data storage (raw, processed, tiers, results).
- `tests/`: Unit and integration tests.
- `docs/`: Documentation.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the pipeline: `python code/run_pipeline.py`
""",
        "requirements.txt": """# Core dependencies
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
lightgbm>=4.0.0
textstat>=0.7.0
datasets>=2.14.0
statsmodels>=0.14.0
pytest>=7.4.0
requests>=2.31.0
ruff>=0.1.0
black>=23.0.0
"""
    }
    
    for file_path, content in core_files.items():
        full_path = root / file_path
        # Only write if file doesn't exist or content differs
        if not full_path.exists() or full_path.read_text() != content:
            full_path.write_text(content)
            print(f"  Created/Updated: {full_path}")
        else:
            print(f"  Exists (skipped): {full_path}")
    
    print("\nProject structure initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
