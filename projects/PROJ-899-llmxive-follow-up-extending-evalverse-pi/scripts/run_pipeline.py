"""
Script to run the full pipeline.
"""
import os
import sys
from pathlib import Path
from src.data.download import fetch_evalverse_dataset
from src.data.download import main as download_main
from src.models.train import main as train_main

def main():
    """Main entry point for pipeline execution."""
    print("Starting llmXive pipeline...")
    
    # Step 1: Fetch dataset
    print("\n=== Step 1: Fetching Dataset ===")
    fetch_evalverse_dataset()
    
    # Step 2: Train models (placeholder for full pipeline)
    print("\n=== Step 2: Training Models ===")
    train_main()
    
    print("\nPipeline completed.")

if __name__ == "__main__":
    main()
