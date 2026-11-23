"""
Setup script to create the outputs and docs directory structure.
This implements task T001c.
"""
import os
import sys
from pathlib import Path

# Import project utilities if available, otherwise fallback to standard lib
try:
    from utils.config import get_project_root
except ImportError:
    # Fallback for running as a script from root without full package context
    def get_project_root():
        return Path.cwd()

def create_outputs_structure(root: Path):
    """Create outputs/figures and outputs/reports directories."""
    outputs_figures = root / "outputs" / "figures"
    outputs_reports = root / "outputs" / "reports"
    
    outputs_figures.mkdir(parents=True, exist_ok=True)
    outputs_reports.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep to ensure directories are tracked in git
    (outputs_figures / ".gitkeep").touch()
    (outputs_reports / ".gitkeep").touch()
    
    return [outputs_figures, outputs_reports]

def create_docs_structure(root: Path):
    """Create docs/ directory."""
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep
    (docs_dir / ".gitkeep").touch()
    
    return [docs_dir]

def main():
    """Main entry point for T001c."""
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    
    print("Creating outputs/figures and outputs/reports...")
    outputs_created = create_outputs_structure(project_root)
    for path in outputs_created:
        print(f"  Created: {path}")
    
    print("Creating docs/...")
    docs_created = create_docs_structure(project_root)
    for path in docs_created:
        print(f"  Created: {path}")
    
    print("T001c completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())