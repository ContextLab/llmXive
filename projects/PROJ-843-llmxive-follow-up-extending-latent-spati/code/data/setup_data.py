"""
Setup script to initialize the data directory structure and schemas.

This script is the entry point for T006. It creates the required directory
hierarchy and generates the initial schema report.
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.schemas import main as schema_main

def main():
    """
    Orchestrates the data setup process.
    """
    print("="*60)
    print("T006: Creating base data schemas and directory structure")
    print("="*60)
    
    # Run the schema main logic which creates dirs and validates
    schema_main()
    
    print("="*60)
    print("T006: Setup Complete")
    print("="*60)

if __name__ == "__main__":
    main()