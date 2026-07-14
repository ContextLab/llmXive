"""
Integration test for the benchmark‑download script (T056).

The test invokes the ``main`` function from ``code.data_acquisition.download_benchmark``
and then checks that:
  1. The CSV file exists under ``data/raw/benchmark/``.
  2. The accompanying ``metadata.json`` file exists.
  3. The checksum recorded in the metadata matches the actual file checksum.
"""

import json
from pathlib import Path

from code.data_acquisition.download_benchmark import (
    BENCHMARK_FILENAME,
    METADATA_FILENAME,
    compute_sha256,
    main,
)


def test_benchmark_download_and_verification(tmp_path, monkeypatch):
    """
    Run the benchmark download script and validate its output.

    ``tmp_path`` is a pytest fixture that provides an isolated temporary
    directory.  We monkey‑patch the project‑relative ``data`` directory to
    point inside this temporary location so the test does not pollute the
    repository's real data folder.
    """
    # Redirect the project's data root to the temporary directory.
    project_root = Path(__file__).resolve().parents[2]  # repo root
    fake_data_root = tmp_path / "data"
    monkeypatch.setattr(
        "code.data_acquisition.download_benchmark.Path",
        lambda *parts: Path(*parts).relative_to(project_root) if parts else Path(),
    )
    # Ensure the script uses the temporary location.
    monkeypatch.setenv("PYTHONPATH", str(project_root))

    # Run the download routine.
    main()

    # Resolve expected locations.
    dataset_path = Path("data") / "raw" / "benchmark" / BENCHMARK_FILENAME
    metadata_path = Path("data") / "raw" / "benchmark" / METADATA_FILENAME

    # The files must exist.
    assert dataset_path.is_file(), f"Dataset file missing: {dataset_path}"
    assert metadata_path.is_file(), f"Metadata file missing: {metadata_path}"

    # Load metadata and verify checksum.
    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)

    expected_checksum = metadata.get("sha256")
    actual_checksum = compute_sha256(dataset_path)

    assert (
        expected_checksum == actual_checksum
    ), "Checksum in metadata does not match actual file checksum"