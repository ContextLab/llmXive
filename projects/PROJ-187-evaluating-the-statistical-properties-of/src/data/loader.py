"""Real-data loading and preprocessing for the statistical fidelity study.

Loads three verified real tabular benchmarks (Adult via OpenML, UCI-HAR and
UCI-Shopper via HuggingFace ``datasets``, with direct fetch of the plan's
verified HTTPS URLs as a secondary real-source path), snapshots the raw
data under ``data/raw/<name>/`` with SHA-256 checksums, imputes missing
values, encodes categorical columns as integer codes, applies the FR-009
RAM mitigation if peak RSS exceeds 6.5 GB, and writes an 80/20
train/hold-out split (seed 123) to
``data/processed/<name>/{train,holdout}.parquet`` plus a provenance
``metadata.yaml`` and ``preprocess_log.txt``.

The loader fails loudly on any fetch failure: no synthetic or mock
fallback exists anywhere in this module. Every fallback path between
loaders below is a REAL source (the plan's verified dataset URLs).
In addition, per‑dataset RAM usage and mitigation status are aggregated
into ``outputs/metrics/resource_summary.json`` as required by the task
specification.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import pandas as pd
import psutil
import requests
import yaml
from sklearn.model_selection import train_test_split

from llmxive_toolkit import paths

log = logging.getLogger(__name__)

SEED = 123
SPLIT_FRACTION = 0.8
RAM_LIMIT_BYTES = int(6.5 * 1024 ** 3)  # strict headroom below the 7 GB hard limit
MAX_ROWS_AFTER_MITIGATION = 10_000
HIGH_CARDINALITY_THRESHOLD = 50

HAR_VERIFIED_URL = (
    "https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/train.csv"
)
SHOPPER_VERIFIED_URL = (
    "https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/"
    "data/train-00000-of-00001-3316810f8df41d3a.parquet"
)

# ---------------------------------------------------------------------------
# Global collection for the resource‑summary JSON
# ---------------------------------------------------------------------------
_resource_summary: List[Dict] = []


# ---------------------------------------------------------------------------
# Raw loaders (real sources only; failures propagate loudly)
# ---------------------------------------------------------------------------

def _fetch_bytes(url: str) -> bytes:
    """Fetch a verified URL, raising loudly on any HTTP failure."""
    resp = requests.get(url, timeout=180)
    resp.raise_for_status()
    if not resp.content:
        raise RuntimeError(f"empty response body from {url}")
    return resp.content


def load_adult() -> pd.DataFrame:
    """UCI Adult via OpenML dataset id 1590 (verified source)."""
    import openml

    dataset = openml.datasets.get_dataset(1590, download_data=True)
    df, _, _, _ = dataset.get_data(
        dataset_format="dataframe", target=dataset.default_target_attribute
    )
    if df is None or len(df) == 0:
        raise RuntimeError("OpenML dataset 1590 (Adult) returned no data")
    return df


def load_har() -> pd.DataFrame:
    """UCI Human Activity Recognition via HuggingFace udayl/UCI_HAR.

    Primary path is ``datasets.load_dataset("udayl/UCI_HAR",
    split="train")`` exactly as specified in tasks.md; if the Hub library
    cannot serve the repository (e.g. script‑based dataset incompatibil-
    ity), the plan's verified HTTPS URL for the same real data is fetched
    directly. Both paths are real data; if both fail the error propagates.
    """
    errors: List[str] = []
    for kwargs in (
        {"split": "train"},
        {"name": "csv_files", "split": "train"},
    ):
        try:
            from datasets import load_dataset

            ds = load_dataset("udayl/UCI_HAR", **kwargs)
            df = ds.to_pandas()
            if df is None or len(df) == 0:
                raise RuntimeError("empty dataframe from udayl/UCI_HAR")
            return df
        except Exception as exc:  # real‑source fallback below, never synthetic
            errors.append(f"load_dataset({kwargs!r}) failed: {exc}")
    try:
        content = _fetch_bytes(HAR_VERIFIED_URL)
        df = pd.read_csv(io.BytesIO(content))
        if df is None or len(df) == 0:
            raise RuntimeError("empty dataframe from verified HAR URL")
        return df
    except Exception as exc:
        errors.append(f"direct fetch of {HAR_VERIFIED_URL} failed: {exc}")
    raise RuntimeError(
        "all real‑source fetches for UCI‑HAR failed: " + " | ".join(errors)
    )


def load_shopper() -> pd.DataFrame:
    """UCI Online Shoppers Purchasing Intention via HF jlh/uci-shopper."""
    errors: List[str] = []
    try:
        from datasets import load_dataset

        ds = load_dataset("jlh/uci-shopper", split="train")
        df = ds.to_pandas()
        if df is None or len(df) == 0:
            raise RuntimeError("empty dataframe from jlh/uci-shopper")
        return df
    except Exception as exc:  # real‑source fallback below, never synthetic
        errors.append(f"load_dataset failed: {exc}")
    try:
        content = _fetch_bytes(SHOPPER_VERIFIED_URL)
        df = pd.read_parquet(io.BytesIO(content))
        if df is None or len(df) == 0:
            raise RuntimeError("empty dataframe from verified shopper URL")
        return df
    except Exception as exc:
        errors.append(f"direct fetch of {SHOPPER_VERIFIED_URL} failed: {exc}")
    raise RuntimeError(
        "all real‑source fetches for UCI‑Shopper failed: " + " | ".join(errors)
    )


LOADERS: Dict[str, Tuple[Callable[[], pd.DataFrame], str]] = {
    "adult": (load_adult, "OpenML dataset 1590 (UCI Adult)"),
    "har": (load_har, 'HuggingFace datasets: udayl/UCI_HAR split="train"'),
    "shopper": (
        load_shopper,
        'HuggingFace datasets: jlh/uci-shopper split="train"',
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def current_rss_bytes() -> int:
    return psutil.Process().memory_info().rss


def _sanitize_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """Make mixed‑type object columns parquet‑writable without losing NaNs."""
    for col in df.columns:
        if df[col].dtype == object:
            mask = df[col].notna()
            if mask.any():
                vals = df.loc[mask, col]
                if not all(isinstance(v, str) for v in vals.head(1000).tolist()):
                    df.loc[mask, col] = vals.astype(str)
    return df


def _is_categorical(series: pd.Series) -> bool:
    return (
        series.dtype == object
        or isinstance(series.dtype, pd.CategoricalDtype)
        or series.dtype == bool
        or pd.api.types.is_string_dtype(series)
    )


def _relpath(p: Path) -> str:
    try:
        return str(p.relative_to(paths.root))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def process_dataset(name: str, df: pd.DataFrame, source: str) -> Dict:
    """Snapshot raw data, preprocess, split, and write all artifacts.

    Returns a dictionary summarising RAM usage and mitigation actions for
    inclusion in the global ``resource_summary.json`` file.
    """
    df = _sanitize_for_parquet(df.copy())
    log_lines: List[str] = [
        f"dataset={name}",
        f"source={source}",
        f"raw_rows={len(df)}",
        f"raw_columns={df.shape[1]}",
    ]

    # --- Raw snapshot + checksums (constitution Principle III) -----------
    raw_dir = paths.data("raw", name)
    raw_path = raw_dir / "raw.parquet"
    df.to_parquet(raw_path, index=False)
    digest = sha256_file(raw_path)
    checksums = {"raw.parquet": digest}
    (raw_dir / "checksums.sha256").write_text(
        "".join(f"{h}  {fn}\n" for fn, h in sorted(checksums.items()))
    )
    log_lines.append(f"raw_snapshot={_relpath(raw_path)} sha256={digest}")

    # --- Column typing -----------------------------------------------------
    cat_cols = [c for c in df.columns if _is_categorical(df[c])]
    num_cols = [c for c in df.columns if c not in cat_cols]
    log_lines.append(f"categorical_columns={cat_cols}")
    log_lines.append(f"numeric_columns={num_cols}")

    # --- Missing‑value handling -------------------------------------------
    dropped_all_nan: List[str] = []
    for col in df.columns:
        if df[col].isna().all():
            dropped_all_nan.append(col)
        elif col in cat_cols:
            mode = df[col].mode(dropna=True)
            df[col] = df[col].fillna(mode.iloc[0]) if len(mode) else df[col]
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())
    if dropped_all_nan:
        df = df.drop(columns=dropped_all_nan)
        cat_cols = [c for c in cat_cols if c not in dropped_all_nan]
        num_cols = [c for c in num_cols if c not in dropped_all_nan]
    log_lines.append(
        f"imputation=numeric:median categorical:mode "
        f"dropped_all_nan_columns={dropped_all_nan}"
    )

    # --- Categorical encoding (integer codes + recorded mapping) ----------
    mappings: Dict[str, Dict[str, int]] = {}
    for col in cat_cols:
        codes = df[col].astype("category")
        mappings[col] = {
            str(cat): int(i) for i, cat in enumerate(codes.cat.categories)
        }
        df[col] = codes.cat.codes.astype("int64")
    log_lines.append("encoding=strategy:integer_codes")

    # --- FR‑009 RAM monitoring and mitigation ------------------------------
    mitigations: List[str] = []
    peak_rss = current_rss_bytes()
    log_lines.append(f"peak_rss_bytes_after_preprocess={peak_rss}")
    if peak_rss > RAM_LIMIT_BYTES:
        high_card = [
            c
            for c in cat_cols
            if df[c].nunique() > HIGH_CARDINALITY_THRESHOLD
        ]
        if high_card:
            df = df.drop(columns=high_card)
            cat_cols = [c for c in cat_cols if c not in high_card]
            num_cols = [c for c in num_cols if c not in high_card]
            mitigations.append(
                f"dropped high‑cardinality categorical columns {high_card} "
                f"(cardinality > {HIGH_CARDINALITY_THRESHOLD})"
            )
        if current_rss_bytes() > RAM_LIMIT_BYTES and len(df) > MAX_ROWS_AFTER_MITIGATION:
            df = df.sample(n=MAX_ROWS_AFTER_MITIGATION, random_state=SEED)
            mitigations.append(
                f"uniformly down‑sampled to {MAX_ROWS_AFTER_MITIGATION} rows "
                f"(seed {SEED})"
            )
    log_lines.append(
        f"ram_mitigations={mitigations if mitigations else 'none'}"
    )

    # --- 80/20 train/hold‑out split (FR‑015, seed 123) --------------------
    train_df, holdout_df = train_test_split(
        df,
        train_size=SPLIT_FRACTION,
        random_state=SEED,
        shuffle=True,
    )

    proc_dir = paths.data("processed", name)
    train_path = proc_dir / "train.parquet"
    holdout_path = proc_dir / "holdout.parquet"
    train_df.to_parquet(train_path, index=False)
    holdout_df.to_parquet(holdout_path, index=False)
    log_lines.append(f"train_rows={len(train_df)} holdout_rows={len(holdout_df)}")
    log_lines.append(
        f"train_nulls={int(train_df.isna().sum().sum())} "
        f"holdout_nulls={int(holdout_df.isna().sum().sum())}"
    )

    # --- Provenance metadata ----------------------------------------------
    metadata = {
        "dataset": name,
        "source": source,
        "raw_snapshot": _relpath(raw_path),
        "checksums_file": _relpath(raw_dir / "checksums.sha256"),
        "checksums": checksums,
        "imputation": {
            "numeric": "median",
            "categorical": "mode",
            "dropped_all_nan_columns": dropped_all_nan,
        },
        "encoding": {
            "strategy": "integer_codes",
            "categorical_columns": cat_cols,
            "numeric_columns": num_cols,
            "mappings": mappings,
        },
        "split": {
            "fraction": SPLIT_FRACTION,
            "seed": SEED,
            "train_rows": int(len(train_df)),
            "holdout_rows": int(len(holdout_df)),
        },
        "ram_limit_bytes": RAM_LIMIT_BYTES,
        "ram_mitigations": mitigations,
        "columns": list(df.columns),
    }
    (proc_dir / "metadata.yaml").write_text(
        yaml.safe_dump(metadata, sort_keys=False)
    )

    (proc_dir / "preprocess_log.txt").write_text("\n".join(log_lines) + "\n")
    log.info(
        "processed %s: train=%d holdout=%d", name, len(train_df), len(holdout_df)
    )

    # -----------------------------------------------------------------------
    # Assemble a summary entry for the global resource‑summary JSON
    # -----------------------------------------------------------------------
    post_mitigation_rss = current_rss_bytes()
    summary_entry = {
        "dataset": name,
        "peak_ram_gb": round(peak_rss / (1024 ** 3), 3),
        "post_mitigation_ram_gb": round(post_mitigation_rss / (1024 ** 3), 3),
        "mitigation_applied": bool(mitigations),
        "completed_within_limit": post_mitigation_rss <= RAM_LIMIT_BYTES,
    }
    return summary_entry


def main(argv: List[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets",
        default="all",
        help="comma-separated subset of {adult,har,shopper} or 'all'",
    )
    args = parser.parse_args(argv)

    if args.datasets == "all":
        selected = list(LOADERS)
    else:
        selected = [
            s.strip() for s in args.datasets.split(",") if s.strip()
        ]
        unknown = [s for s in selected if s not in LOADERS]
        if unknown:
            parser.error(f"unknown datasets: {unknown}")

    for name in selected:
        loader, source = LOADERS[name]
        log.info("loading %s from %s", name, source)
        df = loader()  # fails loudly on any fetch failure
        summary = process_dataset(name, df, source)
        _resource_summary.append(summary)

    # After all datasets have been processed, write the aggregate summary.
    # The required location is ``outputs/metrics/resource_summary.json``.
    summary_path = paths.outputs("metrics", "resource_summary.json")
    # Compute the aggregate fraction of datasets that completed within RAM limit.
    total = len(_resource_summary)
    within = sum(1 for s in _resource_summary if s["completed_within_limit"])
    aggregate = {
        "datasets": _resource_summary,
        "fraction_completed_within_ram": round(within / total if total else 0, 3),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(aggregate, indent=2))

    log.info("resource summary written to %s", summary_path)


if __name__ == "__main__":
    main()