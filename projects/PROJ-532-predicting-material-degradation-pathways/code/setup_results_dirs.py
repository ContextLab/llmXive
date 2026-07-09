"""
Script to initialize the results directory structure for the project.
Creates metrics/, plots/, and artifacts/ subdirectories under results/.
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    os.makedirs(path, exist_ok=True)

def main() -> None:
    """Create the results directory structure."""
    project_root = Path(__file__).resolve().parent.parent
    results_root = project_root / "results"
    
    subdirs = ["metrics", "plots", "artifacts"]
    
    for subdir in subdirs:
        dir_path = results_root / subdir
        ensure_dir(dir_path)
        print(f"Created: {dir_path}")
    
    # Create a README.md in the results directory
    readme_path = results_root / "README.md"
    if not readme_path.exists():
        readme_content = (
            "# Results Directory\n\n"
            "This directory stores the outputs of the material degradation pipeline.\n\n"
            "## Subdirectories\n\n"
            "- `metrics/`: JSON reports of model performance and validation metrics.\n"
            "- `plots/`: Generated figures (PNG, SVG) including confusion matrices and SHAP plots.\n"
            "- `artifacts/`: Trained model pickles and intermediate artifacts.\n"
        )
        readme_path.write_text(readme_content)
        print(f"Created: {readme_path}")
    else:
        print(f"Skipped (exists): {readme_path}")

if __name__ == "__main__":
    main()
