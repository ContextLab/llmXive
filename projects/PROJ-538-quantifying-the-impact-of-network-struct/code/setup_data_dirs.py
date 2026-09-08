import os
from pathlib import Path

def setup_data_directories() -> None:
    """
    Setup the data directory structure required for the project.
    
    Creates the following directory structure relative to the project root:
    - data/
        - raw/
        - processed/
        - contracts/
    
    This ensures that all necessary directories exist before data ingestion,
    processing, or schema contract generation begins.
    """
    # Define the base data directory relative to the project root
    # Assuming this script is run from the project root or code/ directory
    # We resolve the project root by going up from the code/ directory
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    contracts_dir = data_root / "contracts"
    
    # Create directories with parents=True to ensure full path creation
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    # Optional: Create a .gitkeep file in each directory to ensure they
    # are tracked by version control even if empty
    for directory in [raw_dir, processed_dir, contracts_dir]:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Directory for project data artifacts\n")
    
    # Log the creation for verification
    print(f"Data directories created at: {data_root}")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")
    print(f"  - {contracts_dir}")

if __name__ == "__main__":
    setup_data_directories()