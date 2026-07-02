import os
import sys

def create_init_files():
    """
    Creates __init__.py files in all code/ and tests/ subdirectories
    to ensure they are recognized as Python packages.
    """
    # Define the directories that need __init__.py files
    # Based on the project structure: code/, code/data, code/utils, code/models, tests/
    init_paths = [
        "code",
        "code/data",
        "code/utils",
        "code/models",
        "tests"
    ]

    for path in init_paths:
        init_file_path = os.path.join(path, "__init__.py")
        if not os.path.exists(init_file_path):
            try:
                with open(init_file_path, "w") as f:
                    f.write('"""\n'
                            f'{path.replace("/", " ").replace("_", " ").title()} Module\n'
                            f'"""\n')
                print(f"Created: {init_file_path}")
            except Exception as e:
                print(f"Error creating {init_file_path}: {e}")
        else:
            print(f"Exists: {init_file_path}")

    print("Initialization files creation complete.")

if __name__ == "__main__":
    create_init_files()