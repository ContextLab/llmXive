"""
Project Setup Script for llmXive - Evaluating the Impact of Code Generation Models on Code Vulnerability Density.

This script initializes the project directory structure as per the implementation plan.
It creates the following directories:
- code/
- data/
- data/raw/
- data/generated/
- data/processed/
- results/
- state/
- tests/
- tests/unit/
- tests/integration/
- tests/contract/
- specs/
- docs/
"""

import os
import sys
from pathlib import Path


def create_directory(path: Path, description: str = "") -> None:
    """Create a directory if it doesn't exist and log its creation."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path} {description}")
    else:
        print(f"Directory already exists: {path}")

    # Create a .gitkeep file to ensure the directory is tracked by git
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("# Keep this directory in git\n")
        print(f"  -> Created .gitkeep in {path}")


def main() -> None:
    """Create the project structure as per the implementation plan."""
    # Get the project root directory (assumed to be the parent of the code/ directory)
    project_root = Path(__file__).resolve().parent.parent

    print(f"Setting up project structure at: {project_root}")
    print("=" * 60)

    # Phase 1: Core directories
    create_directory(project_root / "code", "# Core implementation code")
    create_directory(project_root / "data", "# Raw and processed data")
    create_directory(project_root / "data" / "raw", "# Raw downloaded datasets")
    create_directory(project_root / "data" / "generated", "# LLM-generated code samples")
    create_directory(project_root / "data" / "processed", "# Processed analysis data")
    create_directory(project_root / "results", "# Final results and reports")
    create_directory(project_root / "state", "# State tracking and hashes")
    create_directory(project_root / "tests", "# Test suite")
    create_directory(project_root / "tests" / "unit", "# Unit tests")
    create_directory(project_root / "tests" / "integration", "# Integration tests")
    create_directory(project_root / "tests" / "contract", "# Contract tests")
    create_directory(project_root / "specs", "# Feature specifications")
    create_directory(project_root / "docs", "# Documentation")

    print("=" * 60)
    print("Project structure setup complete!")
    print("\nDirectory hierarchy created:")
    print("├── code/")
    print("├── data/")
    print("│   ├── raw/")
    print("│   ├── generated/")
    print("│   └── processed/")
    print("├── results/")
    print("├── state/")
    print("├── tests/")
    print("│   ├── unit/")
    print("│   ├── integration/")
    print("│   └── contract/")
    print("├── specs/")
    print("└── docs/")


if __name__ == "__main__":
    main()