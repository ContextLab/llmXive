import os
from pathlib import Path

def setup_results_directories():
    """
    Create the required results directory structure for the project.
    
    This function creates:
    - results/plots/ : For storing generated visualization images (PNGs)
    - results/reports/ : For storing Markdown reports, JSON statistics, and benchmark logs
    
    This satisfies task T001c in the project pipeline.
    """
    base_dir = Path("results")
    plots_dir = base_dir / "plots"
    reports_dir = base_dir / "reports"

    plots_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Create a .gitkeep file in each directory to ensure they are tracked by git
    # even if they are initially empty.
    (plots_dir / ".gitkeep").touch()
    (reports_dir / ".gitkeep").touch()

    return {
        "plots": str(plots_dir.absolute()),
        "reports": str(reports_dir.absolute())
    }

if __name__ == "__main__":
    result = setup_results_directories()
    print(f"Results directories created:")
    print(f"  Plots: {result['plots']}")
    print(f"  Reports: {result['reports']}")