"""
Script to verify ruff and black configuration.
Runs checks on the 'src' directory (which may be empty or minimal at this stage)
and saves the validation log to data/logs/linting_config.json.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Add project root to path if running from scripts
project_root = Path(__file__).resolve().parent.parent
src_dir = project_root / "src"
data_logs_dir = project_root / "data" / "logs"

def ensure_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def run_command(cmd: list, cwd: Path) -> dict:
    """Run a shell command and capture output."""
    result = {
        "command": " ".join(cmd),
        "success": False,
        "stdout": "",
        "stderr": "",
        "returncode": -1
    }
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["returncode"] = proc.returncode
        result["success"] = (proc.returncode == 0)
    except subprocess.TimeoutExpired:
        result["stderr"] = "Command timed out"
        result["returncode"] = -1
    except FileNotFoundError:
        result["stderr"] = f"Command not found: {cmd[0]}"
        result["returncode"] = -1
    except Exception as e:
        result["stderr"] = str(e)
    return result

def main():
    print(f"Verifying linting configuration in {project_root}...")
    
    # Ensure directories exist
    ensure_dir(data_logs_dir)
    ensure_dir(src_dir)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "project_root": str(project_root),
        "checks": {}
    }

    # 1. Run Ruff Check
    print("Running ruff check...")
    ruff_cmd = [sys.executable, "-m", "ruff", "check", str(src_dir)]
    # If ruff is not installed as a module, try direct command
    if not Path(sys.executable).parent / "ruff.exe" if os.name == "nt" else Path(sys.executable).parent / "ruff":
        # Fallback to just 'ruff' if installed globally
        ruff_cmd = ["ruff", "check", str(src_dir)]
    
    ruff_result = run_command(ruff_cmd, project_root)
    log_entry["checks"]["ruff_check"] = ruff_result

    # 2. Run Black Check
    print("Running black check...")
    black_cmd = [sys.executable, "-m", "black", "--check", str(src_dir)]
    # Fallback to just 'black'
    if not Path(sys.executable).parent / "black.exe" if os.name == "nt" else Path(sys.executable).parent / "black":
        black_cmd = ["black", "--check", str(src_dir)]

    black_result = run_command(black_cmd, project_root)
    log_entry["checks"]["black_check"] = black_result

    # 3. Verify Config Files Exist
    print("Checking configuration files...")
    config_files = {
        "pyproject.toml": (project_root / "pyproject.toml").exists(),
        "ruff.toml": (project_root / "ruff.toml").exists(),
        ".ruff.toml": (project_root / ".ruff.toml").exists(),
        ".black.toml": (project_root / ".black.toml").exists()
    }
    log_entry["config_files_present"] = config_files

    # Determine overall status
    ruff_pass = ruff_result["success"]
    black_pass = black_result["success"]
    
    # Note: If src/ is empty, black/ruff might return 0 (success) or 1 (no files found) depending on version.
    # We consider it a pass if the command runs without crashing and finds no violations.
    # However, if they explicitly say "no files found", that's also a success for configuration validity.
    if "No Python files are present" in ruff_result["stdout"] or "No Python files are present" in ruff_result["stderr"]:
        ruff_pass = True
        log_entry["checks"]["ruff_check"]["note"] = "No Python files found in src/, configuration valid."
    
    if "No Python files are present" in black_result["stdout"] or "No Python files are present" in black_result["stderr"]:
        black_pass = True
        log_entry["checks"]["black_check"]["note"] = "No Python files found in src/, configuration valid."

    log_entry["overall_status"] = "PASS" if (ruff_pass and black_pass) else "FAIL"
    log_entry["summary"] = {
        "ruff": "PASS" if ruff_pass else "FAIL",
        "black": "PASS" if black_pass else "FAIL"
    }

    # Write log
    output_path = data_logs_dir / "linting_config.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2)

    print(f"Log written to {output_path}")
    print(f"Overall Status: {log_entry['overall_status']}")

    # Exit with appropriate code
    if log_entry["overall_status"] == "FAIL":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
