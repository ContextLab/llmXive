import os
from pathlib import Path

def main():
    """
    Creates the 'data/processed/' directory for project PROJ-920-llmxive-follow-up-extending-masking-stal.
    This directory is intended for storing intermediate and final processed data artifacts.
    """
    base_path = Path("projects/PROJ-920-llmxive-follow-up-extending-masking-stal")
    processed_dir = base_path / "data" / "processed"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a .gitkeep file to ensure the directory is tracked by git even if empty
    gitkeep = processed_dir / ".gitkeep"
    gitkeep.write_text("# Processed data directory\n")
    
    print(f"Successfully created directory: {processed_dir}")

if __name__ == "__main__":
    main()