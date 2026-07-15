import os
from pathlib import Path

def setup_results_directories():
    """
    Create the required directory structure for results:
    - results/plots/
    - results/reports/

    This function ensures the directories exist, creating parent directories
    if necessary. It does not create any files, only the directory structure.
    """
    base_dir = Path("results")
    plots_dir = base_dir / "plots"
    reports_dir = base_dir / "reports"

    # Create directories if they don't exist
    plots_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Verify creation (optional logging)
    created = []
    if plots_dir.exists() and plots_dir.is_dir():
        created.append(str(plots_dir))
    if reports_dir.exists() and reports_dir.is_dir():
        created.append(str(reports_dir))

    return created

if __name__ == "__main__":
    created_dirs = setup_results_directories()
    print(f"Created directories: {', '.join(created_dirs)}")