import os
import sys

def main():
    """
    Setup the data directory structure and create .gitkeep files.
    This task ONLY creates directories and empty markers. It MUST NOT
    create or initialize any data files.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    directories = [
        os.path.join(data_dir, 'raw'),
        os.path.join(data_dir, 'processed'),
        os.path.join(data_dir, 'interim')
    ]

    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        gitkeep_path = os.path.join(dir_path, '.gitkeep')
        # Create empty .gitkeep file to ensure directory is tracked by git
        with open(gitkeep_path, 'w') as f:
            pass
        print(f"Created: {dir_path}")
        print(f"Created: {gitkeep_path}")

    print("Data directory structure setup complete.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
