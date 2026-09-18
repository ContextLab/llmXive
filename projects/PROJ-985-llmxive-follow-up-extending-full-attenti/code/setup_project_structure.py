import os
import sys

def create_directories():
    """Create the required project directory structure."""
    base_dir = os.getcwd()
    
    # Define all required directories relative to the project root
    required_dirs = [
        "code",
        "tests",
        "data",
        os.path.join("code", "lib"),
        os.path.join("code", "data"),
        os.path.join("code", "models"),
        os.path.join("code", "evaluation"),
        os.path.join("data", "results"),
        os.path.join("data", "logs"),
        os.path.join("data", "intermediate"),
    ]
    
    created = []
    for dir_path in required_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    return created

def verify_structure():
    """Verify that all required directories exist."""
    base_dir = os.getcwd()
    
    required_dirs = [
        "code",
        "tests",
        "data",
        os.path.join("code", "lib"),
        os.path.join("code", "data"),
        os.path.join("code", "models"),
        os.path.join("code", "evaluation"),
        os.path.join("data", "results"),
        os.path.join("data", "logs"),
        os.path.join("data", "intermediate"),
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.isdir(full_path):
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: Missing directories: {missing}")
        return False
    
    print("All required directories verified.")
    return True

def main():
    """Main entry point for project structure setup."""
    print("Setting up project structure for llmXive...")
    created = create_directories()
    if created:
        print(f"Created {len(created)} new directories.")
    else:
        print("No new directories created (all exist).")
    
    success = verify_structure()
    if success:
        print("Project structure setup completed successfully.")
    else:
        print("Project structure setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
