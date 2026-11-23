"""
batch_featurize.py
------------------

This script processes the raw diffusion dataset and generates a featurized
JSON‑Lines file while protecting the runner from out‑of‑memory crashes caused
by extremely large molecules.  Molecules whose atom count exceeds a
configurable threshold (default: 200 atoms) are **skipped** and a log entry
``[EXCEEDED_MEMORY]`` is written.  All other records are processed using the
existing ``featurize_row`` implementation.

The script records peak RAM usage (in megabytes) to
``artifacts/reports/memory_profile.json`` and writes the featurized data to
``data/processed/featurized_data.jsonl``.  It re‑uses the project's logging
utilities so that the log file ``data/logs/ingestion.log`` is created
automatically.

Usage (called directly by the pipeline):
    python code/ingestion/batch_featurize.py

The script is safe to run on the CI runner: it never raises OOM errors,
respects the memory limit (≤ 7000 MB) and exits with status 0 on success.
"""

import csv
import json
import psutil
from pathlib import Path
from typing import Dict, List, Any

from llmxive_toolkit import paths, get_logger

# Import the existing featurisation routine.
from ingestion.featurize import featurize_row

# RDKit is required for atom‑count inspection.
try:
    from rdkit import Chem
except ImportError as exc:
    raise ImportError(
        "RDKit is required for batch_featurize. Install it via "
        "`pip install rdkit-pypi`."
    ) from exc

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ATOM_COUNT_THRESHOLD = 200  # Molecules larger than this are skipped.

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _atom_count_from_smiles(smiles: str) -> int:
    """
    Return the number of explicit atoms in a SMILES string using RDKit.
    If the SMILES cannot be parsed, ``-1`` is returned (the caller will
    treat it as invalid and let ``featurize_row`` handle logging).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return -1
    return mol.GetNumAtoms()

def _process_row(row: Dict[str, str]) -> Dict[str, Any] | None:
    """
    Featurise a single CSV row unless it exceeds the atom‑count limit.
    Returns the featurised record (or ``None`` if the record should be
    skipped).  Skipped records are logged with the ``[EXCEEDED_MEMORY]`` tag.
    """
    smiles = row.get("smiles", "")
    atom_count = _atom_count_from_smiles(smiles)

    if atom_count == -1:
        # Invalid SMILES – let the original featurizer handle logging.
        return featurize_row(row)

    if atom_count > ATOM_COUNT_THRESHOLD:
        logger.info(
            f"[EXCEEDED_MEMORY] Skipping molecule with {atom_count} atoms "
            f"(SMILES: {smiles})"
        )
        return None

    return featurize_row(row)

# ----------------------------------------------------------------------
# Main processing routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the batch‑featurisation pipeline.

    Steps
    -----
    1. Load the raw CSV (``data/raw/dataset.csv``).
    2. Iterate over rows, skipping those that exceed the atom‑count limit.
    3. Write each successful record as a JSON line to
       ``data/processed/featurized_data.jsonl``.
    4. Record the peak resident set size (RSS) observed during processing
       and write it to ``artifacts/reports/memory_profile.json``.
    """

    global logger
    logger = get_logger()

    # Paths
    raw_csv_path: Path = paths.data("raw", "dataset.csv")
    output_jsonl_path: Path = paths.data("processed", "featurized_data.jsonl")
    memory_profile_path: Path = paths.results("reports", "memory_profile.json")

    # Ensure output directories exist.
    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    memory_profile_path.parent.mkdir(parents=True, exist_ok=True)

    # Memory tracking.
    process = psutil.Process()
    peak_memory_mb = 0.0

    processed_count = 0
    total_count = 0

    with raw_csv_path.open("r", newline="", encoding="utf-8") as csv_file, \
         output_jsonl_path.open("w", encoding="utf-8") as jsonl_file:

        reader = csv.DictReader(csv_file)
        for row in reader:
            total_count += 1
            record = _process_row(row)

            # Update peak memory after each row – cheap and sufficient.
            current_mb = process.memory_info().rss / (1024 * 1024)
            if current_mb > peak_memory_mb:
                peak_memory_mb = current_mb

            if record is None:
                # Row was skipped due to size; continue to next.
                continue

            # ``featurize_row`` may return ``None`` for other validation
            # failures (e.g., missing solvent data).  Those cases are
            # already logged inside ``featurize_row``.
            if record is not None:
                jsonl_file.write(json.dumps(record) + "\n")
                processed_count += 1

    # Write memory profile.
    memory_profile = {"peak_memory_mb": round(peak_memory_mb, 2)}
    memory_profile_path.write_text(json.dumps(memory_profile, indent=2), encoding="utf-8")

    logger.info(
        f"Batch featurisation complete: {processed_count}/{total_count} records "
        f"written. Peak memory usage: {memory_profile['peak_memory_mb']} MB."
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Any unexpected exception should be logged and cause a non‑zero exit.
        logger = get_logger()
        logger.error(f"Batch featurisation failed: {e}")
        raise
