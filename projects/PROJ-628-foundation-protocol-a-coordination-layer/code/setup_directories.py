import os
import sys

def create_directories():
    """Create the required sub-directories for the Foundation Protocol project."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define the relative paths to be created
    directories = [
        "code",
        "code/foundation_protocol",
        "code/agents",
        "code/benchmarks",
        "code/experiments",
        "code/reports",
        "code/data",
        "code/tests",
        "data",
        "results",
        "state",
        "docs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    return created_count

def verify_directories():
    """Verify that all required sub-directories exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    directories = [
        "code",
        "code/foundation_protocol",
        "code/agents",
        "code/benchmarks",
        "code/experiments",
        "code/reports",
        "code/data",
        "code/tests",
        "data",
        "results",
        "state",
        "docs"
    ]
    
    missing = []
    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            missing.append(dir_path)
    
    if missing:
        print(f"Missing directories: {missing}")
        return False
    
    print("All required directories verified.")
    return True

if __name__ == "__main__":
    created = create_directories()
    print(f"Created {created} new directories.")
    
    if verify_directories():
        sys.exit(0)
    else:
        sys.exit(1)