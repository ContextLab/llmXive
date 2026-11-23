"""
Script to install project dependencies listed in requirements.txt.
It runs `pip install -r requirements.txt` and writes the installation
log to `data/results/requirements_install_log.txt`. The script exits with
a non‑zero status if the installation fails, causing the pipeline to halt.
"""
import subprocess
import sys
from pathlib import Path

def main() -> None:
    # Resolve the path to the repository root's requirements.txt
    repo_root = Path(__file__).resolve().parents[1]
    requirements_path = repo_root / "requirements.txt"

    if not requirements_path.is_file():
        print(f"Requirements file not found at {requirements_path}", file=sys.stderr)
        sys.exit(1)

    # Run pip install in a subprocess
    print(f"Installing dependencies from {requirements_path} ...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
        capture_output=True,
        text=True,
    )

    # Write stdout and stderr to a log file for audit
    log_path = repo_root / "data" / "results" / "requirements_install_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        f.write("=== pip install stdout ===\n")
        f.write(result.stdout or "")
        f.write("\n=== pip install stderr ===\n")
        f.write(result.stderr or "")

    # Report status
    if result.returncode == 0:
        print("✅ Dependencies installed successfully.")
    else:
        print("❌ pip install failed. See log for details.", file=sys.stderr)
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
