import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assuming the script is run from code/scripts or similar
    current = Path(__file__).resolve()
    # Traverse up to find the project root (where pyproject.toml or requirements.txt might be)
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() or (parent / "requirements.txt").exists():
            return parent
    # Fallback to parent of current script
    return current.parent.parent

def check_command(cmd: str) -> bool:
    """Check if a command is available in the system."""
    try:
        subprocess.run(["which", cmd], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def install_if_missing(cmd: str, package: str) -> None:
    """Install a package if the command is not available."""
    if not check_command(cmd):
        print(f"Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

def validate_config_files(project_root: Path) -> dict:
    """Validate ruff and black configuration by running them on an empty or existing src/."""
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "ruff": {"status": "unknown", "message": ""},
        "black": {"status": "unknown", "message": ""},
        "config_path": str(project_root / "pyproject.toml")
    }

    src_dir = project_root / "src"
    if not src_dir.exists():
        src_dir.mkdir(parents=True, exist_ok=True)

    # Ensure ruff and black are installed
    install_if_missing("ruff", "ruff")
    install_if_missing("black", "black")

    # Run ruff check
    try:
        # Run on src directory. If empty, it should pass or return 0.
        # We use --exit-zero to ensure we get output even if there are no files/issues
        result = subprocess.run(
            ["ruff", "check", str(src_dir)],
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )
        results["ruff"]["status"] = "success" if result.returncode == 0 else "error"
        results["ruff"]["message"] = result.stdout + result.stderr
    except Exception as e:
        results["ruff"]["status"] = "error"
        results["ruff"]["message"] = str(e)

    # Run black --check
    try:
        result = subprocess.run(
            ["black", "--check", str(src_dir)],
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )
        results["black"]["status"] = "success" if result.returncode == 0 else "error"
        results["black"]["message"] = result.stdout + result.stderr
    except Exception as e:
        results["black"]["status"] = "error"
        results["black"]["message"] = str(e)

    return results

def run_precommit_install(project_root: Path) -> dict:
    """Run pre-commit install if available."""
    result = {"status": "skipped", "message": ""}
    if check_command("pre-commit"):
        try:
            subprocess.run(
                ["pre-commit", "install"],
                cwd=str(project_root),
                capture_output=True,
                text=True
            )
            result["status"] = "success"
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)
    else:
        result["message"] = "pre-commit not installed"
    return result

def main():
    project_root = get_project_root()
    print(f"Project root: {project_root}")

    # Validate configurations
    validation_results = validate_config_files(project_root)

    # Ensure output directory exists
    logs_dir = project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    output_file = logs_dir / "linting_config.json"

    # Write results
    with open(output_file, "w") as f:
        json.dump(validation_results, f, indent=2)

    print(f"Linting validation log written to: {output_file}")
    print(json.dumps(validation_results, indent=2))

    return 0 if validation_results["ruff"]["status"] == "success" and validation_results["black"]["status"] == "success" else 1

if __name__ == "__main__":
    sys.exit(main())
