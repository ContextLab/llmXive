import os
import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_python311() -> Path:
    """
    Locate a Python 3.11 executable on the system.
    Checks common names and paths. Returns the path if found, else raises FileNotFoundError.
    """
    candidates = [
        "python3.11",
        "python3.11.exe",
        "python3", 
        "python"
    ]
    
    # Try to find via sys.executable if it matches 3.11
    if sys.version_info[:2] == (3, 11):
        logger.info(f"Using current interpreter: {sys.executable}")
        return Path(sys.executable)

    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and "3.11" in result.stdout:
                logger.info(f"Found Python 3.11 at: {candidate}")
                return Path(candidate)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    # Fallback: try to find in common installation paths (Windows/Linux/macOS)
    common_paths = [
        Path("/usr/bin/python3.11"),
        Path("/usr/local/bin/python3.11"),
        Path("C:\\Python311\\python.exe"),
        Path(os.environ.get("PROGRAMFILES", "C:\\Program Files") + "\\Python311\\python.exe")
    ]
    
    for p in common_paths:
        if p.exists():
            # Verify version
            try:
                result = subprocess.run([str(p), "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
                if "3.11" in result.stdout:
                    logger.info(f"Found Python 3.11 at: {p}")
                    return p
            except Exception:
                continue

    raise FileNotFoundError(
        "Could not find a Python 3.11 interpreter. "
        "Please install Python 3.11 and ensure it is in your PATH or set the PYTHON311 environment variable."
    )

def ensure_venv(venv_path: Path, python_executable: Path) -> bool:
    """
    Create a virtual environment at venv_path using the specified python executable.
    Returns True if successful or if it already exists and is valid.
    """
    if venv_path.exists():
        logger.info(f"Virtual environment already exists at {venv_path}. Verifying...")
        # Simple check: does bin/python (or Scripts\python.exe) exist?
        bin_dir = "Scripts" if os.name == "nt" else "bin"
        venv_python = venv_path / bin_dir / ("python.exe" if os.name == "nt" else "python")
        if not venv_python.exists():
            logger.warning(f"Existing venv at {venv_path} appears corrupted. Recreating...")
            try:
                subprocess.run([str(python_executable), "-m", "venv", str(venv_path)], check=True)
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to recreate venv: {e}")
                return False
        logger.info("Virtual environment is valid.")
        return True

    logger.info(f"Creating virtual environment at {venv_path} using {python_executable}...")
    try:
        subprocess.run(
            [str(python_executable), "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return False

def ensure_pip(venv_path: Path) -> bool:
    """
    Ensure pip is installed and upgraded in the virtual environment.
    """
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    pip_executable = venv_path / bin_dir / ("pip.exe" if os.name == "nt" else "pip")
    
    if not pip_executable.exists():
        # Try to ensure pip is present (usually created by venv, but just in case)
        logger.info("pip not found in venv. Attempting to bootstrap...")
        python_executable = venv_path / bin_dir / ("python.exe" if os.name == "nt" else "python")
        try:
            subprocess.run(
                [str(python_executable), "-m", "ensurepip", "--upgrade"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to bootstrap pip: {e}")
            return False

    logger.info("Upgrading pip...")
    try:
        subprocess.run(
            [str(pip_executable), "install", "--upgrade", "pip"],
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to upgrade pip: {e}")
        return False

def main():
    """
    Main entry point to initialize the Python 3.11 virtual environment.
    Creates the venv at ./venv in the project root.
    """
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / "venv"
    
    logger.info(f"Project root: {project_root}")
    
    try:
        python_executable = find_python311()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if not ensure_venv(venv_path, python_executable):
        logger.error("Failed to initialize virtual environment.")
        sys.exit(1)
    
    if not ensure_pip(venv_path):
        logger.error("Failed to ensure pip is ready.")
        sys.exit(1)
    
    logger.info("Virtual environment initialization complete.")
    logger.info(f"Activate with: source {venv_path / 'bin' / 'activate'} (Linux/Mac) or {venv_path / 'Scripts' / 'activate'} (Windows)")

if __name__ == "__main__":
    main()