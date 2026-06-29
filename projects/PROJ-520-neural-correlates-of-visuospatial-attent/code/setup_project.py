"""
Project setup script for PROJ-520-neural-correlates-of-visuospatial-attent.
Creates the required directory structure and verifies existence.
"""
import os
import sys

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "logs",
    "tests/unit",
    "tests/integration",
]

def create_directories():
    """Create all required directories if they do not exist."""
    created = []
    for dir_path in REQUIRED_DIRS:
        if not os.path.exists(dir_path):
          os.makedirs(dir_path)
          created.append(dir_path)
          print(f"Created directory: {dir_path}")
        else:
          print(f"Directory already exists: {dir_path}")
    return created

def verify_directories():
    """Verify that all required directories exist."""
    missing = []
    for dir_path in REQUIRED_DIRS:
        if not os.path.isdir(dir_path):
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: Missing directories: {', '.join(missing)}")
        return False
    
    print("\nVerification successful. All directories exist:")
    for dir_path in REQUIRED_DIRS:
        print(f"  - {dir_path}/")
    return True

def main():
    """Main entry point."""
    print("=== Project Setup ===")
    create_directories()
    
    if not verify_directories():
        sys.exit(1)
    
    print("\n=== Setup Complete ===")

if __name__ == "__main__":
    main()