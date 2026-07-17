import os
from pathlib import Path

def setup_data_directories():
    """
    Create the required data directory structure for the project.
    
    Creates:
      - data/raw/
      - data/interim/
      - data/processed/
      - data/external/
    
    These directories are used to store:
      - raw: Original downloaded GW noise segments
      - interim: Intermediate data products (e.g., injected waveforms)
      - processed: Final validated datasets ready for analysis
      - external: External baseline artifacts and reference data
    
    Returns:
      dict: Mapping of directory names to their absolute paths
    """
    base_dir = Path(__file__).resolve().parent.parent / "data"
    
    directories = {
        "raw": base_dir / "raw",
        "interim": base_dir / "interim",
        "processed": base_dir / "processed",
        "external": base_dir / "external",
    }
    
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    
    return {name: str(path) for name, path in directories.items()}

if __name__ == "__main__":
    setup_data_directories()