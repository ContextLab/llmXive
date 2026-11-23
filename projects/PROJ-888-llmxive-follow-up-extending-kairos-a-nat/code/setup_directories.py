import os
import sys
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)

def create_directory(path: Path) -> bool:
    """Create a directory if it doesn't exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """Main entry point for directory creation."""
    project_root = Path("projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat")
    
    directories = [
        project_root,
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "state",
        project_root / "docs",
        project_root / "results",
        project_root / "logs",
        project_root / "scripts",
        project_root / "specs",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "models",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        project_root / "code" / "utils",
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "analysis",
        project_root / "figures",
    ]

    all_success = True
    for directory in directories:
        if not create_directory(directory):
            all_success = False

    if all_success:
        logger.info("All directories created successfully.")
        return 0
    else:
        logger.info(f"Directory already exists: {dir_path}")

def main() -> None:
    """Initialize the project directory structure."""
    project_root = Path(__file__).parent.parent
    project_name = "PROJ-888-llmxive-follow-up-extending-kairos-a-nat"
    
    # Define the root project directory
    project_dir = project_root / "projects" / project_name
    
    # Define subdirectories
    subdirs = ["code", "tests", "data", "state", "docs"]
    
    # Create the main project directory
    create_directory(str(project_dir))
    
    # Create subdirectories
    for subdir in subdirs:
        create_directory(str(project_dir / subdir))
    
    # Generate directory listing using tree command
    import subprocess
    try:
        result = subprocess.run(
            ["tree", "-L", "2"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True
        )
        listing_path = project_dir / "state" / "directory_listing.txt"
        with open(listing_path, "w") as f:
            f.write(result.stdout)
        logger.info(f"Directory listing written to: {listing_path}")
        
        # Verify file exists and has content
        if listing_path.exists() and listing_path.stat().st_size > 0:
            logger.info("Verification successful: directory_listing.txt exists and is non-empty")
        else:
            logger.error("Verification failed: directory_listing.txt is missing or empty")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run tree command: {e}")
        logger.error("Falling back to manual directory listing generation")
        
        # Fallback: manually generate listing
        listing_path = project_dir / "state" / "directory_listing.txt"
        with open(listing_path, "w") as f:
            f.write(f"{project_name}\n")
            f.write("├── code/\n")
            f.write("├── data/\n")
            f.write("├── docs/\n")
            f.write("├── state/\n")
            f.write("└── tests/\n")
        
        logger.info(f"Manual directory listing written to: {listing_path}")

if __name__ == "__main__":
    main()