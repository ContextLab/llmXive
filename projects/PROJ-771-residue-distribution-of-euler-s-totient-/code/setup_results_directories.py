import os
from pathlib import Path

def setup_results_directories():
    """
    Create the results directory structure for plots and reports.
    
    Creates:
        - results/plots/
        - results/reports/
    
    This task corresponds to T001c in the project plan.
    """
    base_dir = Path("results")
    plots_dir = base_dir / "plots"
    reports_dir = base_dir / "reports"
    
    plots_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files to make them proper Python packages
    # (optional but good practice for project structure)
    (base_dir / "__init__.py").touch(exist_ok=True)
    (plots_dir / "__init__.py").touch(exist_ok=True)
    (reports_dir / "__init__.py").touch(exist_ok=True)
    
    return {
        "base": str(base_dir),
        "plots": str(plots_dir),
        "reports": str(reports_dir)
    }

if __name__ == "__main__":
    result = setup_results_directories()
    print(f"Created results directories: {result}")