import os
from pathlib import Path
import sys
import subprocess

def main():
    # Define the required directory structure
    directories = [
        "code",
        "code/utils",
        "data/raw",
        "data/interim",
        "data/processed",
        "results",
        "paper",
        "tests",
    ]

    print("Creating project directory structure...")
    for dir_path in directories:
        p = Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder __init__.py in every requested directory
        init_file = p / "__init__.py"
        init_file.touch()
        print(f"Created: {init_file}")

    # Verification: check if pandas is importable
    print("Verifying environment...")
    try:
        import pandas
        print(f"Pandas version {pandas.__version__} imported successfully.")
    except ImportError as e:
        print(f"Pandas import failed: {e}")
        sys.exit(1)

    # Also run the specific command requested in verification
    try:
        subprocess.run([sys.executable, "-c", "import pandas"], check=True)
        print("Command 'python -c \"import pandas\"' executed successfully.")
    except subprocess.CalledProcessError:
        print("Command 'python -c \"import pandas\"' failed.")
        sys.exit(1)

    print("Project layout and dependency verification complete.")

if __name__ == "__main__":
    main()