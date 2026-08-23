import os
import sys

def ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> None:
    """Create the full project directory structure."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Define the required directory structure relative to the project root
    directories = [
        # Code modules
        os.path.join(base_dir, "code", "data"),
        os.path.join(base_dir, "code", "models"),
        os.path.join(base_dir, "code", "analysis"),
        os.path.join(base_dir, "code", "utils"),
        
        # Data storage
        os.path.join(base_dir, "data", "raw"),
        os.path.join(base_dir, "data", "processed"),
        os.path.join(base_dir, "data", "results"),
        
        # Tests
        os.path.join(base_dir, "tests"),
        os.path.join(base_dir, "tests", "integration"),
        os.path.join(base_dir, "tests", "unit"),
    ]
    
    print("Setting up project directory structure...")
    for directory in directories:
        ensure_dir(directory)
    
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()
