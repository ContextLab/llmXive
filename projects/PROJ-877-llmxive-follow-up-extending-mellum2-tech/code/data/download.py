"""
Dataset download module for llmXive pipeline.
Implements Task T002: stream `codeparrot/github-code`, perform a deterministic
reservoir sample per language, write raw records to Parquet, and record a SHA‑256
checksum.
"""
import json
import logging
import sys
import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List
import random

# Add project root to sys.path for sibling imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import get_project_root, get_config
from datasets import load_dataset
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def reservoir_sample_stream(
    iterator,
    sample_size: int,
    seed: int,
    key: str = "id"
) -> List[Dict[str, Any]]:
    """
    Perform a deterministic reservoir sample over a streaming iterator.

    Args:
        iterator: An iterator yielding dictionaries.
        sample_size: Desired number of samples.
        seed: Random seed for reproducibility.
        key: Optional unique identifier field (unused but kept for API compatibility).

    Returns:
        A list containing ``sample_size`` sampled items (or fewer if the iterator ends early).
    """
    random.seed(seed)
    reservoir: List[Dict[str, Any]] = []
    for i, item in enumerate(iterator, 1):
        if i <= sample_size:
            reservoir.append(item)
        else:
            # Replace with decreasing probability
            j = random.randint(1, i)
            if j <= sample_size:
                reservoir[j - 1] = item
    return reservoir


def fetch_and_sample(
    languages: List[str],
    total_sample_size: int,
    seed: int
) -> List[Dict[str, Any]]:
    """
    Stream the `codeparrot/github-code` dataset, filter by language,
    and obtain a deterministic reservoir sample of ``total_sample_size`` chunks
    (evenly split across the requested languages).

    Args:
        languages: List of language names (e.g., ['python', 'java']).
        total_sample_size: Total number of chunks to sample across all languages.
        seed: Random seed for reproducibility.

    Returns:
        List of sampled chunk dictionaries with keys:
        ``chunk_id``, ``repo_name``, ``language``, ``content``.
    """
    # Normalise languages to lower‑case for matching
    lang_set = {l.lower() for l in languages}
    per_lang = max(1, total_sample_size // len(lang_set))

    logger.info(
        f"Sampling {total_sample_size} chunks total "
        f"({per_lang} per language) for languages: {sorted(lang_set)}"
    )

    # Load the streaming dataset
    try:
        dataset = load_dataset(
            "codeparrot/github-code",
            streaming=True,
            split="train",
            trust_remote_code=True
        )
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # Prepare per‑language reservoirs
    reservoirs: Dict[str, List[Dict[str, Any]]] = {lang: [] for lang in lang_set}
    counts: Dict[str, int] = {lang: 0 for lang in lang_set}

    # Iterate through the streaming dataset
    for idx, example in enumerate(dataset):
        lang = example.get("language", "").lower()
        if lang not in lang_set:
            continue

        # Basic sanity checks
        content = example.get("content")
        if not content or len(content) < 20:
            continue

        # Build a minimal record
        record = {
            "id": f"chunk_{idx}_{lang}",
            "repo_name": example.get("repo", "unknown"),
            "language": lang,
            "content": content,
            "status": "raw"
        }

        # Reservoir sampling for this language
        counts[lang] += 1
        cur_res = reservoirs[lang]
        if len(cur_res) < per_lang:
            cur_res.append(record)
        else:
            # Deterministic replacement using the global seed + language offset
            random.seed(seed + idx + hash(lang))
            j = random.randint(0, counts[lang] - 1)
            if j < per_lang:
                cur_res[j] = record

        # Early exit if all reservoirs are full
        if all(len(r) >= per_lang for r in reservoirs.values()):
            # We have enough samples; break to avoid unnecessary streaming
            break

    # Flatten reservoirs while preserving language balance
    sampled: List[Dict[str, Any]] = []
    for lang in sorted(lang_set):
        sampled.extend(reservoirs[lang])

    logger.info(f"Collected {len(sampled)} sampled chunks "
                f"({sum(len(r) for r in reservoirs.values())} total).")
    return sampled


def write_parquet_and_checksum(
    records: List[Dict[str, Any]],
    output_parquet: Path,
    checksum_path: Path
) -> None:
    """
    Write the list of records to a Parquet file and record its SHA‑256 checksum.

    Args:
        records: List of dictionaries with the required columns.
        output_parquet: Destination Parquet file path.
        checksum_path: File where the checksum line will be written.
    """
    df = pd.DataFrame(records)
    # Ensure column ordering as required by the task
    df = df[["id", "repo_name", "language", "content", "status"]]

    # Write Parquet (using pyarrow engine)
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, engine="pyarrow", index=False)
    logger.info(f"Wrote Parquet file with {len(df)} rows to {output_parquet}")

    # Compute SHA‑256 checksum of the file bytes
    sha256 = hashlib.sha256()
    with open(output_parquet, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()

    # Write checksum file
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {output_parquet.name}\\n")
    logger.info(f"Wrote checksum to {checksum_path}")


def main():
    """
    CLI entry point for the download script.
    Mirrors the original ``code/data/download.py`` interface but implements
    the T002 specification.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Download and reservoir‑sample code chunks from the "
                    "`codeparrot/github-code` dataset."
    )
    parser.add_argument(
        "--lang",
        nargs="+",
        default=["python", "java"],
        help="Languages to download (e.g., --lang python java)."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500,
        help="Total number of chunks to sample across all languages."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic sampling. If omitted, the "
             "project configuration SEED is used."
    )

    args = parser.parse_args()

    # Resolve configuration
    config = get_config()
    seed = args.seed if args.seed is not None else config.get("SEED", 12345)

    # Fetch and sample
    sampled_records = fetch_and_sample(
        languages=args.lang,
        total_sample_size=args.sample_size,
        seed=seed
    )

    # Define output locations using llmxive_toolkit paths
    project_root = get_project_root()
    parquet_path = project_root / "data" / "processed" / "raw_chunks.parquet"
    checksum_path = project_root / "data" / "checksums.txt"

    # Write outputs
    write_parquet_and_checksum(
        records=sampled_records,
        output_parquet=parquet_path,
        checksum_path=checksum_path
    )

    logger.info("Dataset download & raw storage completed successfully.")


if __name__ == "__main__":
    main()
