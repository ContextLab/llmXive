"""
Script to initialize and validate requirements.txt for the project.
This script ensures the requirements.txt file exists with the correct pinned dependencies.
"""
import os
import sys
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory (parent of code/)."""
    current = Path(__file__).resolve()
    # Navigate up from code/setup/init_requirements.py to project root
    return current.parent.parent.parent

def ensure_requirements_txt(root: Path) -> bool:
    """Create or validate requirements.txt with pinned dependencies."""
    req_file = root / "requirements.txt"
    
    required_packages = {
        "numpy": ">=1.26.0,<2.0.0",
        "scipy": ">=1.12.0,<2.0.0",
        "pandas": ">=2.2.0,<3.0.0",
        "matplotlib": ">=3.8.0,<4.0.0",
        "jupyter": ">=1.0.0,<2.0.0",
        "streamlit": ">=1.32.0,<2.0.0",
        "pytest": ">=8.0.0,<9.0.0",
        "ruff": ">=0.3.0,<1.0.0",
        "black": ">=24.0.0,<25.0.0"
    }
    
    if req_file.exists():
        print(f"Found existing requirements.txt at {req_file}")
        with open(req_file, 'r') as f:
            content = f.read()
        
        # Check if all required packages are present
        missing = []
        for package in required_packages:
            if not any(line.startswith(package + ">=") or line.startswith(package + "<=") or line.startswith(package + "==") for line in content.split('\n') if line.strip()):
                missing.append(package)
        
        if missing:
            print(f"Warning: Missing packages in requirements.txt: {missing}")
            print("Updating requirements.txt with missing packages...")
            with open(req_file, 'a') as f:
                for package in missing:
                    f.write(f"{package}{required_packages[package]}\n")
            return True
        else:
            print("All required packages are present in requirements.txt")
            return True
    else:
        print(f"Creating new requirements.txt at {req_file}")
        with open(req_file, 'w') as f:
            f.write("# Python 3.11+ pinned dependencies for PROJ-015\n")
            f.write("# Core scientific computing and data analysis\n")
            f.write(f"numpy{required_packages['numpy']}\n")
            f.write(f"scipy{required_packages['scipy']}\n")
            f.write(f"pandas{required_packages['pandas']}\n")
            f.write("\n")
            f.write("# Visualization\n")
            f.write(f"matplotlib{required_packages['matplotlib']}\n")
            f.write("\n")
            f.write("# Interactive development and web app\n")
            f.write(f"jupyter{required_packages['jupyter']}\n")
            f.write(f"streamlit{required_packages['streamlit']}\n")
            f.write("\n")
            f.write("# Testing and linting (optional but recommended)\n")
            f.write(f"pytest{required_packages['pytest']}\n")
            f.write(f"ruff{required_packages['ruff']}\n")
            f.write(f"black{required_packages['black']}\n")
        return True

def main():
    """Main entry point for the script."""
    root = get_project_root()
    print(f"Project root: {root}")
    
    if ensure_requirements_txt(root):
        print("✓ requirements.txt is properly initialized")
        return 0
    else:
        print("✗ Failed to initialize requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())