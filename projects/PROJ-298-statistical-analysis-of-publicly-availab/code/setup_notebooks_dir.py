"""
Script to create the notebooks directory for the project.
This satisfies task T001e: Create `projects/PROJ-298-statistical-analysis-of-publicly-availab/notebooks/` directory.
"""
import os
from pathlib import Path

def main():
    """Create the notebooks directory if it doesn't exist."""
    # Define the project root relative to this script's location
    # The script is in code/, so project root is one level up
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    notebooks_dir = project_root / "notebooks"
    
    if not notebooks_dir.exists():
        notebooks_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {notebooks_dir}")
    else:
        print(f"Directory already exists: {notebooks_dir}")
    
    # Create a README.md to explain the purpose of the directory
    readme_path = notebooks_dir / "README.md"
    if not readme_path.exists():
        readme_content = """# Notebooks Directory

This directory contains Jupyter notebooks for exploratory data analysis, visualization, and reporting.

## Notebooks

- `01_data_exploration.ipynb`: Initial data exploration and summary statistics
- `02_trend_analysis.ipynb`: Time series trend analysis using Mann-Kendall test
- `03_decomposition.ipynb`: Time series decomposition and seasonality analysis
- `04_clustering.ipynb`: Tag co-occurrence clustering analysis

## Usage

To run a notebook:

```bash
jupyter notebook notebooks/<notebook_name>.ipynb
```

Ensure you have activated the virtual environment with required dependencies installed.
"""
        readme_path.write_text(readme_content)
        print(f"Created README: {readme_path}")
    else:
        print(f"README already exists: {readme_path}")

if __name__ == "__main__":
    main()