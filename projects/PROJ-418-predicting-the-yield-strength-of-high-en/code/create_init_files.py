import os
import sys

def create_init_files():
    """
    Creates __init__.py files in all code/ and tests/ subdirectories
    to ensure they are recognized as Python packages.
    """
    # Define the root directories to scan
    root_dirs = ['code', 'tests']
    
    # Directories that should NOT have __init__.py (data storage, output)
    skip_dirs = {
        'data/raw', 'data/processed', 'output', 'output/plots',
        'data/raw/*', 'data/processed/*', 'output/*', 'output/plots/*'
    }

    for root_dir in root_dirs:
        if not os.path.exists(root_dir):
            print(f"Warning: Directory {root_dir} does not exist. Skipping.")
            continue

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Create __init__.py in the current directory if it doesn't exist
            init_path = os.path.join(dirpath, '__init__.py')
            if not os.path.exists(init_path):
                with open(init_path, 'w') as f:
                    f.write('"""\n')
                    f.write(f'{dirpath} module.\n')
                    f.write('"""\n')
                print(f"Created: {init_path}")
            else:
                print(f"Exists: {init_path}")

    print("Initialization complete.")

if __name__ == "__main__":
    create_init_files()