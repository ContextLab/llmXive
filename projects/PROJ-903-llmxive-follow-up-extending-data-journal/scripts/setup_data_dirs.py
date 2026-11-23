"""
Script to initialize the required directory structure for the llmXive project.
Creates:
  - data/raw/
  - data/processed/
  - output/
"""
import os
import sys

def main():
    # Define the project root relative to this script location or explicit path
    # The task requires paths relative to the project root.
    # Assuming this script runs from the project root or we derive the root.
    # Based on task description: "projects/PROJ-903-llmxive-follow-up-extending-data-journal/data/..."
    # We will use the current working directory as the project root for flexibility,
    # or explicitly construct the path if the environment dictates.
    # To be safe and adhere to the "stay inside project tree" constraint,
    # we assume the script is run from the project root or we target the specific path.
    
    # The task explicitly lists:
    # projects/PROJ-903-llmxive-follow-up-extending-data-journal/data/raw
    # projects/PROJ-903-llmxive-follow-up-extending-data-journal/data/processed
    # projects/PROJ-903-llmxive-follow-up-extending-data-journal/output
    
    # We will construct these relative to the current working directory to ensure
    # we are writing to the correct location when the pipeline runs.
    
    base_dirs = [
        "projects/PROJ-903-llmxive-follow-up-extending-data-journal/data/raw",
        "projects/PROJ-903-llmxive-follow-up-extending-data-journal/data/processed",
        "projects/PROJ-903-llmxive-follow-up-extending-data-journal/output"
    ]
    
    created_count = 0
    
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("No new directories needed to be created.")
    
    # Verify existence
    for dir_path in base_dirs:
        if not os.path.isdir(dir_path):
            print(f"ERROR: Failed to create or verify {dir_path}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()