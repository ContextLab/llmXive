"""
Setup script to create the required data directory structure for the llmXive pipeline.

Creates the following directories under the project root:
- data/raw: For original unmodified source data (e.g., ActivityNet clips)
- data/distorted: For generated videos with extreme aspect ratio distortions
- data/outputs: For final analysis outputs, metrics, and reports
- data/metadata: For CSV mappings, schema definitions, and intermediate metadata
"""
import os
from pathlib import Path

def main():
    # Define the project root (assuming this script is in code/ and root is parent)
    # Or run from project root and use relative paths
    base_path = Path(os.getcwd())
    
    # Define the required directories relative to the project root
    directories = [
        "data/raw",
        "data/distorted",
        "data/outputs",
        "data/metadata"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSetup complete. {created_count} new directory(ies) created.")

if __name__ == "__main__":
    main()