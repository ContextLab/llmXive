"""
Script to initialize the data directory structure for the llmXive project.
Creates: data/raw, data/filtered, data/scores
"""
import os
import sys

def main():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    dirs_to_create = [
        os.path.join(base_dir, "raw"),
        os.path.join(base_dir, "filtered"),
        os.path.join(base_dir, "scores"),
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count == 0:
        print("No new directories were created; all exist.")
    else:
        print(f"Successfully created {created_count} directory/directories.")

    # Explicitly verify the target directory for T001h
    target = os.path.join(base_dir, "raw")
    if not os.path.isdir(target):
        print(f"ERROR: Failed to create required directory: {target}", file=sys.stderr)
        sys.exit(1)
    print(f"Verified existence of required directory: {target}")

if __name__ == "__main__":
    main()