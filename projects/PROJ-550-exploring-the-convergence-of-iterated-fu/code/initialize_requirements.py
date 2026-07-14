import subprocess
import sys
from pathlib import Path

def main():
    """
    Initialize the Python project dependencies for T002.
    1. Ensures requirements.txt exists with pinned versions.
    2. Runs pip install -r requirements.txt.
    3. Runs pip freeze > requirements.txt to confirm environment state.
    """
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    # Define the pinned versions as per task specification
    pinned_versions = [
        "numpy==1.26.4",
        "scipy==1.12.0",
        "scikit-learn==1.4.0",
        "pandas==2.1.4",
        "pytest==7.4.3",
        "matplotlib==3.8.2",
        "pyarrow==14.0.1",
    ]

    # Write requirements.txt if it doesn't match or to ensure freshness
    # (In a real CI/CD or local run, we ensure the file exists first)
    if not requirements_path.exists():
        print(f"Creating {requirements_path}...")
        requirements_path.write_text("\n".join(pinned_versions) + "\n")
    else:
        current_content = requirements_path.read_text().strip().splitlines()
        # Normalize comparison (strip whitespace)
        current_clean = [line.strip() for line in current_content if line.strip()]
        if current_clean != pinned_versions:
            print(f"Updating {requirements_path} to match pinned versions...")
            requirements_path.write_text("\n".join(pinned_versions) + "\n")
        else:
            print(f"{requirements_path} already matches pinned versions.")

    # Step 2: Run pip install
    print("Running pip install -r requirements.txt...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
        ])
    except subprocess.CalledProcessError as e:
        print(f"ERROR: pip install failed with exit code {e.returncode}")
        raise SystemExit(1)

    # Step 3: Run pip freeze to update requirements.txt with the exact installed state
    print("Running pip freeze > requirements.txt...")
    try:
        # We write directly to the file to ensure it reflects the installed environment
        # Note: This might include extra dependencies (e.g., typing-extensions)
        # which is standard behavior for 'pip freeze'.
        subprocess.check_call([
            sys.executable, "-m", "pip", "freeze"
        ], stdout=requirements_path.open("w"))
        
        print("requirements.txt updated with frozen environment.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: pip freeze failed with exit code {e.returncode}")
        raise SystemExit(1)

    print("T002 Initialization complete.")

if __name__ == "__main__":
    main()