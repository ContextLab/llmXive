"""
Scaffold script for the molecular property prediction project.

This script performs the following actions required by task T001:
  1. Creates the canonical directory tree:
     code/, code/data/, code/models/, code/evaluation/, code/utils/,
     tests/, data/raw/, data/processed/, data/generated/,
     results/, logs/, config/
  2. Writes deterministic random seeds to ``config/seeds.yaml``.
  3. Runs ``python -m compileall -q code/`` and captures its output
     into ``logs/compileall.log``.
  4. Generates a simple ``results/structure_report.txt`` that lists all
     top‑level directories created by this script.

The script is idempotent – running it a second time will not raise
errors and will simply overwrite the generated files.
"""

import sys
import subprocess
from pathlib import Path

import yaml

# ----------------------------------------------------------------------
# Helper to create a directory (including parents) if it does not exist.
# ----------------------------------------------------------------------
def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Main entry point.
# ----------------------------------------------------------------------
def main() -> None:
    root = Path.cwd()

    # ------------------------------------------------------------------
    # 1. Create the canonical directory tree.
    # ------------------------------------------------------------------
    dirs_to_create = [
        root / "code",
        root / "code" / "data",
        root / "code" / "models",
        root / "code" / "evaluation",
        root / "code" / "utils",
        root / "tests",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "generated",
        root / "results",
        root / "logs",
        root / "config",
    ]

    for d in dirs_to_create:
        _mkdir(d)

    # ------------------------------------------------------------------
    # 2. Write deterministic seeds.
    # ------------------------------------------------------------------
    seeds = {
        "numpy": 42,
        "torch": 42,
        "python": 42,
    }
    seeds_path = root / "config" / "seeds.yaml"
    with seeds_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(seeds, f, sort_keys=False)

    # ------------------------------------------------------------------
    # 3. Compile all Python files under ``code/``.
    # ------------------------------------------------------------------
    compile_cmd = [sys.executable, "-m", "compileall", "-q", "code/"]
    result = subprocess.run(
        compile_cmd,
        capture_output=True,
        text=True,
    )

    compile_log_path = root / "logs" / "compileall.log"
    with compile_log_path.open("w", encoding="utf-8") as f:
        f.write(result.stdout)
        f.write(result.stderr)

    # If compilation failed, we still write the log but raise to make the
    # task clearly fail (the verifier expects a zero‑exit run).
    if result.returncode != 0:
        raise RuntimeError(
            f"compileall exited with code {result.returncode}. "
            f"See {compile_log_path} for details."
        )

    # ------------------------------------------------------------------
    # 4. Produce a simple structure report.
    # ------------------------------------------------------------------
    report_path = root / "results" / "structure_report.txt"
    with report_path.open("w", encoding="utf-8") as f:
        f.write("Project directory structure (top‑level directories only):\n")
        for d in sorted(dirs_to_create):
            # Write paths relative to the project root for readability.
            rel = d.relative_to(root)
            f.write(f"- {rel.as_posix()}\n")

    print("Scaffolding completed successfully.")
    print(f"Seeds written to: {seeds_path}")
    print(f"Compile log written to: {compile_log_path}")
    print(f"Structure report written to: {report_path}")

if __name__ == "__main__":
    main()
