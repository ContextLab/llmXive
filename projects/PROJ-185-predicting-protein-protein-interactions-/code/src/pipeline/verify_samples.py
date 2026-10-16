"""
verify_samples.py
-----------------

This script validates that the total number of retained GEO samples for each
species meets the minimum required (`min_samples`) defined in
``src/config/species.yaml``. It is part of the data‑acquisition phase
(Task T007).

Behaviour
----------
* Reads ``species.yaml`` to obtain, for every species, the list of GEO
  accession IDs to be processed and the required ``min_samples`` threshold.
* For each accession, looks for a downloaded ``.tar.gz`` archive under
  ``data/raw/`` (the output of Task T006).
* Inspects the series‑matrix file inside the archive and counts the number
  of samples (columns) present.
* Sums the sample counts across all retained series for a species.
* If the total is **greater than or equal** to the required minimum, writes
  an ``INFO`` entry to ``pipeline.log``.
* If the total is **less** than the required minimum, writes an ``ERROR``
  entry to ``pipeline.log`` and aborts the pipeline by raising ``SystemExit``.
  The raised exception contains a concise message that the integration
  test ``tests/integration/test_sample_power.py`` expects.

Logging
-------
The script writes a single JSON‑Line entry per species to
``src/logs/pipeline.log`` (the path is created via ``llmxive_toolkit.paths``).
The schema follows ``contracts/pipeline_log.schema.yaml`` and includes the
fields ``timestamp``, ``level``, ``message`` and ``schema_version``.

Usage
-----
The script is invoked automatically by the ``make all`` target after the
download step, but it can also be run manually:

```bash
python code/src/pipeline/verify_samples.py
```

It exits with status ``0`` on success and ``1`` when any species fails the
sample‑power check.
"""

import sys
import json
import yaml
import tarfile
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_species_config() -> dict:
    """Load ``src/config/species.yaml``."""
    config_path = Path("src") / "config" / "species.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(f"Species configuration not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _extract_series_ids(entry: dict) -> list[str]:
    """
    Return a list of GEO accession IDs for a species entry.

    The YAML structure may vary between projects; this function supports
    the common layouts used in the repository:

    * ``accessions`` – a list of IDs
    * ``series`` – a list of IDs
    * ``geo_ids`` – a list of IDs
    * a plain list (when the species maps directly to a list)
    """
    if isinstance(entry, list):
        return entry
    if not isinstance(entry, dict):
        raise ValueError(f"Unexpected species entry format: {entry!r}")

    for key in ("accessions", "series", "geo_ids"):
        if key in entry and isinstance(entry[key], list):
            return entry[key]

    # Fallback: if the dict contains a single key that is not a known
    # metadata field, treat its value as the list of series.
    for k, v in entry.items():
        if k not in ("held_out_series", "min_samples") and isinstance(v, list):
            return v

    raise ValueError(f"Could not determine series list for entry: {entry!r}")

def _count_samples_in_tar(tar_path: Path) -> int:
    """
    Open a GEO ``.tar.gz`` archive and count the number of samples.

    The archive contains a file ending with ``_series_matrix.txt``. The
    first line after ``#!Series_matrix_table_begin`` starts with ``ID_REF`` and
    is followed by one column per sample. The number of samples is therefore
    ``len(columns) - 1``.
    """
    with tarfile.open(tar_path, "r:gz") as tar:
        # Find the series‑matrix file
        matrix_member = None
        for member in tar.getmembers():
            if member.name.endswith("_series_matrix.txt"):
                matrix_member = member
                break
        if matrix_member is None:
            raise FileNotFoundError(
                f"No series‑matrix file found in archive {tar_path}"
            )

        f = tar.extractfile(matrix_member)
        if f is None:
            raise RuntimeError(f"Failed to extract {matrix_member.name} from {tar_path}")

        # Decode as UTF‑8; GEO matrix files are plain text
        for line_bytes in f:
            line = line_bytes.decode("utf-8", errors="replace").strip()
            if line.startswith("ID_REF"):
                # Columns are tab‑separated; first column is gene ID
                cols = line.split("\t")
                return max(0, len(cols) - 1)
        raise RuntimeError(f"Unable to locate header line in {matrix_member.name}")

def _write_log_entry(level: str, message: str) -> None:
    """
    Append a JSON‑Line entry to ``src/logs/pipeline.log``.
    The entry complies with ``contracts/pipeline_log.schema.yaml``.
    """
    log_path = paths.logs("pipeline.log")
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
        "schema_version": "1.0",
    }
    # Ensure the parent directory exists (paths.* does this)
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(entry) + "\n")

# ----------------------------------------------------------------------
# Core verification routine
# ----------------------------------------------------------------------
def verify_species_samples() -> None:
    """
    Perform the sample‑power check for every species defined in
    ``species.yaml``.
    """
    config = _load_species_config()
    any_failure = False

    for species, entry in config.items():
        # Extract required fields
        try:
            min_samples = int(entry.get("min_samples", 0))
        except Exception as exc:
            raise ValueError(f"Invalid or missing 'min_samples' for {species}: {exc}")

        series_ids = _extract_series_ids(entry)

        total_samples = 0
        for gid in series_ids:
            tar_path = paths.data("raw", f"{gid}.tar.gz")
            if not tar_path.is_file():
                # The downloader skips series with <30 samples; missing files are
                # simply ignored for the power calculation.
                continue
            try:
                total_samples += _count_samples_in_tar(tar_path)
            except Exception as exc:
                # Log the problem but continue with other series; the test suite
                # expects a clean abort only when the *total* is insufficient.
                _write_log_entry(
                    "WARNING",
                    f"Failed to count samples for {gid} ({species}): {exc}",
                )

        if total_samples >= min_samples:
            _write_log_entry(
                "INFO",
                f"Sufficient samples for {species}: {total_samples} >= {min_samples}",
            )
        else:
            msg = (
                f"Insufficient samples for {species}: "
                f"{total_samples} < {min_samples}"
            )
            _write_log_entry("ERROR", msg)
            any_failure = True

    if any_failure:
        # Raising SystemExit with the message satisfies the integration test.
        raise SystemExit("Sample power check failed – see pipeline.log for details.")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Execute the verification step.

    Returns
    -------
    int
        Exit code (0 = success, 1 = failure).
    """
    try:
        verify_species_samples()
    except SystemExit as se:
        # Propagate the exit status expected by the test harness.
        sys.stderr.write(str(se) + "\n")
        return 1
    except Exception as exc:
        _write_log_entry("ERROR", f"Unexpected error during sample verification: {exc}")
        sys.stderr.write(f"Unexpected error: {exc}\n")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())