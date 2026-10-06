import os
import sys
from pathlib import Path

# Project root is assumed to be the directory containing 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def create_directories():
    """
    Creates the required output directory structure:
    outputs/
    outputs/figures/
    outputs/reports/
    """
    base_path = PROJECT_ROOT / "outputs"
    dirs_to_create = [
        base_path,
        base_path / "figures",
        base_path / "reports"
    ]

    created = []
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(PROJECT_ROOT)))
        else:
            created.append(str(dir_path.relative_to(PROJECT_ROOT)))

    return created

def write_hierarchy_doc():
    """
    Writes the hierarchy definition to docs/design/output_structure.md
    """
    docs_dir = PROJECT_ROOT / "docs" / "design"
    docs_dir.mkdir(parents=True, exist_ok=True)

    file_path = docs_dir / "output_structure.md"

    content = """# Output Directory Structure

This document defines the hierarchy of the output directories for the project.

## Root: `outputs/`

The root directory for all generated results, figures, and reports.

### Subdirectories

- **`outputs/figures/`**: Contains all generated plots, charts, and visualizations (e.g., RDF plots, VDOS spectra, correlation scatter plots).
- **`outputs/reports/`**: Contains final analysis reports, summary tables, and documentation (e.g., PDF/HTML reports, assumptions.md).

## Usage

- All scripts generating visual outputs must save files to `outputs/figures/`.
- All scripts generating final reports or summaries must save files to `outputs/reports/`.
- Do not write intermediate data files here; use `data/derived/` for that purpose.
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path.relative_to(PROJECT_ROOT))

def main():
    """
    Main entry point to create directories and write the documentation.
    """
    print("Setting up output directories...")
    created_dirs = create_directories()
    print(f"Created/Verified directories: {', '.join(created_dirs)}")

    doc_path = write_hierarchy_doc()
    print(f"Wrote hierarchy definition to: {doc_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())