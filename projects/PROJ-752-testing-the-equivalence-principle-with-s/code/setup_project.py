import os
import sys

def create_project_structure():
    """
    Creates the directory structure for the llmXive automated science pipeline project.
    
    This function creates the following directories relative to the current working directory:
    - code/data, code/models, code/analysis, code/utils, code/tests
    - contracts
    - data/raw, data/processed, data/results
    - docs
    
    It also creates placeholder __init__.py files in Python packages to ensure they are
    recognized as modules.
    """
    # Define the directory structure to create
    directories = [
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "code/tests",
        "contracts",
        "data/raw",
        "data/processed",
        "data/results",
        "docs"
    ]

    # Create directories
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create __init__.py files for Python packages
    python_packages = [
        "code",
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "code/tests"
    ]

    for package_path in python_packages:
        init_file = os.path.join(package_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Package initialization file\n")
            print(f"Created package initializer: {init_file}")
        else:
            print(f"Package initializer already exists: {init_file}")

    # Create placeholder files for contracts
    contract_files = [
        "contracts/normal_point.schema.yaml",
        "contracts/orbit_solution.schema.yaml",
        "contracts/eotvos_result.schema.yaml"
    ]

    for contract_file in contract_files:
        if not os.path.exists(contract_file):
            with open(contract_file, "w") as f:
                f.write("# Schema definition placeholder\n")
            print(f"Created contract schema placeholder: {contract_file}")
        else:
            print(f"Contract schema already exists: {contract_file}")

    # Create placeholder files for data directories
    data_placeholders = [
        ("data/raw/.gitkeep", "# Raw data directory - do not commit actual data files"),
        ("data/processed/.gitkeep", "# Processed data directory"),
        ("data/results/.gitkeep", "# Results directory"),
        ("docs/.gitkeep", "# Documentation directory")
    ]

    for file_path, content in data_placeholders:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write(content)
            print(f"Created placeholder file: {file_path}")
        else:
            print(f"Placeholder file already exists: {file_path}")

    print("\nProject structure creation complete.")
    print("Directory structure:")
    print("├── code/")
    print("│   ├── data/")
    print("│   ├── models/")
    print("│   ├── analysis/")
    print("│   ├── utils/")
    print("│   └── tests/")
    print("├── contracts/")
    print("├── data/")
    print("│   ├── raw/")
    print("│   ├── processed/")
    print("│   └── results/")
    print("└── docs/")

if __name__ == "__main__":
    create_project_structure()