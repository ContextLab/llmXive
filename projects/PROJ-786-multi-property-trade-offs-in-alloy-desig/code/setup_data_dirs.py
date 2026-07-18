import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the required data directory structure for the project.
    Specifically creates data/raw/ and data/processed/ directories.
    Also ensures .gitkeep files are present to track empty directories in git.
    """
    base_path = Path(__file__).parent.parent
    data_path = base_path / "data"
    
    # Define required subdirectories
    subdirs = [
        data_path / "raw",
        data_path / "processed"
    ]
    
    created_dirs = []
    for subdir in subdirs:
        subdir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(subdir.relative_to(base_path)))
        
        # Create .gitkeep to ensure directory is tracked by git
        gitkeep = subdir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            created_dirs.append(str(gitkeep.relative_to(base_path)))
    
    return created_dirs

if __name__ == "__main__":
    created = setup_data_directories()
    print(f"Created directories: {', '.join(created)}")
