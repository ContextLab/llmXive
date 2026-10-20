"""
Verification script for T002.

1. Runs `ruff --quiet .` and `black --check .` to ensure code style compliance.
2. Loads the example environment file and checks that the required
   variables are accessible via the project's configuration getter.
"""

import subprocess
import sys
import os
from pathlib import Path

# Load the example .env file so that os.getenv picks up the variables.
try:
    from dotenv import load_dotenv
except ImportError as e:
    print("python-dotenv is required for this verification script.", file=sys.stderr)
    sys.exit(1)

# Path to the .env.example at the repository root
env_path = Path(__file__).resolve().parents[2] / ".env.example"
if not env_path.is_file():
    print(f".env.example not found at expected location: {env_path}", file=sys.stderr)
    sys.exit(1)

load_dotenv(dotenv_path=env_path, override=True)

# 1. Linting checks
def run_cmd(command: list[str]) -> int:
    """Run a command and return its exit code."""
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Command {' '.join(command)} failed with exit code {result.returncode}", file=sys.stderr)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    return result.returncode

# Ruff
ruff_exit = run_cmd([sys.executable, "-m", "ruff", "--quiet", "."])
# Black
black_exit = run_cmd([sys.executable, "-m", "black", "--check", "."])

if ruff_exit != 0 or black_exit != 0:
    sys.exit(1)

# 2. Environment variable verification via the project's config getter
try:
    # Import the project's config module
    from code.config import get
except Exception as e:
    print(f"Failed to import config module: {e}", file=sys.stderr)
    sys.exit(1)

ncbi_key = get("NCBI_API_KEY")
pmdb_token = get("PMDB_API_TOKEN")

if not ncbi_key or not pmdb_token:
    print("Environment variables NCBI_API_KEY or PMDB_API_TOKEN are missing or empty.", file=sys.stderr)
    sys.exit(1)

print("All checks passed.")
sys.exit(0)