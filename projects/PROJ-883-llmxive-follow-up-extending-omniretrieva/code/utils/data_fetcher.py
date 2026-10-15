"""Data fetching utilities for real datasets.

This module provides:
- checksum calculation
- dataset fetching from HuggingFace `datasets` with streaming support
- verification of required datasets
- a CLI entry point for on‑demand fetching
"""

import argparse
import hashlib
import json
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
    synthetic_flag: int = 0,
) -> None:
    """Write a streamed HuggingFace dataset to a JSON‑Lines file.

    Each record is written as a single JSON object per line.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8") as out_f:
        # If a DatasetDict (multiple splits), concatenate them
        if hasattr(ds, "keys"):  # crude check for DatasetDict‑like object
            iterator = (example for split in ds.values() for example in split)
        else:
            iterator = ds

        for example in iterator:
            # Attach synthetic flag if needed
            if synthetic_flag:
                example = dict(example)
                example["synthetic_flag"] = synthetic_flag
            out_f.write(json.dumps(example, ensure_ascii=False) + "\n")


def fetch_dataset(
    name: str,
    config_name: Optional[str] = None,
    split: str = "train",
    dest_path: Union[str, Path] = None,
    allow_synthetic: bool = False,
) -> Path:
    """Fetch a dataset from HuggingFace and persist it locally.

    Parameters
    ----------
    name: str
        The HuggingFace dataset identifier (e.g., ``"microsoft/ms_marco"``).
    config_name: str, optional
        Configuration name for datasets that expose multiple configs.
    split: str, optional
        Which split to download (default ``"train"``).
    dest_path: str or Path, optional
        Destination file path. If ``None``, a sensible path under
        ``paths.data("raw")`` is chosen based on the dataset name.
    allow_synthetic: bool, optional
        If ``True`` and the real fetch fails, a tiny synthetic graph
        (a list of triples) is written instead with ``synthetic_flag=1``.

    Returns
    -------
    Path
        Path to the written JSON‑Lines file.

    Raises
    ------
    DataFetchError
        If the dataset cannot be fetched and ``allow_synthetic`` is ``False``.
    """
    try:
        # Import lazily to avoid importing heavy dependencies (e.g., pyarrow) unless needed.
        from datasets import load_dataset, DownloadConfig, DownloadMode  # type: ignore
    except Exception as exc:
        log.error(f"Failed to import datasets library: {exc}")
        if allow_synthetic:
            log.warning("Falling back to synthetic dataset generation (synthetic_flag=1).")
            synthetic_path = Path(dest_path) if dest_path else paths.data(
                "raw", f"synthetic_{name.replace('/', '_')}.jsonl"
            )
            _generate_synthetic_graph(synthetic_path)
            return synthetic_path
        else:
            raise DataFetchError(
                "Unable to import datasets library and synthetic fallback is disabled."
            ) from exc

    try:
        log.info(
            f"Attempting to fetch dataset: {name} (config={config_name}, split={split})"
        )
        # Build arguments correctly: ``name`` is the dataset identifier,
        # ``config_name`` (if provided) is passed via the ``name`` keyword
        # argument of ``load_dataset``.
        load_kwargs = {
            "streaming": True,
            "download_config": DownloadConfig(
                # Force download mode to raise on failure rather than using cache
                download_mode=DownloadMode.FORCE_DOWNLOAD
            ),
        }
        if config_name:
            load_kwargs["name"] = config_name

        ds = load_dataset(
            name,
            split=split,
            **load_kwargs,
        )

        # Resolve destination path
        if dest_path is None:
            safe_name = name.replace("/", "_")
            if config_name:
                safe_name += f"_{config_name}"
            dest_path = paths.data("raw", f"{safe_name}_{split}.jsonl")
        dest_path = Path(dest_path)

        _write_streamed_dataset(ds, dest_path)
        log.info(f"Dataset written to {dest_path}")
        return dest_path
    except Exception as exc:
        log.error(f"Failed to fetch dataset {name}: {exc}")
        if allow_synthetic:
            log.warning("Falling back to synthetic dataset generation (synthetic_flag=1).")
            synthetic_path = Path(dest_path) if dest_path else paths.data(
                "raw", f"synthetic_{name.replace('/', '_')}.jsonl"
            )
            _generate_synthetic_graph(synthetic_path)
            return synthetic_path
        else:
            raise DataFetchError(
                f"Unable to fetch dataset {name} and synthetic fallback is disabled."
            ) from exc


def _generate_synthetic_graph(dest_path: Path) -> None:
    """Generate a tiny synthetic graph and write it as JSON‑Lines.

    The synthetic graph consists of a few triples of the form
    ``{'head': 'nodeX', 'relation': 'relY', 'tail': 'nodeZ', 'synthetic_flag': 1}``.
    """
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
        # (dataset name, config, split)
        ("microsoft/ms_marco", "v1.1", "train"),
        ("xlangai/spider", None, "train"),
        ("wikidata5m/wikidata5m", None, "train"),
    ]

    for name, cfg, split in required:
        safe_name = name.replace("/", "_")
        if cfg:
            safe_name += f"_{cfg}"
        expected_path = paths.data("raw", f"{safe_name}_{split}.jsonl")
        if not expected_path.is_file():
            log.info(f"Dataset file {expected_path} missing – fetching.")
            fetch_dataset(
                name=name,
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