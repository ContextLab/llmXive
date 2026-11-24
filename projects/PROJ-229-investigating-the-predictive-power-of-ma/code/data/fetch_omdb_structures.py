"""
fetch_omdb_structures.py

This script downloads crystal structure CIF files for each material listed in the
`pcm.parquet` dataset (produced by T002) from the Open Materials Database (OMDB)
structures HuggingFace dataset.

It writes each CIF to ``data/raw/omdb_structures/<material_id>.cif``.  The script
aborts with an exception if the remote fetch fails or if fewer than 80 % of the
requested material IDs are found, satisfying the verification test
``tests/integration/test_fetch_omdb.py``.
"""

import logging
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
LOG = get_logger(__name__)

# Input parquet produced by T002
INPUT_PARQUET = paths.data("raw", "pcm.parquet")

# Output directory for CIF files
OUTPUT_DIR: Path = paths.data("raw", "omdb_structures")

# Minimum fraction of material IDs that must have a CIF
MIN_COVERAGE = 0.80

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_material_ids(parquet_path: Path) -> set[str]:
    """
    Load the set of material IDs from the PCM parquet file.

    Parameters
    ----------
    parquet_path: Path
        Path to the parquet file containing the PCM dataset.

    Returns
    -------
    set[str]
        A set of material identifier strings (e.g., ``mp-1234``).
    """
    LOG.info("Loading material IDs from %s", parquet_path)
    df = pd.read_parquet(parquet_path, engine="pyarrow")
    if "material_id" not in df.columns:
        raise KeyError(
            "Column 'material_id' not found in PCM parquet. "
            "Available columns: %s" % ", ".join(df.columns)
        )
    ids = set(df["material_id"].astype(str).unique())
    LOG.info("Found %d unique material IDs.", len(ids))
    return ids

def _download_cifs(material_ids: set[str], output_dir: Path) -> int:
    """
    Stream the OMDB structures dataset and write CIF files for the requested IDs.

    Parameters
    ----------
    material_ids : set[str]
        The set of material IDs we need CIFs for.
    output_dir : Path
        Directory where CIF files will be written.

    Returns
    -------
    int
        Number of CIF files successfully written.
    """
    LOG.info(
        "Starting download of CIFs from HuggingFace dataset 'omdb/structures' (streaming)."
    )
    # The OMDB structures dataset is provided as a streaming dataset.
    # It contains at least the fields ``material_id`` and ``cif`` (CIF content as a string).
    dataset = load_dataset(
        "omdb/structures", split="train", streaming=True
    )  # type: ignore[arg-type]

    written = 0
    needed = set(material_ids)  # copy we will shrink as we find matches

    for record in dataset:
        mat_id = str(record.get("material_id"))
        if mat_id in needed:
            cif_content = record.get("cif")
            if not cif_content:
                LOG.warning("CIF content missing for material_id %s", mat_id)
                continue

            cif_path = output_dir / f"{mat_id}.cif"
            # Ensure parent directory exists (paths.data already did)
            with open(cif_path, "w", encoding="utf-8") as f:
                f.write(cif_content)
            written += 1
            needed.remove(mat_id)

            LOG.debug("Wrote CIF for %s (%d remaining)", mat_id, len(needed))

            # Early exit if we have collected all requested CIFs
            if not needed:
                LOG.info("All requested CIFs have been downloaded.")
                break

    LOG.info("Downloaded %d CIF files.", written)
    return written

def main() -> None:
    """
    Entry‑point for ``python -m code.data.fetch_omdb_structures``.
    """
    LOG.info("Fetching OMDB structure CIFs...")
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: read material IDs from the PCM parquet file
    material_ids = _load_material_ids(INPUT_PARQUET)

    if not material_ids:
        raise RuntimeError("No material IDs found in the input parquet file.")

    # Step 2: download CIFs
    num_written = _download_cifs(material_ids, OUTPUT_DIR)

    # Step 3: verify coverage
    coverage = num_written / len(material_ids)
    LOG.info(
        "CIF coverage: %.2f%% (%d of %d IDs)",
        coverage * 100,
        num_written,
        len(material_ids),
    )
    if coverage < MIN_COVERAGE:
        raise AssertionError(
            f"CIF coverage {coverage:.2%} is below the required {MIN_COVERAGE:.2%}."
        )

    LOG.info("OMDB CIF fetching completed successfully.")

if __name__ == "__main__":
    main()
