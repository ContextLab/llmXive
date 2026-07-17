import os
from pathlib import Path

def setup_project_structure(project_name: str = "PROJ-964-llmxive-follow-up-extending-wan-streamer") -> None:
    """
    Creates the complete directory structure for the llmXive project.
    
    This task (T005) creates the root project directory and all required
    subdirectories for code, data, state, and docs as specified in the
    project plan.
    
    Structure created:
    projects/<project_name>/
    ├── code/
    │   ├── data/
    │   ├── models/
    │   ├── inference/
    │   ├── evaluation/
    │   ├── utils/
    │   ├── tasks/
    │   └── tests/
    ├── data/
    │   ├── raw/
    │   ├── processed/
    │   └── models/
    ├── state/
    └── docs/
    
    Args:
        project_name: The name of the project directory to create.
    """
    base_path = Path("projects") / project_name
    
    directories = [
        # Code directories
        base_path / "code",
        base_path / "code" / "data",
        base_path / "code" / "models",
        base_path / "code" / "inference",
        base_path / "code" / "evaluation",
        base_path / "code" / "utils",
        base_path / "code" / "tasks",
        base_path / "code" / "tests",
        
        # Data directories
        base_path / "data",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "models",
        
        # State and Docs
        base_path / "state",
        base_path / "docs",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        gitkeep.touch()
    
    print(f"Successfully created project structure at: {base_path}")

if __name__ == "__main__":
    setup_project_structure()