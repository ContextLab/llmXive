import os
from pathlib import Path

def setup_data_directories(base_path: Path = None) -> None:
    """
    Creates the required directory structure for data storage.
    
    Args:
        base_path: Base path for data directories. Defaults to project root.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define directory structure
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "artifacts",
        base_path / "projects" / "PROJ-846-llmxive-follow-up-extending-guava-an-eff" / "data" / "raw",
        base_path / "projects" / "PROJ-846-llmxive-follow-up-extending-guava-an-eff" / "data" / "processed",
        base_path / "projects" / "PROJ-846-llmxive-follow-up-extending-guava-an-eff" / "data" / "artifacts",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
        print(f"Created directory: {directory}")

def main():
    """Main entry point for directory setup."""
    setup_data_directories()
    print("Data directories setup complete.")

if __name__ == "__main__":
    main()
