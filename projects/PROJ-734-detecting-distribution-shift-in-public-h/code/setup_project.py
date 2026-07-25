import os
import sys

def main():
    """
    Create the project directory structure as defined in T001.
    Paths are relative to the project root.
    """
    # Define the required directories
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "code/contracts"
    ]

    # Create directories
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
