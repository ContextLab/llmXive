import os
import sys

def main():
    """
    Creates the project directory structure as specified in T001.
    Directories: data/raw, data/processed, code, tests, code/contracts
    """
    base_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "code/contracts"
    ]

    created = []
    skipped = []

    for dir_path in base_dirs:
        if os.path.exists(dir_path):
            skipped.append(dir_path)
            continue
        os.makedirs(dir_path, exist_ok=True)
        created.append(dir_path)

    if created:
        print(f"Created directories: {', '.join(created)}")
    if skipped:
        print(f"Directories already exist: {', '.join(skipped)}")
    
    # Ensure code/__init__.py exists if 'code' was created or to be safe
    code_init = "code/__init__.py"
    if not os.path.exists(code_init):
        with open(code_init, "w") as f:
            f.write("# llmXive project package\n")
        print(f"Created {code_init}")

    # Ensure tests/__init__.py exists
    tests_init = "tests/__init__.py"
    if not os.path.exists(tests_init):
        with open(tests_init, "w") as f:
            f.write("# Tests package\n")
        print(f"Created {tests_init}")

    print("Project structure initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())