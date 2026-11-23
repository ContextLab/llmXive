# This file is a legacy/wrapper for compatibility if T007 was initially planned here.
# The actual implementation is in code/data/manifest.py as per the API surface.
# We re-export the main function to satisfy potential import paths if the project
# structure expects it here, but the primary artifact is manifest.py.

import sys
import os

# Add parent directory to path to import from code.data
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.manifest import (
    calculate_file_checksum,
    fetch_remote_checksum,
    verify_dataset_integrity,
    generate_manifest,
    update_state,
    main
)

__all__ = [
    'calculate_file_checksum',
    'fetch_remote_checksum',
    'verify_dataset_integrity',
    'generate_manifest',
    'update_state',
    'main'
]