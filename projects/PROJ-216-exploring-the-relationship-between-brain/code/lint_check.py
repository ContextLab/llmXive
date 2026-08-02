"""
Utility script to verify that linting (Ruff) and formatting (Black) are correctly configured
and can be run against the project codebase.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> tuple[int, str]:
    """Run a command and return (returncode, stdout)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=check
        )
        return result.returncode, result.stdout
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout + e.stderr
    except FileNotFoundError:
        return -1, f"Command not found: {cmd[0]}"

def main() -> int:
    """Check if ruff and black are installed and configured."""
    root = Path(__file__).resolve().parent.parent

    print("Checking linting and formatting tools configuration...")

    # 1. Check Ruff availability
    print("\n1. Checking Ruff installation...")
    code, output = run_command(["ruff", "--version"], check=False)
    if code != 0:
        print(f"   ERROR: Ruff not found or not executable. ({output})")
        return 1
    print(f"   OK: {output.strip()}")

    # 2. Check Black availability
    print("\n2. Checking Black installation...")
    code, output = run_command(["black", "--version"], check=False)
    if code != 0:
        print(f"   ERROR: Black not found or not executable. ({output})")
        return 1
    print(f"   OK: {output.strip()}")

    # 3. Verify configuration file exists
    print("\n3. Checking configuration file (pyproject.toml)...")
    config_file = root / "pyproject.toml"
    if not config_file.exists():
        print(f"   ERROR: {config_file} not found.")
        return 1
    
    content = config_file.read_text()
    if "[tool.black]" not in content:
        print("   ERROR: [tool.black] section missing in pyproject.toml")
        return 1
    if "[tool.ruff]" not in content:
        print("   ERROR: [tool.ruff] section missing in pyproject.toml")
        return 1
    print("   OK: Configuration sections found.")

    # 4. Run Ruff check (dry run to verify config parsing)
    print("\n4. Running Ruff check (config validation)...")
    code, output = run_command(
        ["ruff", "check", str(root / "code"), str(root / "tests")], check=False
    )
    # Ruff returns 1 if issues found, 0 if clean. We just want to ensure it runs.
    if code > 1:
        print(f"   ERROR: Ruff failed to run. ({output})")
        return 1
    if code == 0:
        print("   OK: No linting issues found.")
    else:
        print("   INFO: Linting issues found (expected if code is not yet clean), but tool is configured correctly.")
        # Don't fail here, just report

    # 5. Run Black check (dry run)
    print("\n5. Running Black check (format validation)...")
    code, output = run_command(
        ["black", "--check", str(root / "code"), str(root / "tests")], check=False
    )
    if code > 1:
        print(f"   ERROR: Black failed to run. ({output})")
        return 1
    if code == 0:
        print("   OK: Code is properly formatted.")
    else:
        print("   INFO: Formatting issues found (expected if code is not yet clean), but tool is configured correctly.")

    print("\n✅ Linting and formatting tools are correctly configured.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
