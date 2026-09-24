import os
from pathlib import Path

def setup_results_directories():
    """
    Create the results directory structure for plots and reports.
    
    This task (T001c) implements the creation of:
    - results/plots/
    - results/reports/
    
    Returns:
        bool: True if directories were created successfully, False otherwise.
    """
    base_dir = Path("results")
    plots_dir = base_dir / "plots"
    reports_dir = base_dir / "reports"
    
    try:
        plots_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify creation by checking existence
        if not plots_dir.exists() or not reports_dir.is_dir():
            raise RuntimeError(f"Failed to create {plots_dir}")
        if not reports_dir.exists() or not reports_dir.is_dir():
            raise RuntimeError(f"Failed to create {reports_dir}")
            
        return True
    except Exception as e:
        print(f"Error creating results directories: {e}")
        return False

if __name__ == "__main__":
    success = setup_results_directories()
    if success:
        print("Successfully created results/plots/ and results/reports/ directories.")
    else:
        print("Failed to create results directories.")
        exit(1)
