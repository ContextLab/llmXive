import os
from pathlib import Path
from config import get_config

def setup_data_directories():
    """Create all required data directories."""
    config = get_config()
    dirs = [
        config.stimuli_dir,
        config.stimuli_metadata_dir,
        config.responses_dir,
        config.processed_dir,
        config.ethics_dir,
        config.logs_dir,
        config.figures_dir
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

if __name__ == "__main__":
    setup_data_directories()