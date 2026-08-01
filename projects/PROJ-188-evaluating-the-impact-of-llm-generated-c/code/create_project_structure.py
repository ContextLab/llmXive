import os
from pathlib import Path

def create_project_structure():
    """
    Create the root directory structure for the project.
    Specifically creates projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/
    as per task T001a.
    """
    root_dir = Path("projects/PROJ-188-evaluating-the-impact-of-llm-generated-c")
    
    # Create the root directory
    root_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created project root directory: {root_dir}")
    
    return str(root_dir)

if __name__ == "__main__":
    create_project_structure()
