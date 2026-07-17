import os
import sys
from pathlib import Path

def setup_data_directories(base_path: Path) -> None:
    """
    Create the required data subdirectories for the project.
    
    Creates:
    - data/raw: For raw, unprocessed dataset files (e.g., VoxCeleb2, logs)
    - data/processed: For processed datasets, extracted latents, and intermediate artifacts
    - data/models: For saved model checkpoints and weights
    
    Args:
        base_path: The root directory of the project (where 'data' folder should be created)
    """
    data_dir = base_path / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    models_dir = data_dir / "models"
    
    directories = [data_dir, raw_dir, processed_dir, models_dir]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Optional: create a .gitkeep file to ensure the directory is tracked by git
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# This directory is managed by the llmXive pipeline\n")
        
    print(f"Created data directories under: {data_dir}")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")
    print(f"  - {models_dir}")

def main():
    """
    Main entry point for creating data directories.
    Assumes the script is run from the project root.
    """
    # Determine the project root (parent of 'code' directory)
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent
    
    print(f"Project root detected at: {project_root}")
    
    try:
        setup_data_directories(project_root)
        print("Data directory setup completed successfully.")
    except Exception as e:
        print(f"Error setting up data directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
