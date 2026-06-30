"""
Script to initialize the project structure for the MgB2 Impurity Impact study.
Executes the creation of all required directories as per the implementation plan.
"""
import os
import sys

# Define the directory structure relative to the project root
# Note: The tasks.md mentions 'src/' but the system prompt constraints require
# artifacts to live under 'code/', 'data/', 'tests/', or 'specs/'.
# To satisfy the "Stay inside the project tree" constraint and ensure the
# generated code is runnable and the paths are valid for subsequent tasks,
# we map 'src' -> 'code', 'data/raw' -> 'data/raw', 'tests' -> 'tests'.
# This ensures the project structure is consistent with the LlmXive pipeline constraints.

base_dirs = [
    "code/ingestion",
    "code/modeling",
    "code/visualization",
    "code/utils",
    "tests/contract",
    "tests/integration",
    "tests/unit",
    "data/raw",
    "data/processed",
    "docs",
]

def create_structure():
    created_count = 0
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nProject structure initialization complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(create_structure())
