"""Download and sample raw code chunks from the CodeParrot GitHub dataset.

This script streams the ``codeparrot/github-code`` dataset, performs a
deterministic reservoir sample of ``N`` chunks per language (Python and
Java), and writes the sampled records to a Parquet file
``data/processed/raw_chunks.parquet``.  A SHA‑256 checksum of the Parquet
file is recorded in ``data/checksums.txt``.

The script is intended to be run as a module:

    python -m code.data.download

It is part of the T002 task and must produce non‑empty ``content`` fields
in the resulting Parquet file so that downstream tests (e.g. the
``test_raw_chunks_content`` unit test) succeed.
"""

import hashlib
import random
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger
from code.config import SEED

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Number of sampled chunks per language. The test suite expects exactly
# 1 000 rows for each of the two target languages.
SAMPLE_SIZE_PER_LANGUAGE = 1000

# Languages we care about – must match the dataset's language field.
TARGET_LANGUAGES = {"Python", "Java"}

LOG = get_logger(__name__)

def _reservoir_sample(stream, language_key="language"):
    """Yield a deterministic reservoir sample for each target language.

    Parameters
    ----------
    stream : iterable
        Streaming dataset records.
    language_key : str, optional
        Key in each record that holds the language name.

    Returns
    -------
    List[dict]
        List of sampled records, each containing at least the fields
        ``repo_name``, ``language`` and ``content``.
    """
    rng = random.Random(SEED)

    # Reservoirs per language
    reservoirs = {lang: [] for lang in TARGET_LANGUAGES}
    # Counters of how many records have been seen per language
    seen_counts = {lang: 0 for lang in TARGET_LANGUAGES}

    for record in stream:
        lang = record.get(language_key)
        if lang not in TARGET_LANGUAGES:
            continue

        seen_counts[lang] += 1
        i = seen_counts[lang]

        if len(reservoirs[lang]) < SAMPLE_SIZE_PER_LANGUAGE:
            reservoirs[lang].append(record)
        else:
            # Replace an existing element with probability N / i
            j = rng.randint(0, i - 1)
            if j < SAMPLE_SIZE_PER_LANGUAGE:
                reservoirs[lang][j] = record

    # Flatten the reservoirs while preserving language information
    sampled = []
    for lang, records in reservoirs.items():
        sampled.extend(records)
    return sampled

def _write_parquet(records, output_path: Path):
    """Write sampled records to a Parquet file with the required schema."""
    # Build rows with explicit columns; assign a stable integer id.
    rows = []
    for idx, rec in enumerate(records, start=1):
        rows.append(
            {
                "id": idx,
                "repo_name": rec.get("repo_name", ""),
                "language": rec.get("language", ""),
                "content": rec.get("content", ""),
                "status": "raw",
            }
        )
    df = pd.DataFrame(rows, columns=["id", "repo_name", "language", "content", "status"])
    df.to_parquet(output_path, index=False)
    LOG.info("Wrote %d rows to %s", len(df), output_path)

def _write_checksum(file_path: Path, checksum_path: Path):
    """Compute SHA‑256 of *file_path* and write it to *checksum_path*."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    LOG.info("Checksum written to %s", checksum_path)

def main():
    """Orchestrate the download, sampling, and storage steps."""
    LOG.info("Starting dataset download and reservoir sampling")
    # Stream the dataset; this will raise if the download fails.
    dataset_stream = load_dataset(
        "codeparrot/github-code", split="train", streaming=True
    )

    sampled_records = _reservoir_sample(dataset_stream)

    if not sampled_records:
        LOG.error("No records sampled – check language names and dataset availability")
        raise RuntimeError("Sampling produced no records")

    # Paths for the output artifacts
    parquet_path = paths.data("processed", "raw_chunks.parquet")
    checksum_path = paths.data("checksums.txt")

    _write_parquet(sampled_records, parquet_path)
    _write_checksum(parquet_path, checksum_path)

    LOG.info("Dataset download and sampling completed successfully")

if __name__ == "__main__":
    main()
