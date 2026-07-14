"""
Orchestration script for T031c: Generate final metrics with Bonferroni correction.
This script ensures all prerequisites are met and executes the statistical analysis.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis.stats import main as stats_main

def main():
    """
    Entry point for the final metrics generation pipeline.
    """
    print("Starting T031c: Bonferroni correction and final metrics generation...")
    try:
        stats_main()
        print("T031c completed successfully.")
    except Exception as e:
        print(f"T031c failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
