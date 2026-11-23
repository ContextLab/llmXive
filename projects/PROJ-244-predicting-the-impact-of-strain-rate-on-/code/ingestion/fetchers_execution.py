"""
Execution wrapper for the ingestion fetcher.

This script simply invokes the main entry point of ``code/ingestion/fetchers.py``
with the arguments required by the Quickstart guide.  It exists so that the
automated runner can execute the fetcher and produce the expected artefacts
without modifying the Quickstart documentation.
"""
import subprocess
import sys
from pathlib import Path

# Resolve the project root (the directory containing this script)
project_root = Path(__file__).resolve().parent.parent

# Build the command line to invoke the fetcher
fetcher_script = project_root / "code" / "ingestion" / "fetchers.py"
cmd = [
    sys.executable,
    str(fetcher_script),
    "--mode",
    "simulated",
    "--output",
    str(project_root / "data" / "raw" / "simulated_tensile.csv"),
]

# Run the command and forward stdout/stderr
result = subprocess.run(cmd, capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

# Exit with the same return code so the runner sees success/failure
sys.exit(result.returncode)