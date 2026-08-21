import os
from pathlib import Path

def main():
    """
    Creates the code/utils/ directory for the llmXive follow-up project.
    This directory will contain utility modules such as entropy.py and heuristics.py.
    """
    project_root = Path("projects/PROJ-920-llmxive-follow-up-extending-masking-stal")
    utils_dir = project_root / "code" / "utils"
    
    # Ensure the parent code directory exists first
    code_dir = project_root / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the utils directory
    utils_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created directory: {utils_dir}")
    
    # Create an __init__.py to make it a proper Python package
    init_file = utils_dir / "__init__.py"
    init_file.write_text("# llmXive utilities package\n")
    print(f"Created package initializer: {init_file}")

if __name__ == "__main__":
    main()