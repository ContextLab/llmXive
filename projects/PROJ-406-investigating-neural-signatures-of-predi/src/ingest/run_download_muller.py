"""
Helper script to invoke the sub‑command style of src.ingest.load_illusions.
This script exists solely so that the CI can execute the download step
without needing to pass command‑line arguments to the module directly.
"""

from src.ingest.load_illusions import main

if __name__ == "__main__":
    # Execute the sub‑command with no additional arguments (uses defaults)
    main(["download_muller"])
