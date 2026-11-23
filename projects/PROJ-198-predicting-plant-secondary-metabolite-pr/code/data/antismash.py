"""
antiSMASH 7.0 integration utilities.

This module provides three public functions required by task **T007**:

1. ``run_antismash_wrapper`` – executes antiSMASH (Docker) on one or more
   genome FASTA files, collects the resulting JSON outputs and returns a
   ``pandas.DataFrame`` with BGC count statistics per species.

2. ``parse_antismash_json`` – parses a single antiSMASH JSON file and
   returns a dictionary mapping BGC types to their counts.

3. ``map_bgc_to_mibig`` – maps a raw antiSMASH BGC type string to the
   corresponding MIBiG ontology class.  Unknown types are mapped to the
   literal ``'unknown'``.

The module also supports a **CI mode** (environment variable ``CI_MODE=1``)
where Docker is unavailable.  In that case a mock JSON file located at
``data/raw/mock_anti_smash.json`` is used instead of invoking Docker.  This
allows the test suite to run without requiring a Docker installation while
still exercising the full parsing and mapping logic on real‑style data.

When executed as a script, the module writes two CSV files under
``data/processed/``:
  * ``bgc_presence.csv`` – binary presence/absence matrix, aggregated by
    MIBiG metabolite class.
  * ``bgc_counts.csv``   – raw BGC count matrix, aggregated by MIBiG class.

Unmapped BGC types are labelled ``'unknown'``.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

import pandas as pd

from llmxive_toolkit import get_logger, paths

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Static mapping from antiSMASH BGC type strings to MIBiG ontology classes.
# This is a minimal, but representative, mapping covering the most common
# plant BGC types.  Types not listed are mapped to ``'unknown'``.
# ----------------------------------------------------------------------
_BGC_TYPE_TO_MIBIG: Mapping[str, str] = {
    "polyketide": "polyketide",
    "nonribosomal_peptide": "NRP",
    "terpene": "terpene",
    "alkaloid": "alkaloid",
    "saccharide": "saccharide",
    "ribosomally_synthesized_and_post-translationally_modified_peptide": "RiPP",
    "lanthipeptide": "lanthipeptide",
    "tRNA-dependent": "tRNA-dependent",
    # Add more mappings as needed.
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _run_docker_antismash(genome_path: Path, output_dir: Path) -> Path:
    """
    Execute antiSMASH 7.0 via Docker.

    Parameters
    ----------
    genome_path: Path
        Path to the input FASTA file.
    output_dir: Path
        Directory (inside the same host directory as ``genome_path``)
        where antiSMASH will write its output.  The function creates the
        directory if it does not exist.

    Returns
    -------
    Path
        Path to the generated JSON file (``<genome_stem>.json``).

    Raises
    ------
    RuntimeError
        If Docker is not available or the antiSMASH container exits
        with a non‑zero status.
    """
    # ------------------------------------------------------------------
    # CI mode – use a mock JSON file instead of Docker.
    # ------------------------------------------------------------------
    ci_mode = os.getenv("CI_MODE", "0").lower() in {"1", "true", "yes"}
    if ci_mode:
        mock_json = Path("data/raw/mock_anti_smash.json")
        if not mock_json.is_file():
            raise FileNotFoundError(
                "CI_MODE is enabled but mock antiSMASH JSON not found at "
                f"{mock_json}"
            )
        logger.info(
            f"CI_MODE detected – using mock antiSMASH output {mock_json}"
        )
        return mock_json

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Docker image that ships antiSMASH 7.0 (biocontainers)
    image = "quay.io/biocontainers/antismash:7.0.0--pyh7cba7a3_0"

    # Build the Docker command.
    # We mount the parent directory of the genome so that antiSMASH can
    # write its output inside the same host tree.
    host_dir = genome_path.parent.resolve()
    container_dir = Path("/data")
    genome_container_path = container_dir / genome_path.name
    output_container_path = container_dir / output_dir.name

    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{host_dir}:{container_dir}",
        "-w",
        str(container_dir),
        image,
        "antismash",
        "--output-dir",
        output_dir.name,
        "--genefinding-tool",
        "prodigal",
        "--full-hmmer",
        "--asf",
        "--cb-general",
        "--cb-subclusters",
        "--cb-knownclusters",
        "--cb-knownclusterblast",
        "--pfam2go",
        genome_path.name,
    ]

    logger.info(f"Running antiSMASH Docker: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(
            f"antiSMASH Docker failed for {genome_path}:\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
        raise RuntimeError(
            f"antiSMASH Docker execution failed (exit {result.returncode})"
        )

    json_path = output_dir / f"{genome_path.stem}.json"
    if not json_path.is_file():
        raise RuntimeError(f"Expected JSON output not found at {json_path}")

    logger.info(f"antiSMASH completed: JSON output at {json_path}")
    return json_path

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def run_antismash_wrapper(
    genome_paths: Iterable[Path],
    species_mapping: Mapping[Path, str],
    confidence: float = 0.5,
) -> pd.DataFrame:
    """
    Run antiSMASH on a collection of genome FASTA files and return a
    DataFrame with BGC count statistics per species.

    Parameters
    ----------
    genome_paths: Iterable[Path]
        Paths to genome FASTA files.
    species_mapping: Mapping[Path, str]
        Mapping from each genome path to the corresponding species name.
    confidence: float, optional
        Minimum confidence score for a BGC to be counted.  antiSMASH
        version 7 stores confidence per BGC in the ``confidence`` field
        (0‑1).  BGCs below this threshold are ignored.

    Returns
    -------
    pd.DataFrame
        Columns:
            - ``species`` (str)
            - ``total_bgc_count`` (int)
            - one column per observed BGC type (int count)
    """
    records: List[Dict] = []

    for genome_path in genome_paths:
        genome_path = Path(genome_path).resolve()
        if not genome_path.is_file():
            logger.warning(f"Genome file not found: {genome_path}")
            continue

        species_name = species_mapping.get(genome_path)
        if not species_name:
            logger.warning(
                f"No species name supplied for genome {genome_path}; skipping."
            )
            continue

        # antiSMASH output directory (sibling to the FASTA file)
        out_dir = genome_path.parent / f"{genome_path.stem}_antismash"

        try:
            json_file = _run_docker_antismash(genome_path, out_dir)
            bgc_counts = parse_antismash_json(json_file, confidence=confidence)
        except Exception as exc:
            logger.error(f"Failed to process {genome_path}: {exc}")
            continue

        # Build a flat record for this species
        record = {"species": species_name, "total_bgc_count": sum(bgc_counts.values())}
        record.update(bgc_counts)
        records.append(record)

    if not records:
        logger.warning("No antiSMASH results were successfully parsed.")
        return pd.DataFrame()

    df = pd.DataFrame(records).fillna(0).astype(
        {col: int for col in df.columns if col != "species"}
    )
    logger.info(f"antiSMASH wrapper produced DataFrame with shape {df.shape}")
    return df

def parse_antismash_json(json_path: Path, confidence: float = 0.5) -> Dict[str, int]:
    """
    Parse a single antiSMASH JSON output file and count BGC types that meet
    the confidence threshold.

    Parameters
    ----------
    json_path: Path
        Path to the antiSMASH JSON file.
    confidence: float, optional
        Minimum confidence score for a BGC to be counted.

    Returns
    -------
    dict
        Mapping from BGC type (as reported by antiSMASH) to integer count.
    """
    json_path = Path(json_path).resolve()
    if not json_path.is_file():
        raise FileNotFoundError(f"antiSMASH JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # antiSMASH JSON structure (v7) contains a top‑level ``records`` list.
    # Each record corresponds to a genome and holds a ``bgc`` list.
    bgc_counts: Dict[str, int] = {}

    for record in data.get("records", []):
        for bgc in record.get("bgc", []):
            # Confidence is stored under ``confidence`` (0‑1).  If missing,
            # we assume the BGC passes.
            bgc_conf = bgc.get("confidence", 1.0)
            if bgc_conf < confidence:
                continue

            # The BGC type can be found in ``product`` (a list of dicts)
            # or directly in ``type``.  We prefer ``product`` because it is
            # more granular.
            bgc_type = None
            products = bgc.get("product", [])
            if isinstance(products, list) and products:
                # Take the first product's ``type`` entry.
                bgc_type = products[0].get("type")
            if not bgc_type:
                bgc_type = bgc.get("type")

            if not bgc_type:
                continue  # skip malformed entries

            # Normalise the type string (antiSMASH uses lower‑case with
            # underscores in many cases).
            bgc_type_norm = str(bgc_type).strip().lower().replace(" ", "_")
            bgc_counts[bgc_type_norm] = bgc_counts.get(bgc_type_norm, 0) + 1

    logger.debug(f"Parsed BGC counts from {json_path}: {bgc_counts}")
    return bgc_counts

def map_bgc_to_mibig(bgc_type: str) -> str:
    """
    Map a raw antiSMASH BGC type string to the MIBiG ontology class.

    Parameters
    ----------
    bgc_type: str
        BGC type string as returned by antiSMASH (e.g. ``'polyketide'``).

    Returns
    -------
    str
        Corresponding MIBiG class name, or ``'unknown'`` if no mapping
        exists.
    """
    if not isinstance(bgc_type, str):
        return "unknown"
    key = bgc_type.strip().lower()
    return _BGC_TYPE_TO_MIBIG.get(key, "unknown")

# ----------------------------------------------------------------------
# CLI entry point – convenient for manual testing.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run antiSMASH on a genome and produce BGC count matrices."
    )
    parser.add_argument(
        "--genome",
        type=str,
        required=True,
        help="Path to the genome FASTA file.",
    )
    parser.add_argument(
        "--species",
        type=str,
        required=True,
        help="Species name associated with the genome.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(paths.data("processed")),
        help="Directory where CSV files will be written.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Minimum confidence score for BGC inclusion.",
    )
    args = parser.parse_args()

    genome_path = Path(args.genome)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Run antiSMASH for the single genome
    df = run_antismash_wrapper(
        [genome_path],
        species_mapping={genome_path: args.species},
        confidence=args.confidence,
    )
    if df.empty:
        logger.error("No BGC data produced; exiting.")
        exit(1)

    # ------------------------------------------------------------------
    # Aggregate by MIBiG class
    # ------------------------------------------------------------------
    # Determine mapping from raw BGC columns to MIBiG classes
    bgc_type_cols = [c for c in df.columns if c not in {"species", "total_bgc_count"}]

    # Build a mapping: raw column -> MIBiG class
    col_to_class = {col: map_bgc_to_mibig(col) for col in bgc_type_cols}

    # Aggregate counts per class
    class_counts = {}
    for col, mibig_class in col_to_class.items():
        class_counts.setdefault(mibig_class, 0)
        class_counts[mibig_class] += df[col].sum()

    # Create counts DataFrame (one row per species, aggregated)
    counts_agg = df[["species"]].copy()
    for mibig_class in set(col_to_class.values()):
        # Sum counts of all columns that map to this class
        cols = [col for col, cls in col_to_class.items() if cls == mibig_class]
        counts_agg[mibig_class] = df[cols].sum(axis=1)

    # Presence matrix: 1 if count > 0, else 0
    presence_agg = counts_agg.copy()
    for col in presence_agg.columns:
        if col != "species":
            presence_agg[col] = (presence_agg[col] > 0).astype(int)

    # Write CSVs
    presence_path = out_dir / "bgc_presence.csv"
    counts_path = out_dir / "bgc_counts.csv"

    presence_agg.to_csv(presence_path, index=False)
    counts_agg.to_csv(counts_path, index=False)

    logger.info(f"BGC presence matrix written to {presence_path}")
    logger.info(f"BGC counts matrix written to {counts_path}")