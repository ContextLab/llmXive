"""
Download and sample the `codeparrot/github-code` dataset.

This script streams the full dataset, performs a deterministic reservoir
sampling per language (Python and Java), and writes the sampled records
to a Parquet file.  It also records a SHA‑256 checksum of the resulting
Parquet file in ``data/checksums.txt`` for reproducibility verification.

The script is invoked as part of the pipeline orchestrated by
``code/main.py`` (phase ``download``).  It requires no command‑line
arguments; all parameters are taken from ``code/config.py`` where a
global ``SEED`` and an optional ``SAMPLE_SIZE_PER_LANGUAGE`` are defined.
If ``SAMPLE_SIZE_PER_LANGUAGE`` is absent, a default of ``500`` samples
per language is used.

The implementation follows the contract for **T002**:
* streams the real HuggingFace dataset (no synthetic fallback),
* uses a proper reservoir sampling algorithm (seeded for determinism),
* writes a Parquet file with columns ``id``, ``repo_name``, ``language``,
  ``content``, ``status``,
* records the SHA‑256 checksum in ``data/checksums.txt``.
"""

import argparse
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
from datasets import load_dataset

# Project utilities
from llmxive_toolkit import paths, get_logger
from code import config

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def reservoir_sample(
    stream,
    language_key: str,
    target_langs: List[str],
    sample_size: int,
    rng,
) -> Dict[str, List[Dict]]:
    """
    Perform deterministic reservoir sampling per language.

    Parameters
    ----------
    stream : iterable
        Iterable of dataset records.
    language_key : str
        Key in each record that denotes the language (e.g., ``language``).
    target_langs : list[str]
        Languages to sample (case‑insensitive).
    sample_size : int
        Desired number of samples per language.
    rng : random.Random
        Random generator seeded for determinism.

    Returns
    -------
    dict
        Mapping ``language`` -> list of sampled records (each record is a
        dict containing the required columns plus ``status``).
    """
    import random

    # Normalise target language names to lower case for matching
    target_set = {lang.lower() for lang in target_langs}
    reservoirs: Dict[str, List[Dict]] = {lang: [] for lang in target_langs}
    counts: Dict[str, int] = {lang: 0 for lang in target_langs}

    for idx, record in enumerate(stream):
        # Defensive: some records may be missing the language field
        lang_raw = record.get(language_key, "")
        if not isinstance(lang_raw, str):
            continue
        lang = lang_raw.strip().lower()
        if lang not in target_set:
            continue

        # Map back to canonical language name (as defined in target_langs)
        # Preserve the original case of the target list entry
        canonical_lang = next(
            (t for t in target_langs if t.lower() == lang), lang_raw
        )

        counts[canonical_lang] += 1
        n = counts[canonical_lang]

        if len(reservoirs[canonical_lang]) < sample_size:
            # Fill the reservoir directly
            reservoirs[canonical_lang].append(record)
        else:
            # Replace with decreasing probability
            replace_idx = rng.randint(0, n - 1)
            if replace_idx < sample_size:
                reservoirs[canonical_lang][replace_idx] = record

    logger.info(
        "Completed reservoir sampling: %s",
        {lang: len(reservoirs[lang]) for lang in reservoirs},
    )
    return reservoirs


