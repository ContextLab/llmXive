"""
Project Structure Setup Script

This script creates the required directory structure for the
Gut Microbiome-Cognitive Correlation Study project.

Usage:
    python setup_project.py

Creates:
    code/
    data/
    results/
    tests/
"""

import os
from pathlib import Path

def create_directory_structure():
    """Create the required project directories."""
    root = Path(".")
    
    directories = [
        "code",
        "data",
        "results",
        "tests",
        "code/models",
        "code/utils",
        "code/validation",
        "data/raw",
        "data/processed",
        "data/external",
        "results/associations",
        "results/plots",
        "results/sensitivity",
        "results/validation",
        "results/power",
        "tests/fixtures",
    ]
    
    created = []
    for dir_path in directories:
        path = root / dir_path
        if not path.exists():
            path.mkdir(parents=True)
            created.append(str(path))
            print(f"Created directory: {path}")
        else:
            print(f"Directory exists: {path}")
    
    return created

def create_init_files():
    """Create __init__.py files in all Python packages."""
    root = Path(".")
    
    init_paths = [
        "code/__init__.py",
        "data/__init__.py",
        "results/__init__.py",
        "tests/__init__.py",
        "code/models/__init__.py",
        "code/utils/__init__.py",
        "code/validation/__init__.py",
    ]
    
    created = []
    for init_path in init_paths:
        path = root / init_path
        if not path.exists():
          with open(path, "w") as f:
              f.write('"""\n' + init_path + '\n"""\n')
          created.append(str(path))
          print(f"Created init file: {path}")
        else:
            print(f"Init file exists: {path}")
    
    return created

def create_readme_files():
    """Create README.md files in all directories."""
    root = Path(".")
    
    readme_contents = {
        "code/README.md": """# Code Module

This directory contains the Python source code for the Gut Microbiome-Cognitive Correlation Study.

## Structure

- `__init__.py`: Package initialization
- `config.py`: Configuration and constants
- `models/`: Data models (Participant, MicrobiomeProfile, CognitiveScore)
- `utils/`: Utility functions (hygiene, logging, streaming)
- `download.py`: Data download scripts
- `preprocess.py`: Data preprocessing and transformation
- `analysis.py`: Statistical analysis
- `visualize.py`: Visualization generation
- `power_analysis.py`: Power analysis utilities
- `validation/`: Validation agents and tools
- `linting_config.py`: Linting and formatting configuration
""",
        "data/README.md": """# Data Directory

This directory stores all data artifacts for the Gut Microbiome-Cognitive Correlation Study.

## Subdirectories

- `raw/`: Raw downloaded data from UK Biobank
- `processed/`: Processed and transformed data (ILR coordinates, filtered cohorts)
- `external/`: External reference data and annotations

## Data Governance

All data files must include:
- Checksums for integrity verification
- PII masking where applicable
- Metadata documentation
""",
        "results/README.md": """# Results Directory

This directory contains all analysis results, reports, and visualizations.

## Subdirectories

- `associations/`: Statistical association results (parquet files)
- `plots/`: Generated visualizations (PNG, SVG)
- `sensitivity/`: Sensitivity analysis reports
- `validation/`: Validation and verification reports
- `power/`: Power analysis reports

## Output Standards

All results must include:
- Timestamp of generation
- Version of code used
- Input data checksums
- Clear interpretation guidelines
""",
        "tests/README.md": """# Tests Directory

This directory contains all test files for the Gut Microbiome-Cognitive Correlation Study.

## Structure

- `__init__.py`: Package initialization
- `test_preprocess.py`: Preprocessing logic tests
- `test_analysis.py`: Statistical analysis tests
- `test_power.py`: Power analysis tests
- `test_visualize.py`: Visualization tests
- `test_integration.py`: End-to-end integration tests

## Running Tests

```bash
pytest tests/ -v --cov=code
```
""",
    }
    
    created = []
    for rel_path, content in readme_contents.items():
        path = root / rel_path
        if not path.exists():
            with open(path, "w") as f:
                f.write(content)
            created.append(str(path))
            print(f"Created README: {path}")
        else:
            print(f"README exists: {path}")
    
    return created

def main():
    """Main entry point."""
    print("Setting up project structure for Gut Microbiome-Cognitive Correlation Study...")
    print("=" * 70)
    
    dirs = create_directory_structure()
    inits = create_init_files()
    readmes = create_readme_files()
    
    print("=" * 70)
    print(f"Setup complete!")
    print(f"Created {len(dirs)} directories")
    print(f"Created {len(inits)} init files")
    print(f"Created {len(readmes)} README files")
    print("\nProject structure is ready for implementation.")

if __name__ == "__main__":
    main()