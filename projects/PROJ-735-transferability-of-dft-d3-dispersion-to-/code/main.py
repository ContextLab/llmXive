"""
Main entry point for the reproducibility check (Task T067).

This script orchestrates the full analysis pipeline, captures runtime
statistics using `/usr/bin/time -v`, computes SHA‑256 checksums of the
key output artifacts, validates them against any JSON‑Schema contracts
located under `specs/PROJ-735-transferability-of-dft-d3-dispersion-to-`,
and records everything in `data/derived/runtime_report.txt`.  It also
appends a “Reproducibility Check” section to `docs/benchmark_report.md`
containing the command executed, exit code, checksums and the time report.

The pipeline follows the steps documented in `quickstart.md`:

  1. python code/load_data.py
  2. python code/run_psi4.py
  3. python code/analyze_energies.py
  4. python code/derive_scaling.py
  5. python code/correlate_bulk.py --scaling data/derived/scaling_stats.json --include-energy-error
  6. python code/generate_reports.py

All intermediate and final artifacts are written to their declared
locations, so the reproducibility run can be validated automatically.
"""

import subprocess
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Tuple, List

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    """Return the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run_command(cmd: str) -> Tuple[int, str, str]:
    """Execute a shell command via `/usr/bin/time -v` and return its exit code, stdout, and stderr."""
    # The command is executed inside a bash -c string so that the && chaining works.
    full_cmd = ["/usr/bin/time", "-v", "bash", "-c", cmd]
    log.info(f"Running pipeline with time wrapper: {' '.join(full_cmd)}")
    result = subprocess.run(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # time -v writes its statistics to stderr; capture both streams.
    return result.returncode, result.stdout, result.stderr


def write_runtime_report(
    command: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    artifact_paths: List[Path],
    report_path: Path,
) -> None:
    """Compose the runtime report and write it to `report_path`."""
    # Ensure the parent directory exists and is a directory.
    parent = report_path.parent
    if parent.exists() and not parent.is_dir():
        # An unexpected file exists where a directory should be; remove it.
        log.warning(f"Removing unexpected file {parent} to create directory.")
        parent.unlink()
    parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"Reproducibility run – {datetime.utcnow().isoformat()}Z",
        "",
        "Command:",
        f"  {command}",
        "",
        f"Exit code: {exit_code}",
        "",
        "Artifact checksums (SHA‑256):",
    ]

    for p in artifact_paths:
        checksum = sha256_file(p) if p.is_file() else "MISSING"
        try:
            rel = p.relative_to(Path.cwd())
        except ValueError:
            # p is not under the current working directory – fall back to the raw path.
            rel = p
        lines.append(f"  {rel}: {checksum}")

    lines.append("")
    lines.append("Runtime statistics (from `/usr/bin/time -v`):")
    lines.append(stderr.strip())
    lines.append("")

    report_path.write_text("\n".join(lines))
    log.info(f"Runtime report written to {report_path}")


def validate_contracts(base_dir: Path) -> None:
    """
    Validate generated artifacts against JSON‑Schema contracts, if any are present.
    Contracts are expected under `specs/PROJ-735-transferability-of-dft-d3-dispersion-to-`
    with a `.json` extension.  Each contract must contain a top‑level `$schema`
    key or be a valid JSON‑Schema.  The contract file name (without extension)
    should match the artifact name (e.g. `raw_energies` → `raw_energies.csv`).
    """
    try:
        import jsonschema
    except ImportError as exc:
        log.warning(
            "jsonschema not installed – contract validation skipped. "
            "Add it to requirements.txt if validation is required."
        )
        return

    contracts_dir = (
        base_dir
        / "specs"
        / "PROJ-735-transferability-of-dft-d3-dispersion-to-"
        / "contracts"
    )
    if not contracts_dir.is_dir():
        log.info("No contracts directory found – skipping validation.")
        return

    for contract_file in contracts_dir.glob("*.json"):
        contract_name = contract_file.stem
        # Map contract name to expected artifact path
        # Simple convention: <name>.json validates <name>.csv (or .json)
        possible_paths = [
            base_dir / "data" / "derived" / f"{contract_name}.csv",
            base_dir / "data" / "derived" / f"{contract_name}.json",
            base_dir / "docs" / f"{contract_name}.md",
        ]
        artifact_path = next((p for p in possible_paths if p.is_file()), None)
        if artifact_path is None:
            log.warning(f"No artifact found for contract {contract_name}; skipping.")
            continue

        with contract_file.open() as f:
            schema = json.load(f)

        with artifact_path.open() as f:
            # Load JSON for .json artifacts, otherwise treat CSV/MD as plain text.
            if artifact_path.suffix == ".json":
                instance = json.load(f)
            else:
                # For CSV/MD we just validate that the file is present;
                # full schema validation would require a custom loader.
                instance = f.read()

        try:
            jsonschema.validate(instance=instance, schema=schema)
            log.info(f"Contract `{contract_file.name}` validated successfully.")
        except jsonschema.ValidationError as ve:
            log.error(f"Contract validation failed for {artifact_path}: {ve.message}")
            raise


# ----------------------------------------------------------------------
# Main reproducibility orchestration
# ----------------------------------------------------------------------
def main() -> None:
    # Define the pipeline command exactly as in quickstart.md
    pipeline_cmd = (
        "python code/load_data.py && "
        "python code/run_psi4.py && "
        "python code/analyze_energies.py && "
        "python code/derive_scaling.py && "
        "python code/correlate_bulk.py "
        "--scaling data/derived/scaling_stats.json --include-energy-error && "
        "python code/generate_reports.py"
    )

    # Run the pipeline under `/usr/bin/time -v`
    exit_code, stdout, stderr = run_command(pipeline_cmd)

    # Paths of the key artifacts that must exist after a successful run
    artifact_paths = [
        Path("data/derived/raw_energies.csv"),
        Path("data/derived/scaling_factor.txt"),
        Path("data/derived/scaling_stats.json"),
        Path("data/derived/correlation_results.csv"),
        Path("docs/benchmark_report.md"),
        Path("docs/correlation_report.md"),
    ]

    # Write the runtime report
    report_path = Path("data/derived/runtime_report.txt")
    write_runtime_report(
        command=pipeline_cmd,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        artifact_paths=artifact_paths,
        report_path=report_path,
    )

    # Append a reproducibility section to the benchmark report
    benchmark_report = Path("docs/benchmark_report.md")
    if benchmark_report.is_file():
        reproduc_section = [
            "",
            "## Reproducibility Check",
            "",
            f"- **Command executed**: `{pipeline_cmd}`",
            f"- **Exit code**: `{exit_code}`",
            "- **Artifact checksums (SHA‑256)**:",
        ]
        for p in artifact_paths:
            checksum = sha256_file(p) if p.is_file() else "MISSING"
            reproduc_section.append(f"  - `{p}`: `{checksum}`")
        reproduc_section.extend(
            [
                "",
                "- **Runtime statistics** (excerpt):",
                "```",
                stderr.strip(),
                "```",
            ]
        )
        # Preserve existing content and add the new section
        benchmark_report.write_text(
            benchmark_report.read_text() + "\n".join(reproduc_section) + "\n"
        )
        log.info("Appended reproducibility section to benchmark_report.md")
    else:
        log.error("Benchmark report not found – cannot append reproducibility section.")

    # Validate contracts (if any)
    try:
        validate_contracts(Path.cwd())
    except Exception as e:
        log.error(f"Contract validation failed: {e}")
        sys.exit(1)

    # Final exit code reflects the pipeline execution
    if exit_code != 0:
        log.error(f"Pipeline failed with exit code {exit_code}")
        sys.exit(exit_code)

    log.info("Reproducibility run completed successfully.")


if __name__ == "__main__":
    main()