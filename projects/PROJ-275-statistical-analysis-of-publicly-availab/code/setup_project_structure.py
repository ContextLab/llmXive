"""
Script to initialize the project directory structure for the
Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue project.

This script creates the necessary folders as defined in the implementation plan:
- code/ (already exists as root for this script, but ensures subfolders)
- tests/
- data/ (with subfolders: raw/, processed/, logs/)
- results/ (with subfolders: tables/, figures/)
- specs/ (with subfolders: 001-sentiment-revenue-lag-analysis/contracts/)
"""
import os
import sys

# Define the relative paths to create from the project root
# Assuming this script is run from the project root
directories = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "data/logs",
    "results/tables",
    "results/figures",
    "specs/001-sentiment-revenue-lag-analysis/contracts",
]

def create_structure():
    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(os.getcwd(), dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count == 0:
        print("No new directories were created. Structure already exists.")
    else:
        print(f"\nSuccessfully created {created_count} directory entries.")
    
    # Verify structure
    print("\nVerifying structure...")
    all_good = True
    for dir_path in directories:
        full_path = os.path.join(os.getcwd(), dir_path)
        if not os.path.isdir(full_path):
            print(f"ERROR: Failed to create or verify {dir_path}")
            all_good = False
    
    if all_good:
        print("All directories verified successfully.")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(create_structure())