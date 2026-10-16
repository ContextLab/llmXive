"""Data fetching utilities for real datasets.

This module provides:
- checksum calculation
- dataset fetching from HuggingFace `datasets` (streaming) for the
  text and relational sources
- direct download of a small RDF/Turtle graph file for the graph source
- verification of required datasets
- a CLI entry point for on‑demand fetching
"""

import argparse
import hashlib
import json
import itertools
import requests
from pathlib import Path
from typing import Any, Optional, Union

from llmxive_toolkit import get_logger, paths
from config import get_dataset_config

log = get_logger(__name__)

class DataFetchError(RuntimeError):
    """Raised when a dataset cannot be fetched and synthetic fallback is not allowed."""
    pass

def calculate_checksum(filepath: Union[str, Path], algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file."""
    file_path = Path(filepath)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    h = hashlib.new(algorithm)
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_streamed_dataset(
    ds: Any,
    dest_path: Path,
    max_samples: int,
    synthetic_flag: int = 0,
) -> None:
    """Write a streamed HuggingFace dataset to a JSON‑Lines file."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8") as out_f:
        # Use islice to limit the streaming dataset
        for i, example in enumerate(itertools.islice(ds, max_samples)):
            if synthetic_flag:
                example = dict(example)
                example["synthetic_flag"] = synthetic_flag
            out_f.write(json.dumps(example, ensure_ascii=False) + "\n")

def _download_ttl(url: str, dest_path: Path) -> None:
    """Download a Turtle file from ``url`` and save as raw .ttl."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    with dest_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    log.info(f"Turtle graph downloaded to {dest_path}")

def fetch_dataset(
    name: str,
    split: str = "train",
    dest_path: Union[str, Path] = None,
    allow_synthetic: bool = False,
) -> Path:
    """Fetch a dataset from HuggingFace or a raw URL and persist it locally."""
    cfg = get_dataset_config(name)
    
    # Resolve destination path
    if dest_path is None:
        ext = "ttl" if name == "dbpedia_sample" else "jsonl"
        safe_name = name.replace("/", "_")
        dest_path = paths.data("raw", f"{safe_name}_{split}.{ext}")
    dest_path = Path(dest_path)

    # ------------------------------------------------------------------
    # Graph source – download a raw TTL file.
    # ------------------------------------------------------------------
    if name == "dbpedia_sample":
        try:
            _download_ttl(cfg["url"], dest_path)
            return dest_path
        except Exception as exc:
            log.error(f"Failed to download TTL for {name}: {exc}")
            if allow_synthetic:
                log.warning("Generating synthetic graph as fallback.")
                _generate_synthetic_graph(dest_path)
                return dest_path
            raise DataFetchError(f"Unable to fetch graph dataset {name}") from exc

    # ------------------------------------------------------------------
    # Text and relational sources – use HuggingFace ``datasets``.
    # ------------------------------------------------------------------
    try:
        from datasets import load_dataset # type: ignore
    except ImportError as exc:
        log.error(f"Failed to import datasets library: {exc}")
        if allow_synthetic:
            _generate_synthetic_graph(dest_path)
            return dest_path
        raise DataFetchError("datasets library not installed.") from exc

    try:
        hf_path = cfg["hf_path"]
        hf_config = cfg["config_name"]
        max_samples = cfg["max_samples"]

        log.info(f"Attempting to fetch dataset: {name} (config={hf_config}, split={split})")
        
        # Use download_mode as a direct argument to load_dataset as required.
        ds = load_dataset(
            hf_path,
            name=hf_config,
            split=split,
            streaming=True,
            download_mode="force_redownload" 
        )

        _write_streamed_dataset(ds, dest_path, max_samples, synthetic_flag=0)
        log.info(f"Dataset written to {dest_path}")
        return dest_path
    except Exception as exc:
        log.error(f"Failed to fetch dataset {name}: {exc}")
        if allow_synthetic:
            log.warning("Falling back to synthetic dataset generation.")
            _generate_synthetic_graph(dest_path)
            return dest_path
        raise DataFetchError(f"Unable to fetch dataset {name}") from exc

def _generate_synthetic_graph(dest_path: Path) -> None:
    """Generate a tiny synthetic graph and write it as JSON‑Lines (fallback)."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    synthetic_triples = [
        {"head": "Alice", "relation": "knows", "tail": "Bob", "synthetic_flag": 1},
        {"head": "Bob", "relation": "likes", "tail": "Charlie", "synthetic_flag": 1},
        {"head": "Charlie", "relation": "works_at", "tail": "AcmeCorp", "synthetic_flag": 1},
    ]
    with dest_path.open("w", encoding="utf-8") as f:
        for triple in synthetic_triples:
            f.write(json.dumps(triple, ensure_ascii=False) + "\n")
    log.info(f"Synthetic graph written to {dest_path}")

def verify_all_datasets(allow_synthetic: bool = False) -> None:
    """Ensure that all required datasets are present under ``data/raw``."""
    required = [
        ("ms_marco", "train"),
        ("spider", "train"),
        ("dbpedia_sample", "train"),
    ]

    for logical_name, split in required:
        cfg = get_dataset_config(logical_name)
        ext = "ttl" if logical_name == "dbpedia_sample" else "jsonl"
        safe_name = logical_name.replace("/", "_")
        expected_path = paths.data("raw", f"{safe_name}_{split}.{ext}")
        
        if not expected_path.is_file():
            log.info(f"Dataset file {expected_path} missing – fetching.")
            fetch_dataset(
                name=logical_name,
                split=split,
                dest_path=expected_path,
                allow_synthetic=allow_synthetic,
            )
        else:
            log.info(f"Dataset file {expected_path} already present.")

def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Fetch required benchmark datasets.")
    parser.add_argument(
        "--allow-synthetic",
        action="store_true",
        help="Generate a tiny synthetic graph if any real dataset cannot be fetched.",
    )
    args = parser.parse_args()
    verify_all_datasets(allow_synthetic=args.allow_synthetic)
