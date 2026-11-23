"""
Setup script to create the documentation directory structure and initial files.
This task (T001c) specifically creates `outputs/` and `docs/` directories and placeholders.
"""
import os
from pathlib import Path
import sys

from utils.config import get_project_root


def create_docs_structure():
    """
    Create the documentation directory structure and placeholder files.
    
    Creates:
    - docs/
    - docs/quickstart.md
    - docs/README.md
    
    Also creates the outputs structure as per T001c requirements:
    - outputs/figures
    - outputs/reports
    """
    project_root = get_project_root()
    
    # Define paths
    docs_dir = project_root / "docs"
    outputs_dir = project_root / "outputs"
    figures_dir = outputs_dir / "figures"
    reports_dir = outputs_dir / "reports"
    
    # Create directories
    print(f"Creating directories under {project_root}...")
    
    # 1. Create docs directory
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {docs_dir}")
    else:
        print(f"  Exists: {docs_dir}")
    
    # 2. Create outputs structure
    if not outputs_dir.exists():
        outputs_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {outputs_dir}")
    
    if not figures_dir.exists():
        figures_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {figures_dir}")
    else:
        print(f"  Exists: {figures_dir}")
        
    if not reports_dir.exists():
        reports_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {reports_dir}")
    else:
        print(f"  Exists: {reports_dir}")
    
    # 3. Create placeholder files in docs/
    quickstart_path = docs_dir / "quickstart.md"
    readme_path = docs_dir / "README.md"
    
    if not quickstart_path.exists():
        quickstart_path.write_text(
            "# Quick Start Guide\n\n"
            "This project analyzes the effects of dark matter halo shapes on galaxy formation.\n\n"
            "## Prerequisites\n"
            "- Python 3.11+\n"
            "- Dependencies from `requirements.txt`\n\n"
            "## Usage\n"
            "Run the main pipeline:\n```bash\npython code/main.py\n```\n"
        )
        print(f"  Created: {quickstart_path}")
    else:
        print(f"  Exists: {quickstart_path}")
    
    if not readme_path.exists():
        readme_path.write_text(
            "# Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation\n\n"
            "## Overview\n"
            "This project implements a pipeline to ingest cosmological simulation data (TNG-100, Millennium-II),\n"
            "compute halo shape metrics, and perform statistical analysis on galaxy formation correlations.\n\n"
            "## Structure\n"
            "- `code/`: Source code\n"
            "- `data/`: Raw and processed data\n"
            "- `outputs/`: Generated figures and reports\n"
            "- `docs/`: Documentation\n\n"
            "## Installation\n"
            "See `docs/quickstart.md` for setup instructions.\n"
        )
        print(f"  Created: {readme_path}")
    else:
        print(f"  Exists: {readme_path}")
    
    print("\nDirectory structure created successfully.")
    return True


def main():
    """Entry point for the setup script."""
    try:
        create_docs_structure()
        print("\n✅ T001c: outputs/ and docs/ directories created.")
        return 0
    except Exception as e:
        print(f"\n❌ Error during directory creation: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
