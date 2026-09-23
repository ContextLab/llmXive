"""
Script to create the output directory structure for the project.
Creates output/figures/ and output/reports/ directories.
"""
import os
from pathlib import Path

def create_output_directories():
    """
    Creates the output directory structure required for the project.
    
    Creates:
        - output/
        - output/figures/
        - output/reports/
    
    Returns:
        None
    
    Raises:
        OSError: If directory creation fails
    """
    project_root = Path(__file__).resolve().parent.parent
    output_base = project_root / "output"
    figures_dir = output_base / "figures"
    reports_dir = output_base / "reports"
    
    # Create directories if they don't exist
    figures_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep files to ensure directories are tracked by git
    (figures_dir / ".gitkeep").touch()
    (reports_dir / ".gitkeep").touch()
    
    print(f"Created output directory structure:")
    print(f"  - {figures_dir}")
    print(f"  - {reports_dir}")

if __name__ == "__main__":
    create_output_directories()
