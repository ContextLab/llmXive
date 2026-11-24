"""Data loading and preprocessing utilities.

This module provides functions to download verified public tabular benchmarks,
compute checksums, monitor RAM usage, preprocess (impute, encode), split into
train/hold‑out, and write artefacts under ``data/raw`` and ``data/processed``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Tuple, List

import pandas as pd
import psutil
import yaml
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


# ----------------------------------------------------------------------
# Dataset specific loaders
# ----------------------------------------------------------------------
def load_adult() -> pd.DataFrame:
    """Load the UCI Adult dataset via a reliable source.

    The original ``datasets.load_dataset("openml", name="adult")`` is no longer
    available on the Hub. We first try the HuggingFace ``openml/Adult`` dataset;
    if that fails we fall back to the official ``openml`` Python package,
    which fetches the dataset directly from OpenML (ID 1590). Any failure
    propagates as an exception – no synthetic fallback is used.
    """
    log.info("Attempting to load UCI Adult dataset via HuggingFace hub.")
    try:
        # New hub identifier (as of datasets 2.x)
        ds = load_dataset("openml/Adult", split="train")
        df = pd.DataFrame(ds)
        log.info("Adult dataset loaded from HuggingFace hub: %d rows, %d columns", df.shape[0], df.shape[1])
        return df
    except Exception as hf_err:
        log.warning("HuggingFace load failed (%s); falling back to openml package.", hf_err)

    # Fallback: use the openml Python client
    try:
        import openml
    except ImportError as e:
        log.error("openml package not installed; cannot load Adult dataset.")
        raise e

    log.info("Fetching Adult dataset via openml package (ID 1590).")
    # Dataset ID 1590 corresponds to the classic UCI Adult dataset
    dataset = openml.datasets.get_dataset(1590)
    X, y, _, attribute_names = dataset.get_data(target=dataset.default_target_attribute)
    # Combine features and target into a single DataFrame
    df = pd.DataFrame(X, columns=attribute_names)
    df[dataset.default_target_attribute] = y
    log.info("Adult dataset fetched via openml: %d rows, %d columns", df.shape[0], df.shape[1])

    # Clean target column naming (standardize to 'income')
    target_col = "income" if "income" in df.columns else dataset.default_target_attribute
    if target_col in df.columns:
        df[target_col] = df[target_col].astype(str).str.strip().str.rstrip(".")
    return df


def load_har() -> pd.DataFrame:
    """Load the UCI HAR dataset via the datasets library."""
    log.info("Loading UCI HAR via datasets (udayl/UCI_HAR)")
    ds = load_dataset("udayl/UCI_HAR", split="test")
    df = pd.DataFrame(ds)
    log.info("HAR dataset loaded: %d rows, %d columns", df.shape[0], df.shape[1])
    return df


def load_shopper() -> pd.DataFrame:
    """Load the UCI Shopper dataset via the datasets library."""
    log.info("Loading UCI Shopper via datasets (jlh/uci-shopper)")
    ds = load_dataset("jlh/uci-shopper", split="train")
    df = pd.DataFrame(ds)
    log.info("Shopper dataset loaded: %d rows, %d columns", df.shape[0], df.shape[1])
    return df


# ----------------------------------------------------------------------
# Pre‑processing utilities
# ----------------------------------------------------------------------
def _is_categorical(series: pd.Series) -> bool:
    """Return True if *series* should be treated as categorical."""
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_bool_dtype(series):
        return True
    uniq = series.nunique(dropna=True)
    return uniq <= 10


def _impute(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Impute missing values (median for numerics, mode for categoricals)."""
    df = df.copy()
    log_dict: Dict = {"numeric": {}, "categorical": {}}
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                median = df[col].median()
                df[col] = df[col].fillna(median)
                log_dict["numeric"][col] = "median"
            else:
                mode_res = df[col].mode()
                if not mode_res.empty:
                    mode = mode_res.iloc[0]
                    df[col] = df[col].fillna(mode)
                    log_dict["categorical"][col] = "mode"
    return df, log_dict


