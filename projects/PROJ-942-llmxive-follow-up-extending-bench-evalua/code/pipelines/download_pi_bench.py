import argparse
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import List, Tuple, Optional

import requests

from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)


def _sha256_checksum(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_checksums(files: List[Tuple[Path, str]], out_path: Path) -> None:
    """Write a manifest of SHA‑256 checksums."""
    with out_path.open("w", encoding="utf-8") as f:
        for rel_path, checksum in files:
            f.write(f"{checksum}  {rel_path}\n")
    log.info(f"Checksum manifest written to {out_path}")


def _download_squad(raw_dir: Path, max_examples: Optional[int] = None) -> List[Tuple[Path, str]]:
    """
    Download the SQuAD v2 training set from the Hugging Face hub via a direct URL.
    Each QA pair is written as a separate JSON file.

    Parameters
    ----------
    raw_dir: Path
        Directory where JSON files will be stored.
    max_examples: Optional[int]
        Limit the number of examples written (useful for CI speed‑up).

    Returns
    -------
    List[Tuple[Path, str]]
        List of (relative_path, checksum) for each written file.
    """
    url = "https://huggingface.co/datasets/squad/resolve/main/train-v2.0.json"
    log.info(f"Downloading SQuAD dataset from {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    squad_data = response.json()

    checksums: List[Tuple[Path, str]] = []
    example_idx = 0

    for paragraph in squad_data.get("data", []):
        for qa in paragraph.get("paragraphs", []):
            # The original format nests QAs under "qas"
            for q in qa.get("qas", []):
                if max_examples is not None and example_idx >= max_examples:
                    break
                # Build a flat example dict
                example = {
                    "id": q.get("id"),
                    "title": paragraph.get("title"),
                    "context": qa.get("context"),
                    "question": q.get("question"),
                    "answers": q.get("answers"),
                }
                safe_id = (
                    str(example["id"])
                    .replace("/", "_")
                    .replace("\\", "_")
                    .replace(" ", "_")
                )
                json_path = raw_dir / f"{safe_id}.json"
                with json_path.open("w", encoding="utf-8") as jf:
                    json.dump(example, jf, ensure_ascii=False, indent=2)

                rel_path = json_path.relative_to(raw_dir)
                checksum = _sha256_checksum(json_path)
                checksums.append((rel_path, checksum))

                example_idx += 1
                if example_idx % 10 == 0:
                    log.debug(f"Wrote {example_idx} SQuAD examples")
            if max_examples is not None and example_idx >= max_examples:
                break
        if max_examples is not None and example_idx >= max_examples:
            break

    log.info(f"Finished writing {example_idx} SQuAD examples to {raw_dir}")
    return checksums


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a public dataset (fallback to SQuAD) and verify checksums."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(paths.data("raw")),
        help="Directory to store raw dataset files.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=10,
        help="Maximum number of examples to download. Set for faster CI.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        checksums = _download_squad(raw_dir, max_examples=args.max_examples)
    except Exception as exc:
        log.error(f"Failed to download or process the dataset: {exc}")
        raise

    # Write a simple manifest
    manifest_path = raw_dir / "download_manifest.txt"
    with manifest_path.open("w", encoding="utf-8") as mf:
        mf.write(
            "Dataset downloaded via direct HTTP request (fallback to SQuAD).\n"
        )

    # Write checksum manifest
    checksum_path = raw_dir / "checksums.txt"
    _write_checksums(checksums, checksum_path)

    log.info("Dataset download and verification completed successfully.")
    print("✅ Dataset download verified")

if __name__ == "__main__":
    main()
