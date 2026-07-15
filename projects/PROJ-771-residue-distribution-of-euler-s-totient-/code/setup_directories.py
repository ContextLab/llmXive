import os
from pathlib import Path

def setup_directories():
    """
    Creates the necessary directory structure for the project.
    Implements T001a, T001b, T001c.
    """
    base = Path(".")
    
    # T001a: Create code directory (usually exists, but ensure)
    (base / "code").mkdir(exist_ok=True)
    
    # T001b: Create data/raw and data/processed
    (base / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (base / "data" / "processed").mkdir(parents=True, exist_ok=True)
    
    # T001c: Create results/plots and results/reports
    (base / "results" / "plots").mkdir(parents=True, exist_ok=True)
    (base / "results" / "reports").mkdir(parents=True, exist_ok=True)
    
    # Print confirmation for verification
    print("Directory structure created successfully:")
    print("  - code/")
    print("  - data/raw/")
    print("  - data/processed/")
    print("  - results/plots/")
    print("  - results/reports/")

if __name__ == "__main__":
    setup_directories()