def _encode(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Encode categoricals.
    - <= 20 categories -> one-hot
    - > 20 categories -> frequency encoding
    """
    encoding_log: Dict = {"strategy": "hybrid", "details": {}}
    result = df.copy()
    for col in df.columns:
        if _is_categorical(df[col]):
            n_unique = df[col].nunique()
            if n_unique <= 20:
                dummies = pd.get_dummies(result[col], prefix=col)
                result = pd.concat([result.drop(columns=col), dummies], axis=1)
                encoding_log["details"][col] = {
                    "type": "one_hot",
                    "categories": list(dummies.columns),
                }
            else:
                freq = df[col].value_counts(normalize=True)
                result[col] = result[col].map(freq)
                encoding_log["details"][col] = {
                    "type": "frequency",
                    "mapping": freq.to_dict(),
                }
    return result, encoding_log


# ----------------------------------------------------------------------
# Main processing pipeline
# ----------------------------------------------------------------------
def process_dataset(name: str, df: pd.DataFrame, source: str) -> Dict:
    """Preprocess *df* and write artefacts."""
    # 1. Raw Storage
    raw_dir = paths.data("raw", name)
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "raw.parquet"
    df.to_parquet(raw_path, index=False)

    checksum = sha256_file(raw_path)
    checksums_path = raw_dir / "checksums.sha256"
    checksums_path.write_text(f"{checksum}  {raw_path.name}\n")

    # 2. Preprocessing
    df, impute_log = _impute(df)
    df, encode_log = _encode(df)

    # 3. Split
    train_df = df.sample(frac=0.8, random_state=123)
    holdout_df = df.drop(train_df.index)

    # 4. RAM monitoring & mitigation
    peak_rss = current_rss_bytes()
    mitigation: Dict = {}
    limit_bytes = 6.5 * (1024 ** 3)
    if peak_rss > limit_bytes:
        max_rows = 10_000
        if len(train_df) > max_rows:
            train_df = train_df.sample(n=max_rows, random_state=42)
            mitigation["downsampled_to"] = max_rows
        else:
            cardinalities = {
                col: df[col].nunique()
                for col in df.columns if _is_categorical(df[col])
            }
            if cardinalities:
                drop_col = max(cardinalities, key=cardinalities.get)
                train_df = train_df.drop(columns=drop_col)
                holdout_df = holdout_df.drop(columns=drop_col)
                mitigation["dropped_column"] = drop_col

    # 5. Processed Storage
    proc_dir = paths.data("processed", name)
    proc_dir.mkdir(parents=True, exist_ok=True)

    train_path = proc_dir / "train.parquet"
    holdout_path = proc_dir / "holdout.parquet"
    train_df.to_parquet(train_path, index=False)
    holdout_df.to_parquet(holdout_path, index=False)

    (proc_dir / "preprocess_log.txt").write_text(json.dumps(mitigation, indent=2))

    metadata = {
        "dataset": name,
        "source": source,
        "raw_snapshot": str(raw_path),
        "checksums_file": str(checksums_path),
        "checksums": {raw_path.name: checksum},
        "imputation": {
            "numeric": "median",
            "categorical": "mode",
        },
        "encoding": {
            "strategy": "hybrid",
            "details": encode_log.get("details", {}),
        },
        "split": {"fraction": 0.8, "seed": 123},
        "ram_limit_bytes": int(limit_bytes),
        "ram_mitigations": mitigation,
        "columns": list(df.columns),
        "row_counts": {
            "original": len(df),
            "train": len(train_df),
            "holdout": len(holdout_df)
        }
    }
    with open(proc_dir / "metadata.yaml", "w") as f:
        yaml.dump(metadata, f)

    return {
        "name": name,
        "peak_ram_gb": peak_rss / (1024 ** 3),
        "mitigation_applied": bool(mitigation),
        "completed_within_limit": peak_rss <= limit_bytes,
    }


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
    dataset_map = {
        "adult": (load_adult, "OpenML adult"),
        "har": (load_har, "UCI HAR"),
        "shopper": (load_shopper, "UCI Shopper"),
    }

    for ds_name in args.datasets:
        loader_fn, src_name = dataset_map[ds_name]
        df = loader_fn()
        sum_dict = process_dataset(ds_name, df, src_name)
        summary.append(sum_dict)

    # Global resource summary
    fraction_ok = (
        sum(1 for s in summary if s["completed_within_limit"]) / len(summary)
        if summary else 0
    )

    final_summary = {
        "per_dataset": summary,
        "fraction_completed_within_ram": fraction_ok
    }

    out_path = paths.outputs("metrics", "resource_summary.json")
    out_path.write_text(json.dumps(final_summary, indent=2))
    log.info("Resource summary written to %s", out_path)


if __name__ == "__main__":
    main()