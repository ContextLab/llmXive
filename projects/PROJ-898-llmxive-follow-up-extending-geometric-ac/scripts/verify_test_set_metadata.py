"""
Script to execute metadata checksumming and zero overlap verification.

This script is the entry point for T012, orchestrating the metadata generation
and verification process for the topology-shift test set.
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.metadata_checksum import main


if __name__ == "__main__":
    sys.exit(main())