import os
from pathlib import Path

def main():
    """
    Creates the directory structure for output plots.
    Specifically creates 'output/plots/' relative to the project root.
    """
    # Determine project root based on the file location or standard convention
    # Since this script is in 'code/', we go up one level to project root
    project_root = Path(__file__).resolve().parent.parent
    plots_dir = project_root / "output" / "plots"
    
    if not plots_dir.exists():
        plots_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {plots_dir}")
    else:
        print(f"Directory already exists: {plots_dir}")

if __name__ == "__main__":
    main()