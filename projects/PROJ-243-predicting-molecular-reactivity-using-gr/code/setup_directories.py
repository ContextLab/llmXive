import os
import sys

def main():
    """
    Creates the required directory structure for the project.
    Directories created:
      - code
      - artifacts
      - tests
      - artifacts/logs
      - artifacts/metrics
      - artifacts/figures
      - tests/unit
      - tests/integration
      - tests/contract
    """
    base_dirs = [
        "code",
        "artifacts",
        "tests",
        "artifacts/logs",
        "artifacts/metrics",
        "artifacts/figures",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    created_count = 0
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