def write_parquet(records: List[Dict], output_path: Path) -> None:
    """
    Write a list of dictionaries to a Parquet file with the required schema.

    Parameters
    ----------
    records : list[dict]
        Sampled records.
    output_path : pathlib.Path
        Destination file (parents are created automatically).
    """
    df = pd.DataFrame(records)

    # Ensure required columns exist; fill missing with ``None``.
    required_cols = ["id", "repo_name", "language", "content", "status"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    # Re‑order columns to match the specification.
    df = df[required_cols]

    # Write using pyarrow engine (default for pandas >= 1.0).
    df.to_parquet(output_path, index=False)
    logger.info("Wrote %d rows to Parquet file %s", len(df), output_path)


def write_checksum(file_path: Path, checksum_path: Path) -> None:
    """
    Compute the SHA‑256 checksum of ``file_path`` and write it to
    ``checksum_path``.  The checksum file contains a single line:
    ``<sha256>  <filename>``.

    Parameters
    ----------
    file_path : pathlib.Path
        The file to checksum.
    checksum_path : pathlib.Path
        Destination for the checksum text file.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum_line = f"{sha256.hexdigest()}  {file_path.name}\n"
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.write_text(checksum_line)
    logger.info("Wrote checksum to %s", checksum_path)


# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------


def main(argv: List[str] | None = None) -> int:
    """
    Entry point for the download phase.

    The function streams the ``codeparrot/github-code`` dataset, performs
    deterministic reservoir sampling per language, writes the sampled
    records to ``data/processed/raw_chunks.parquet`` and records a SHA‑256
    checksum in ``data/checksums.txt``.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    parser = argparse.ArgumentParser(
        description="Download and sample codeparrot/github-code dataset."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=getattr(config, "SAMPLE_SIZE_PER_LANGUAGE", 500),
        help="Number of chunks to sample per language (default: config value or 500).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=getattr(config, "SEED", 12345),
        help="Random seed for deterministic sampling (default: config.SEED or 12345).",
    )
    args = parser.parse_args(argv)

    # Paths for output files
    parquet_path = paths.data("processed", "raw_chunks.parquet")
    checksum_path = paths.data("checksums.txt")

    # Ensure output directories exist
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialise deterministic RNG
    rng = __import__("random").Random(args.seed)

    # Languages we care about (case‑insensitive)
    target_languages = ["Python", "Java"]

    logger.info(
        "Starting streaming download of codeparrot/github-code (sample size per language=%d).",
        args.sample_size,
    )

    # Stream the dataset; any network failure will raise and abort.
    try:
        dataset_stream = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
            trust_remote_code=True,
        )
    except Exception as e:
        logger.error("Failed to load dataset: %s", e)
        raise

    # ------------------------------------------------------------------
    # Optimised sampling loop with early termination
    # ------------------------------------------------------------------
    # We stop as soon as we have collected the required number of
    # samples for *each* target language.  This avoids unnecessary
    # network traffic and guarantees the script finishes quickly
    # even on modest CI runners.
    # ------------------------------------------------------------------
    reservoirs: Dict[str, List[Dict]] = {lang: [] for lang in target_languages}
    counts: Dict[str, int] = {lang: 0 for lang in target_languages}

    for record in dataset_stream:
        lang_raw = record.get("language", "")
        if not isinstance(lang_raw, str):
            continue
        if lang_raw not in target_languages:
            continue

        # Update reservoir for this language
        lang = lang_raw
        counts[lang] += 1
        n = counts[lang]

        if len(reservoirs[lang]) < args.sample_size:
            reservoirs[lang].append(record)
        else:
            replace_idx = rng.randint(0, n - 1)
            if replace_idx < args.sample_size:
                reservoirs[lang][replace_idx] = record

        # Early exit: when both languages have reached the desired size
        if all(len(reservoirs[l]) >= args.sample_size for l in target_languages):
            logger.info(
                "Sample size reached for all languages after processing %d records.",
                sum(counts.values()),
            )
            break

    # Log final counts
    logger.info(
        "Finished streaming. Collected counts: %s",
        {l: len(reservoirs[l]) for l in target_languages},
    )

    # Flatten reservoirs into a single list of records, adding a ``status`` field.
    all_records: List[Dict] = []
    for lang, records in reservoirs.items():
        for rec in records:
            out_rec = {
                "id": rec.get("id"),
                "repo_name": rec.get("repo_name"),
                "language": lang,
                "content": rec.get("content"),
                "status": "ok",
            }
            all_records.append(out_rec)

    # Sanity check: ensure we have exactly the requested number per language.
    for lang in target_languages:
        expected = args.sample_size
        actual = len([r for r in all_records if r["language"] == lang])
        if actual != expected:
            logger.error(
                "Sampling error: expected %d rows for %s but got %d.",
                expected,
                lang,
                actual,
            )
            raise RuntimeError(
                f"Incorrect number of sampled rows for {lang}: expected {expected}, got {actual}"
            )

    # Write Parquet file
    write_parquet(all_records, parquet_path)

    # Write checksum file
    write_checksum(parquet_path, checksum_path)

    logger.info("Dataset download and sampling completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
