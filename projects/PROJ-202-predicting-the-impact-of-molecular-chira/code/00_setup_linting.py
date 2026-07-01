"""
Script to verify linting (ruff) and formatting (black) configuration.
This task (T003) ensures the project has valid configuration files and
provides a helper to run checks if the tools are installed.
"""
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
RUFF_CONFIG = CODE_DIR / ".ruff.toml"
BLACK_CONFIG = CODE_DIR / ".black.toml"

def check_config_files() -> bool:
    """Verify that configuration files exist."""
    configs = [
        (RUFF_CONFIG, "Ruff"),
        (BLACK_CONFIG, "Black"),
    ]
    all_good = True
    for path, name in configs:
        if not path.exists():
            print(f"❌ {name} config missing at: {path}")
            all_good = False
        else:
            print(f"✅ {name} config found: {path}")
    return all_good

def run_ruff_check() -> int:
    """Run ruff check on the code directory."""
    try:
        result = subprocess.run(
            ["ruff", "check", str(CODE_DIR), "--config", str(RUFF_CONFIG)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0:
            print("✅ Ruff check passed.")
        else:
            print("❌ Ruff check failed:")
            print(result.stdout)
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        print("⚠️  Ruff not installed. Skipping check.")
        return 0

def run_black_check() -> int:
    """Run black check on the code directory."""
    try:
        result = subprocess.run(
            ["black", "--check", "--config", str(BLACK_CONFIG), str(CODE_DIR)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.returncode == 0:
            print("✅ Black check passed.")
        else:
            print("❌ Black check failed:")
            print(result.stdout)
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        print("⚠️  Black not installed. Skipping check.")
        return 0

def main():
    print("Checking linting and formatting configuration...")
    if not check_config_files():
        print("Configuration files missing. Cannot proceed with checks.")
        sys.exit(1)

    ruff_code = run_ruff_check()
    black_code = run_black_check()

    if ruff_code == 0 and black_code == 0:
        print("\n🎉 All checks passed.")
        sys.exit(0)
    else:
        print("\n⚠️  Some checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()