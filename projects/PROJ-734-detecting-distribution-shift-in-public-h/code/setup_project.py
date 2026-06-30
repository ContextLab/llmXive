import os
import sys

def main():
    """
    Creates the project directory structure required for the llmXive pipeline.
    
    Directories created:
      - data/raw
      - data/processed
      - code
      - tests
      - code/contracts
    """
    # Define relative paths to create
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "code/contracts"
    ]

    created_count = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Check if it's actually a directory or just a file with same name
            if os.path.isdir(dir_path):
                print(f"Directory already exists: {dir_path}")
            else:
                print(f"Error: Path exists but is not a directory: {dir_path}")
                sys.exit(1)

    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())