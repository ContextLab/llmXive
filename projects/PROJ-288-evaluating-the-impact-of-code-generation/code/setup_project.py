import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure for the llmXive research pipeline.
    
    Directories created:
    - code/data, code/analysis
    - data/raw, data/processed, data/baseline_corpus
    - tests/unit, tests/integration
    - docs/reports
    
    This satisfies T001: Create project structure per implementation plan.
    """
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        "code/data",
        "code/analysis",
        "data/raw",
        "data/processed",
        "data/baseline_corpus",
        "tests/unit",
        "tests/integration",
        "docs/reports"
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())