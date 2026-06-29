"""
Project setup script for PROJ-099-statistical-analysis-of-algorithmic-fair.

This script creates the project directory skeleton with explicit paths
and placeholder README files as specified in T001.

FR-008 Disclaimer: Findings are associational only; no causal claims are made.
"""

import os
from pathlib import Path


def create_directory_structure():
    """Create all required project directories."""
    # Define all required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/analysis",
        "logs",
        "tests",
        "state",
    ]

    # Create each directory
    for dir_path in directories:
        full_path = Path(dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")

    return directories


def create_readme_files():
    """Create README.md files in each top-level folder."""
    # Define README content for each directory
    readme_contents = {
        "code": """# Code Directory

This directory contains all Python source code for the statistical analysis of algorithmic fairness project.

## Structure
- `setup_project.py` - Project initialization script
- `data-model.py` - Core data model classes
- `utils/` - Utility modules for metrics, loaders, and validators

## Execution
Scripts in this directory are designed to be run from the project root:
```bash
python code/<script_name>.py
```

## FR-008 Disclaimer
Findings are associational only; no causal claims are made.
""",
        "data/raw": """# Raw Data Directory

This directory stores the original, unmodified dataset files downloaded from external sources.

## Contents
- UCI Adult dataset
- COMPAS dataset
- Bank Marketing dataset
- German Credit dataset
- Law School Admission dataset

## Integrity
All raw files must maintain their original SHA-256 checksums. Any preprocessing creates copies in `data/processed/`.

## FR-008 Disclaimer
Findings are associational only; no causal claims are made.
""",
        "data/processed": """# Processed Data Directory

This directory contains preprocessed and transformed dataset files ready for analysis.

## Contents
- Preprocessed CSV files with extracted binary protected attributes and outcomes
- Trained model artifacts (subdirectory: `models/`)
- Dataset checksums and metadata

## Structure
```
data/processed/
├── <dataset_id>_preprocessed.csv
└── models/
    └── <model_id>.joblib
```

## FR-008 Disclaimer
Findings are associational only; no causal claims are made.
""",
        "data/analysis": """# Analysis Output Directory

This directory stores all statistical analysis outputs and research artifacts.

## Contents
- `metrics.csv` - Fairness metric computations
- `correlations.csv` - Pairwise metric correlations
- `regression_results.csv` - Fixed-effects regression outputs
- `bootstrap_results.csv` - Bootstrap confidence intervals
- `guidance.csv` - Metric selection guidance
- Diagnostic and coverage files

## FR-008 Disclaimer
Findings are associational only; no causal claims are made.
""",
        "logs": """# Logs Directory

This directory contains execution logs and diagnostic information.

## Files
- `exclusion.log` - CSV log of excluded datasets with columns: timestamp, dataset_id, missing_variable_name, reason
- `quickstart_errors.log` - Quickstart validation errors

## Format
All logs follow a structured format for automated parsing.

## FR-008 Disclaimer
Findings are associational only; no causal claims are made.
""",
        "tests": """# Tests Directory

This directory contains all test suites for the project.

## Structure
```
tests/
├── unit/
│   ├── test_checksum.py
│   ├── test_variable_validation.py
│   ├── test_demographic_parity.py
│   ├── test_equalized_odds.py
│   ├── test_fdr_correction.py
│   └── test_bootstrap.py
├── contract/
│   ├── test_dataset_download.py
│   ├── test_model_training.py
│   ├── test_correlation_analysis.py
│   └── test_framing_verification.py
└── integration/
    ├── test_preprocessing.py
    ├── test_fairness_metrics.py
    └── test_regression_analysis.py
```

## Running Tests
```bash
pytest tests/
```

## FR-008 Disclaimer
Findings are associational only; no causal claims are made.
""",
        "state": """# State Directory

This directory contains project state files and metadata.

## Contents
- `projects/PROJ-099-statistical-analysis-of-algorithmic-fair.yaml` - Project metadata and artifact hashes

## Purpose
State files track pipeline execution progress and artifact integrity.

## FR-008 Disclaimer
Findings are associational only; no causal claims are made.
""",
    }

    # Create README files
    for dir_name, content in readme_contents.items():
        readme_path = Path(dir_name) / "README.md"
        readme_path.write_text(content)
        print(f"✓ Created README: {readme_path}")

    return list(readme_contents.keys())


def main():
    """Main entry point for project setup."""
    print("=" * 60)
    print("PROJ-099 Project Setup")
    print("=" * 60)
    print()

    # Create directories
    print("Creating directory structure...")
    directories = create_directory_structure()
    print()

    # Create README files
    print("Creating README files...")
    readmes = create_readme_files()
    print()

    print("=" * 60)
    print("Setup Complete!")
    print(f"Created {len(directories)} directories and {len(readmes)} README files.")
    print("=" * 60)
    print()
    print("FR-008 Disclaimer: Findings are associational only; no causal claims are made.")


if __name__ == "__main__":
    main()