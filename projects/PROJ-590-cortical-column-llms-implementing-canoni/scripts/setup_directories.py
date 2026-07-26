import os
import sys

def main():
    """
    Creates the explicit directory tree required by plan.md:
    src/models, src/data, src/training, src/experiments, src/utils,
    tests/unit, tests/integration, scripts, data/results, data/logs,
    data/configs, state.
    """
    # Define the relative paths to be created
    directories = [
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "scripts",
        "data/results",
        "data/logs",
        "data/configs",
        "state",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        if os.path.exists(dir_path):
            existing_count += 1
            print(f"[SKIP] Directory exists: {dir_path}")
        else:
            os.makedirs(dir_path, exist_ok=True)
            created_count += 1
            print(f"[CREATED] Directory: {dir_path}")

    print(f"\nSummary: {created_count} directories created, {existing_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
