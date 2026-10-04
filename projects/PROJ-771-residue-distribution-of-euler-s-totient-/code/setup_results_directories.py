import os
from pathlib import Path

def setup_results_directories():
    """
    Create the results directory structure:
    - results/plots/
    - results/reports/
    
    This task corresponds to T001c in the project plan.
    """
    base_dir = Path("results")
    plots_dir = base_dir / "plots"
    reports_dir = base_dir / "reports"

    plots_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files to ensure directories are tracked by git
    (plots_dir / ".gitkeep").touch()
    (reports_dir / ".gitkeep").touch()

    return {
        "plots": str(plots_dir),
        "reports": str(reports_dir)
    }

if __name__ == "__main__":
    result = setup_results_directories()
    print(f"Created directories: {result}")
