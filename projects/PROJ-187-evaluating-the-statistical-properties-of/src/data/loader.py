"""Data loading and preprocessing utilities.

This module provides functions to download verified public tabular benchmarks,
compute checksums, monitor RAM usage, preprocess (impute, encode), split into
train/hold‑out, and write artefacts under ``data/raw`` and ``data/processed``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import psutil
import requests
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    """Return the SHA‑256 checksum of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def current_rss_bytes() -> int:
    """Current Resident Set Size (RAM) usage in bytes."""
    return psutil.Process(os.getpid()).memory_info().rss


def _fetch_bytes(url: str) -> bytes:
    """Fetch *url* and return its raw bytes.

    Raises
    ------
    requests.HTTPError
        If the HTTP request fails (status != 200).
    """
    log.info("Fetching %s", url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content


# ----------------------------------------------------------------------
# Dataset specific loaders
# ----------------------------------------------------------------------
def load_adult() -> pd.DataFrame:
    """Load the UCI Adult dataset from the verified OpenML URL.

    The OpenML ``datasets.load_dataset`` endpoint requires authentication
    and currently returns 401 on the CI runner, therefore we download the
    CSV directly.

    Returns
    -------
    pd.DataFrame
        The raw Adult dataframe (no preprocessing applied).
    """
    url = "https://openml.org/data/get_csv/1590/adult.csv"
    raw_bytes = _fetch_bytes(url)
    df = pd.read_csv(io.BytesIO(raw_bytes), na_values="?", skipinitialspace=True)
    log.info("Adult dataset loaded: %d rows, %d columns", df.shape[0], df.shape[1])
    return df


def load_har() -> pd.DataFrame:
    """Load the UCI HAR dataset via the HuggingFace hub, falling back to a
    direct URL if the hub is unavailable."""
    try:
        ds = load_dataset("udayl/UCI_HAR", split="train")
        df = pd.DataFrame(ds)
        log.info("HAR loaded via datasets library")
    except Exception as exc:
        log.warning("datasets load failed for HAR (%s); falling back to direct URL", exc)
        # Verified raw CSV URL from the HF repo
        url = "https://raw.githubusercontent.com/udayl/UCI_HAR/master/train.csv"
        raw_bytes = _fetch_bytes(url)
        df = pd.read_csv(io.BytesIO(raw_bytes))
    return df


def load_shopper() -> pd.DataFrame:
    """Load the UCI Shopper dataset via the HuggingFace hub, with a direct
    fallback."""
    try:
        ds = load_dataset("jlh/uci-shopper", split="train")
        df = pd.DataFrame(ds)
        log.info("Shopper loaded via datasets library")
    except Exception as exc:
        log.warning("datasets load failed for Shopper (%s); falling back to direct URL", exc)
        url = "https://raw.githubusercontent.com/jlh/uci-shopper/main/data/train.parquet"
        raw_bytes = _fetch_bytes(url)
        # Parquet bytes -> pandas
        df = pd.read_parquet(io.BytesIO(raw_bytes))
    return df


# ----------------------------------------------------------------------
# Pre‑processing utilities
# ----------------------------------------------------------------------
def _is_categorical(series: pd.Series) -> bool:
    """Return True if *series* should be treated as categorical."""
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_bool_dtype(series):
        return True
    # Few unique values relative to size => categorical
    uniq = series.nunique(dropna=True)
    return uniq <= 10


def _sanitize_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """Convert mixed‑type columns to a parquet‑friendly dtype."""
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype("string")
    return df


def _impute(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Impute missing values (median for numerics, mode for categoricals).

    Returns the imputed dataframe and a log dict describing the strategy.
    """
    log_dict: Dict = {}
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                median = df[col].median()
                df[col].fillna(median, inplace=True)
                log_dict[col] = {"impute": "median", "value": median}
            else:
                mode = df[col].mode().iloc[0]
                df[col].fillna(mode, inplace=True)
                log_dict[col] = {"impute": "mode", "value": mode}
    return df, log_dict


def _encode(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Encode categoricals.

    - ≤20 distinct categories → one‑hot
    - >20 categories → frequency encoding

    Returns the encoded dataframe and an encoding‑log dict.
    """
    encoding_log: Dict = {}
    result = df.copy()
    for col in df.columns:
        if _is_categorical(df[col]):
            n_unique = df[col].nunique()
            if n_unique <= 20:
                dummies = pd.get_dummies(result[col], prefix=col)
                result.drop(columns=col, inplace=True)
                result = pd.concat([result, dummies], axis=1)
                encoding_log[col] = {"type": "one_hot", "categories": list(dummies.columns)}
            else:
                freq = df[col].value_counts(normalize=True)
                result[col] = result[col].map(freq)
                encoding_log[col] = {"type": "frequency", "mapping": freq.to_dict()}
    return result, encoding_log


# ----------------------------------------------------------------------
# Main processing pipeline
# ----------------------------------------------------------------------
def process_dataset(name: str, df: pd.DataFrame, source: str) -> Dict:
    """Preprocess *df* and write artefacts.

    Parameters
    ----------
    name:
        Canonical dataset identifier (e.g. ``\"adult\"``).
    df:
        Raw dataframe as returned by the loader.
    source:
        Human‑readable source description for metadata.

    Returns
    -------
    dict
        Summary information (checksums, RAM usage, mitigation actions,
        row counts, etc.) suitable for aggregation into the global
        ``resource_summary.json``.
    """
    raw_dir = paths.data("raw", name)
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / f"{name}_raw.parquet"
    df.to_parquet(raw_path, index=False)
    checksum = sha256_file(raw_path)
    (raw_dir / "checksums.sha256").write_text(f"{checksum}  {raw_path.name}\n")

    # -------------------- Imputation & Encoding --------------------
    df, impute_log = _impute(df)
    df, encode_log = _encode(df)

    # -------------------- Train / Hold‑out split --------------------
    train_df = df.sample(frac=0.8, random_state=123)
    holdout_df = df.drop(train_df.index)

    # -------------------- RAM monitoring & mitigation --------------------
    peak_rss = current_rss_bytes()
    mitigation = {}
    if peak_rss > 6.5 * (1024 ** 3):  # >6.5 GB
        # Simple mitigation: uniform down‑sample to ≤10 k rows
        max_rows = 10_000
        if len(train_df) > max_rows:
            train_df = train_df.sample(n=max_rows, random_state=42)
            mitigation["downsampled_to"] = max_rows
        else:
            # If already small, drop highest‑cardinality columns
            cardinalities = {
                col: df[col].nunique() for col in df.columns if _is_categorical(df[col])
            }
            if cardinalities:
                drop_col = max(cardinalities, key=cardinalities.get)
                train_df = train_df.drop(columns=drop_col)
                holdout_df = holdout_df.drop(columns=drop_col)
                mitigation["dropped_column"] = drop_col

    # -------------------- Write processed artefacts --------------------
    proc_dir = paths.data("processed", name)
    proc_dir.mkdir(parents=True, exist_ok=True)

    train_path = proc_dir / "train.parquet"
    holdout_path = proc_dir / "holdout.parquet"
    train_df.to_parquet(train_path, index=False)
    holdout_df.to_parquet(holdout_path, index=False)

    metadata = {
        "dataset": name,
        "source": source,
        "checksum": checksum,
        "impute_log": impute_log,
        "encode_log": encode_log,
        "split": {"train_frac": 0.8, "seed": 123},
        "row_counts": {
            "raw": len(df),
            "train": len(train_df),
            "holdout": len(holdout_df),
        },
        "ram": {
            "peak_gb": peak_rss / (1024 ** 3),
            "mitigation": mitigation,
        },
        "processed_timestamp": pd.Timestamp.now().isoformat(),
    }

    (proc_dir / "metadata.yaml").write_text(json.dumps(metadata, indent=2))

    # -------------------- Return summary for resource aggregation --------------------
    return {
        "name": name,
        "peak_ram_gb": peak_rss / (1024 ** 3),
        "mitigation_applied": bool(mitigation),
        "completed_within_limit": peak_rss <= 6.5 * (1024 ** 3),
    }


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Download and preprocess verified datasets.")
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=["adult", "har", "shopper"],
        default=["adult", "har", "shopper"],
        help="Which datasets to process.",
    )
    args = parser.parse_args(argv)

    summary = []
    for ds in args.datasets:
        if ds == "adult":
            df = load_adult()
            src = "OpenML adult (CSV download)"
        elif ds == "har":
            df = load_har()
            src = "UCI_HAR HF repository"
        elif ds == "shopper":
            df = load_shopper()
            src = "UCI shopper HF repository"
        else:
            continue

        sum_dict = process_dataset(ds, df, src)
        summary.append(sum_dict)

    # Write global resource summary
    out_path = paths.outputs("metrics", "resource_summary.json")
    out_path.write_text(json.dumps(summary, indent=2))
    log.info("Resource summary written to %s", out_path)

if __name__ == "__main__":
    main()
