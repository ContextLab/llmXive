"""Entry point to generate SHA‑256 checksums for the raw data directory.

This wrapper exists so the task runner can invoke the checksum generation
as a separate executable script (``python -m src.utils.run_checksums``).
"""
from src.utils.checksums import main

if __name__ == "__main__":
    main()