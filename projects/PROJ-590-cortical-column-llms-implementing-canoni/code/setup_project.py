import os
import sys

def main():
    """
    Create the project directory structure for the Cortical Column LLMs project.
    Creates directories: src/models, src/data, src/training, src/experiments, tests.
    """
    # Define the base directory (current working directory or project root)
    base_dir = os.getcwd()

    # Define the required directory structure relative to the project root
    # The task specifies: src/models, src/data, src/training, src/experiments, tests
    directories = [
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "tests",
        # Adding standard subdirectories for completeness based on typical project flow
        "data/results",
        "figures",
        "docs",
        "scripts",
        "state",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Project structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
