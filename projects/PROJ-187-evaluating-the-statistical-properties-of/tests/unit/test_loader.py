"""Unit tests for the T001 data loader (FR-001, FR-009, FR-015)."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import yaml

from llmxive_toolkit import paths

DATASETS = ["adult", "har", "shopper"]


def _processed(name: str, filename: str) -> Path:
    p = paths.data("processed", name, filename)
    assert p.exists(), f"missing processed artifact: {p}"
    return p


def _metadata(name: str) -> dict:
    meta_path = paths.data("processed", name, "metadata.yaml")
    assert meta_path.exists(), f"missing provenance metadata: {meta_path}"
    with open(meta_path) as fh:
        return yaml.safe_load(fh)


def test_processed_files_exist():
    for name in DATASETS:
        _processed(name, "train.parquet")
        _processed(name, "holdout.parquet")
        _processed(name, "metadata.yaml")
        _processed(name, "preprocess_log.txt")
        assert paths.data("raw", name, "raw.parquet").exists()
        assert paths.data("raw", name, "checksums.sha256").exists()


def test_no_nulls_in_train_and_holdout():
    for name in DATASETS:
        for split in ("train", "holdout"):
            df = pd.read_parquet(_processed(name, f"{split}.parquet"))
            nulls = int(df.isna().sum().sum())
            assert nulls == 0, f"{name}/{split} contains {nulls} null values"


def test_split_fractions_80_20():
    for name in DATASETS:
        train = pd.read_parquet(_processed(name, "train.parquet"))
        holdout = pd.read_parquet(_processed(name, "holdout.parquet"))
        total = len(train) + len(holdout)
        assert total > 0
        train_frac = len(train) / total
        assert abs(train_frac - 0.8) < 0.01, (
            f"{name}: train fraction {train_frac:.4f} deviates from 0.8"
        )
        assert abs((1 - train_frac) - 0.2) < 0.01


def test_provenance_metadata_fields():
    required = {
        "dataset", "source", "raw_snapshot", "checksums_file", "checksums",
        "imputation", "encoding", "split", "ram_limit_bytes",
        "ram_mitigations", "columns",
    }
    for name in DATASETS:
        meta = _metadata(name)
        missing = required - set(meta)
        assert not missing, f"{name}: metadata missing keys {missing}"
        assert meta["split"]["fraction"] == 0.8
        assert meta["split"]["seed"] == 123
        assert meta["imputation"]["numeric"] == "median"
        assert meta["imputation"]["categorical"] == "mode"
        assert meta["encoding"]["strategy"] == "integer_codes"
        assert meta["ram_limit_bytes"] == int(6.5 * 1024 ** 3)


def test_recorded_checksums_match_recomputed_sha256():
    for name in DATASETS:
        cs_path = paths.data("raw", name, "checksums.sha256")
        assert cs_path.exists()
        lines = [
            ln for ln in cs_path.read_text().splitlines() if ln.strip()
        ]
        assert lines, f"{name}: checksums file is empty"
        for line in lines:
            digest, filename = line.split(None, 1)
            filename = filename.strip()
            target = paths.data("raw", name, filename)
            assert target.exists(), f"{name}: checksummed file missing: {target}"
            h = hashlib.sha256()
            with open(target, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            assert h.hexdigest() == digest, (
                f"{name}: SHA-256 mismatch for {filename}"
            )
        # metadata must reference the same checksums
        meta = _metadata(name)
        recorded = meta["checksums"]
        parsed = dict(
            (ln.split(None, 1)[1].strip(), ln.split(None, 1)[0]) for ln in lines
        )
        assert recorded == parsed