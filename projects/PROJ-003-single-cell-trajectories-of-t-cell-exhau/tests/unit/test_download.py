"""Unit tests for the GEO downloader (T002).

These tests confirm (per tasks.md verification for T002):
- four Dataset entries exist in data/manifest.yaml with status available,
- a SHA-256 checksum is recorded and matches the file on disk,
- marker_gene_fraction >= 0.80 for every dataset (FR-010 / SC-005),
- raw files exist under data/raw/<accession>/.
"""

import hashlib
from pathlib import Path

import pytest
import yaml

EXPECTED_GSES = ["GSE136103", "GSE127465", "GSE111075", "GSE138852"]
MANIFEST_PATH = Path("data/manifest.yaml")


def _load_manifest():
    if not MANIFEST_PATH.exists():
        pytest.skip(
            "data/manifest.yaml not found - run "
            "'python -m code.download_data' first"
        )
    with MANIFEST_PATH.open("r") as f:
        return yaml.safe_load(f)


def test_manifest_has_four_dataset_entries():
    manifest = _load_manifest()
    datasets = manifest.get("datasets", {})
    for gse in EXPECTED_GSES:
        assert gse in datasets, f"Dataset {gse} missing from manifest"
        entry = datasets[gse]
        for field in (
            "dataset_id", "source", "raw_counts_path", "checksum",
            "cell_count", "gene_count", "marker_gene_fraction", "status",
        ):
            assert field in entry, f"Field {field} missing for {gse}"
        assert entry["status"] == "available", (
            f"Dataset {gse} status is {entry['status']}, expected available"
        )


def test_checksums_recorded_and_match_files():
    manifest = _load_manifest()
    for gse in EXPECTED_GSES:
        entry = manifest["datasets"][gse]
        checksum = entry["checksum"]
        assert isinstance(checksum, str) and len(checksum) == 64, (
            f"Invalid SHA-256 checksum recorded for {gse}: {checksum}"
        )
        matrix_path = Path(entry["raw_counts_path"])
        assert matrix_path.exists(), f"Matrix file missing for {gse}: {matrix_path}"
        actual = hashlib.sha256(matrix_path.read_bytes()).hexdigest()
        assert actual == checksum, (
            f"Checksum mismatch for {gse}: manifest {checksum} vs actual {actual}"
        )


def test_marker_gene_fraction_at_least_080():
    """FR-010 / SC-005: at least 80% of the required marker list present."""
    manifest = _load_manifest()
    for gse in EXPECTED_GSES:
        entry = manifest["datasets"][gse]
        fraction = entry["marker_gene_fraction"]
        assert 0.0 <= fraction <= 1.0, f"Fraction out of range for {gse}"
        assert fraction >= 0.80, (
            f"marker_gene_fraction for {gse} is {fraction}, must be >= 0.80"
        )


def test_raw_files_exist():
    raw_root = Path("data/raw")
    for gse in EXPECTED_GSES:
        gse_dir = raw_root / gse
        assert gse_dir.exists(), f"Directory for {gse} should exist"
        files = [p for p in gse_dir.rglob("*") if p.is_file()]
        assert files, f"No raw files found for {gse}"


def test_manifest_entries_match_dataset_schema():
    """Entries in data/manifest.yaml validate against the Dataset schema."""
    schema_path = (
        Path("specs")
        / "001-single-cell-trajectories-of-t-cell-exhaustion"
        / "contracts" / "dataset.schema.yaml"
    )
    if not schema_path.exists():
        schema_path = (
            Path("..") / "specs"
            / "001-single-cell-trajectories-of-t-cell-exhaustion"
            / "contracts" / "dataset.schema.yaml"
        )
    if not schema_path.exists():
        pytest.skip("dataset.schema.yaml not found in repository")
    import jsonschema

    with schema_path.open("r") as f:
        schema = yaml.safe_load(f)
    manifest = _load_manifest()
    for gse in EXPECTED_GSES:
        jsonschema.validate(instance=manifest["datasets"][gse], schema=schema)