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
import logging
import os
import requests
from pathlib import Path
from typing import Any, Optional, Union

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

class DataFetchError(RuntimeError):
    """Raised when a dataset cannot be fetched and synthetic fallback is not allowed."""
    pass


def calculate_checksum(filepath: Union[str, Path], algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file.

    Parameters
    ----------
    filepath: str or Path
        Path to the file whose checksum should be calculated.
    algorithm: str, optional
        Hash algorithm supported by ``hashlib`` (default ``sha256``).

    Returns
    -------
    str
        Hexadecimal digest of the file.
    """
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
    """Write a streamed HuggingFace dataset to a JSON‑Lines file.

    Only ``max_samples`` records are written (or fewer if the dataset
    ends earlier).  ``synthetic_flag`` is added when a synthetic fallback
    is used.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8") as out_f:
        iterator = ds
        for i, example in enumerate(iterator):
            if i >= max_samples:
                break
            if synthetic_flag:
                example = dict(example)
                example["synthetic_flag"] = synthetic_flag
            out_f.write(json.dumps(example, ensure_ascii=False) + "\n")


def _download_ttl(url: str, dest_path: Path, synthetic_flag: int = 0) -> None:
    """Download a Turtle file from ``url`` and write it as JSON‑Lines.

    Each line contains a JSON object with a single ``ttl`` key holding the
    raw Turtle line.  This keeps the output format consistent with the
    other datasets (JSON‑Lines) while preserving the raw graph data.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    with dest_path.open("w", encoding="utf-8") as out_f:
        for line in response.iter_lines(decode_unicode=True):
            if line:
                obj = {"ttl": line}
                if synthetic_flag:
                    obj["synthetic_flag"] = synthetic_flag
                out_f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    log.info(f"Turtle graph downloaded to {dest_path}")


def fetch_dataset(
    name: str,
    config_name: Optional[str] = None,
    split: str = "train",
    dest_path: Union[str, Path] = None,
    allow_synthetic: bool = False,
) -> Path:
    """Fetch a dataset from HuggingFace (or a raw URL for the graph) and persist it locally.

    Parameters
    ----------
    name: str
        Logical name of the dataset as used in ``config.DATASET_URLS``.
    config_name: str, optional
        Configuration name for HuggingFace datasets that expose multiple configs.
    split: str, optional
        Which split to download (default ``"train"``).
    dest_path: str or Path, optional
        Destination file path. If ``None``, a sensible path under
        ``paths.data("raw")`` is chosen based on the dataset name.
    allow_synthetic: bool, optional
        If ``True`` and the real fetch fails, a tiny synthetic graph is
        written instead with ``synthetic_flag=1``.

    Returns
    -------
    Path
        Path to the written JSON‑Lines file.

    Raises
    ------
    DataFetchError
        If the dataset cannot be fetched and ``allow_synthetic`` is ``False``.
    """
    # Resolve destination path early so we can use it for synthetic fallback.
    if dest_path is None:
        safe_name = name.replace("/", "_")
        dest_path = paths.data("raw", f"{safe_name}_{split}.jsonl")
    dest_path = Path(dest_path)

    # ------------------------------------------------------------------
    # Graph source – download a small TTL file directly.
    # ------------------------------------------------------------------
    if name == "dbpedia_sample":
        url = paths.config.get_dataset_path(name) if hasattr(paths, "config") else None
        # Fallback to the URL defined in config module.
        if url is None:
            url = DATASET_URLS.get(name)
        try:
            _download_ttl(url, dest_path, synthetic_flag=0)
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
        from datasets import load_dataset, DownloadMode  # type: ignore
    except Exception as exc:
        log.error(f"Failed to import datasets library: {exc}")
        if allow_synthetic:
            log.warning("Falling back to synthetic dataset generation.")
            _generate_synthetic_graph(dest_path)
            return dest_path
        raise DataFetchError(
            "Unable to import datasets library and synthetic fallback is disabled."
        ) from exc

    try:
        # Resolve configuration values from the central config module.
        from config import get_dataset_config  # Local import to avoid circularity.

        cfg = get_dataset_config(name)
        max_samples = cfg.get("max_samples", 1000)
        hf_name = cfg.get("url", cfg.get("dataset_name", name))
        # For MS MARCO we need the explicit config name (v1.1)
        hf_config = cfg.get("config_name")
        load_kwargs: dict = {
            "streaming": True,
            "download_mode": DownloadMode.FORCE_DOWNLOAD,
        }
        if hf_config:
            load_kwargs["name"] = hf_config

        log.info(
            f"Attempting to fetch dataset: {name} (config={hf_config}, split={split})"
        )
        ds = load_dataset(
            hf_name,
            split=split,
            **load_kwargs,
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
        raise DataFetchError(
            f"Unable to fetch dataset {name} and synthetic fallback is disabled."
        ) from exc


def _generate_synthetic_graph(dest_path: Path) -> None:
    """Generate a tiny synthetic graph and write it as JSON‑Lines."""
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
    """Ensure that all required datasets are present under ``data/raw``.

    The function attempts to fetch each dataset if it does not already exist.
    """
    required = [
        # (logical name, config_name, split)
        ("ms_marco", "v1.1", "train"),
        ("spider", None, "train"),
        ("dbpedia_sample", None, "train"),
    ]

    for logical_name, cfg, split in required:
        safe_name = logical_name.replace("/", "_")
        if cfg:
            safe_name += f"_{cfg}"
        expected_path = paths.data("raw", f"{safe_name}_{split}.jsonl")
        if not expected_path.is_file():
            log.info(f"Dataset file {expected_path} missing – fetching.")
            fetch_dataset(
                name=logical_name,
                config_name=cfg,
                split=split,
                dest_path=expected_path,
                allow_synthetic=allow_synthetic,
            )
        else:
            log.info(f"Dataset file {expected_path} already present.")


def main() -> None:
    """CLI entry point.

    Usage:
        python -m code.utils.data_fetcher [--allow-synthetic]

    The command fetches all required datasets into ``data/raw``.
    """
    parser = argparse.ArgumentParser(
        description="Fetch required benchmark datasets."
    )
    parser.add_argument(
        "--allow-synthetic",
        action="store_true",
        help="Generate a tiny synthetic graph if any real dataset cannot be fetched.",
    )
    args = parser.parse_args()
    verify_all_datasets(allow_synthetic=args.allow_synthetic)
