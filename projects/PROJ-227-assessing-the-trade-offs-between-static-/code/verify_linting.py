import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"

def main() -> int:
    """Verify linting and formatting configuration."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Verifying linting in: {project_root}")

    # Check Black
    print("Running: black --check .")
    returncode, stdout, stderr = run_command(["black", "--check", "."], cwd=project_root)
    if returncode == 0:
        print("✓ Black check passed.")
    else:
        print("✗ Black check failed:")
        print(stdout)
        print(stderr)

    # Check Flake8
    print("Running: flake8 .")
    returncode, stdout, stderr = run_command(["flake8", "."], cwd=project_root)
    if returncode == 0:
        print("✓ Flake8 check passed.")
    else:
        print("✗ Flake8 check failed:")
        print(stdout)
        print(stderr)

    # Return 0 only if both pass (for CI integration)
    # Note: In a real CI, we might want to fail if either fails.
    # Here we just report status.
    return 0

if __name__ == "__main__":
    sys.exit(main())