"""
Script to create the required code directory structure for the project.
This fulfills task T003.
"""
import os
import sys

def main():
    """
    Creates the following directories relative to the project root:
    - code/data/
    - code/tests/
    - code/utils/
    
    Also ensures __init__.py files exist in each to make them packages.
    """
    # Define the base directory (project root)
    # We assume this script is run from the project root or the script determines the root.
    # For T003, we are creating directories under the project root.
    # The prompt implies we are in the project root context.
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # The script is in code/, so base_dir is code/. We need to go up one level to project root.
    project_root = os.path.dirname(base_dir)
    
    directories = [
        os.path.join(project_root, "code", "data"),
        os.path.join(project_root, "code", "tests"),
        os.path.join(project_root, "code", "utils"),
    ]
    
    created = []
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created.append(dir_path)
        else:
            print(f"Directory already exists: {dir_path}")
        
        # Ensure __init__.py exists to make it a Python package
        init_file = os.path.join(dir_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write('"""' + os.path.basename(dir_path) + " module.\n\"\"\"\n")
            print(f"Created package initializer: {init_file}")
        else:
            print(f"Package initializer already exists: {init_file}")
    
    # Also ensure code/ itself has an __init__.py if it doesn't
    code_init = os.path.join(project_root, "code", "__init__.py")
    if not os.path.exists(code_init):
        with open(code_init, "w") as f:
            f.write('"""' + "Code package.\n\"\"\"\n")
        print(f"Created package initializer: {code_init}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())