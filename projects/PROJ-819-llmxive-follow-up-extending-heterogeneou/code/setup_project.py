import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-819.
    
    Directories created:
    - projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/
      - code/
        - cache/
        - pipeline/
        - analysis/
      - data/
        - raw/
        - derived/
      - tests/
        - unit/
        - integration/
      - state/
    """
    project_root = Path("projects/PROJ-819-llmxive-follow-up-extending-heterogeneou")
    
    # Define the directory structure relative to project_root
    directories = [
        "code",
        "code/cache",
        "code/pipeline",
        "code/analysis",
        "data",
        "data/raw",
        "data/derived",
        "tests",
        "tests/unit",
        "tests/integration",
        "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {full_path}")
        else:
            print(f"Exists:  {full_path}")
    
    print(f"Setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
