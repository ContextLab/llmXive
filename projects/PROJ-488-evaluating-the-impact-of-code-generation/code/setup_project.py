#!/usr/bin/env python3
"""Setup script to create project directory structure for llmXive pipeline.

This script creates the required project directories and placeholder files
as specified in task T001.
"""
import os
from pathlib import Path


def create_directories():
    """Create all required project directories."""
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/metrics",
        "results",
        "state",
        "specs",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created directory: {dir_path}")


def create_readme():
    """Create placeholder README.md at project root."""
    readme_content = """# PROJ-488: Evaluating the Impact of Code Generation

This project evaluates the impact of code generation on code quality metrics
using static analysis tools and statistical testing.

## Setup

Run the setup script to create the project structure:
```bash
python code/setup_project.py
```

## Project Structure

- `code/` - Python source code and modules
- `data/raw/` - Raw dataset files (CodeSearchNet, CodeGen)
- `data/processed/` - Processed and filtered datasets
- `data/metrics/` - Computed metrics (CSV files)
- `results/` - Analysis results, figures, and reports
- `state/` - Pipeline state tracking YAML files
- `specs/` - Feature specifications and design documents

## Requirements

See `code/requirements.txt` for dependencies.

## Constitutional Amendments

⚠️ This project requires approval of Constitutional Amendments T009 and T010
before proceeding with Phase 3+. Check `state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml`
for amendment status.

## License

Research project under llmXive automated science pipeline.
"""
    readme_path = Path("README.md")
    readme_path.write_text(readme_content)
    print(f"[OK] Created: README.md")


def create_gitkeep_files():
    """Create .gitkeep files in empty directories to ensure they're tracked."""
    empty_dirs = [
        "data/raw",
        "data/processed",
        "data/metrics",
        "results",
        "state",
        "specs",
    ]
    
    for dir_path in empty_dirs:
        gitkeep = Path(dir_path) / ".gitkeep"
        gitkeep.touch()
        print(f"[OK] Created: {gitkeep}")


def main():
    """Main entry point for project setup."""
    print("=" * 60)
    print("llmXive Project Setup - Task T001")
    print("=" * 60)
    
    create_directories()
    create_readme()
    create_gitkeep_files()
    
    print("=" * 60)
    print("Project structure setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()