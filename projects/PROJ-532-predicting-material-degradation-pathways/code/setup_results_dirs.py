"""
Script to initialize the results directory structure for the project.
Creates metrics/, plots/, and artifacts/ subdirectories under results/.
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Create the results directory structure."""
    project_root = Path(__file__).resolve().parent.parent
    results_root = project_root / "results"

    # Define subdirectories
    subdirs = [
        "metrics",
        "plots",
        "artifacts"
    ]

    for subdir_name in subdirs:
        subdir_path = results_root / subdir_name
        ensure_dir(subdir_path)
        print(f"Created directory: {subdir_path}")

    # Create a README in the results root
    readme_path = results_root / "README.md"
    if not readme_path.exists():
        readme_content = (
            "# Results Directory\n\n"
            "This directory stores all output artifacts from the material degradation pipeline.\n\n"
            "## Subdirectories\n\n"
            "- `metrics/`: JSON reports and evaluation metrics.\n"
            "- `plots/`: Generated visualizations (PNG, SVG).\n"
            "- `artifacts/`: Trained models and serialized objects.\n"
        )
        readme_path.write_text(readme_content)
        print(f"Created file: {readme_path}")

if __name__ == "__main__":
    main()
