import os
import subprocess
import sys
import shutil
from pathlib import Path

def find_python311() -> Path:
    """
    Locate a Python 3.11 executable on the system.
    Checks common locations and the system PATH.
    Raises FileNotFoundError if not found.
    """
    possible_names = ["python3.11", "python3", "python"]
    python_path = None

    # Try specific python3.11 first, then generic python3
    for name in ["python3.11", "python3"]:
        try:
            result = subprocess.run(
                [name, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            if "3.11" in result.stdout or "3.11" in result.stderr:
                # Found a 3.11 version
                python_path = shutil.which(name)
                break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    if not python_path:
        # Fallback to generic python if python3.11 not found explicitly
        # (Assuming the environment running this script is 3.11)
        python_path = sys.executable
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if "3.11" not in version:
            raise FileNotFoundError(
                f"Could not find Python 3.11. "
                f"Current interpreter is {version} at {python_path}. "
                f"Please ensure python3.11 is installed and in PATH."
            )

    return Path(python_path)

def main():
    """
    Initialize a Python 3.11 virtual environment in the project root.
    Project root is expected to be the directory containing this script's parent 'code' directory.
    """
    # Determine project root: code/setup_venv.py -> parent is project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    venv_path = project_root / "venv"

    print(f"Project Root: {project_root}")
    print(f"Target Venv: {venv_path}")

    if venv_path.exists():
        print("Virtual environment already exists at 'venv/'. Skipping creation.")
        print("To recreate, manually remove the 'venv/' directory.")
        return 0

    try:
        python_exec = find_python311()
        print(f"Using Python executable: {python_exec}")

        # Create the virtual environment
        subprocess.run(
            [str(python_exec), "-m", "venv", str(venv_path)],
            check=True
        )
        print(f"Successfully created virtual environment at '{venv_path}'.")
        print(f"Activate with: source {venv_path}/bin/activate (Linux/Mac) or {venv_path}\\Scripts\\activate (Windows)")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
