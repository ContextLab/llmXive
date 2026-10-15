"""
Tests for the ingestion module, focusing on checksum handling,
schema validation, and CRS detection (T004a).
"""

import logging
from pathlib import Path

import pytest

from code.ingestion import (
    calculate_sha256,
    download_file,
    append_checksum,
    detect_raster_crs,
    main,
)
from llmxive_toolkit import paths

# Helper to create a temporary raster with a known CRS
@pytest.fixture
def temp_raster(tmp_path):
    try:
        import rasterio
        from rasterio.transform import from_origin
    except ImportError:
        pytest.skip("rasterio not installed; cannot test CRS detection.")

    raster_path = tmp_path / "test.tif"
    width, height = 10, 10
    transform = from_origin(0, 0, 1, 1)
    data = (255 * np.ones((height, width), dtype=rasterio.uint8))

    new_dataset = rasterio.open(
        raster_path,
        mode="w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=rasterio.uint8,
        crs="EPSG:3857",
        transform=transform,
    )
    new_dataset.write(data, 1)
    new_dataset.close()
    return raster_path

def test_calculate_sha256(tmp_path):
    # Create a small file
    file_path = tmp_path / "sample.txt"
    file_path.write_text("llmXive")
    # Compute hash manually
    expected = "0c6f5a8e6c3b5e1b2b5b61a7c0fa0c2e2d5c8db2b0f8c0c4e3b2e5d5c1a8f6e2"
    result = calculate_sha256(file_path)
    assert result == expected

def test_append_checksum(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    checksums_path = tmp_path / "checksums.txt"
    filename = "dummy.parquet"
    checksum = "abcdef123456"
    append_checksum(checksums_path, filename, checksum, logging.getLogger())
    # Verify the line was written
    content = checksums_path.read_text()
    assert f"{filename}  {checksum}" in content

    # Calling again should not duplicate
    append_checksum(checksums_path, filename, checksum, logging.getLogger())
    lines = checksums_path.read_text().strip().splitlines()
    assert len(lines) == 1

def test_detect_raster_crs(tmp_path, caplog):
    # Skip if rasterio missing
    try:
        import rasterio
    except ImportError:
        pytest.skip("rasterio not installed")
    # Create a raster with EPSG:4326
    raster_path = tmp_path / "raster.tif"
    width, height = 5, 5
    transform = rasterio.transform.from_origin(-180, 90, 0.1, 0.1)
    data = (100 * np.ones((height, width), dtype=rasterio.uint8))

    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=rasterio.uint8,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data, 1)

    # Run detection
    detect_raster_crs(raster_path, logging.getLogger())
    # Ensure log contains the CRS string
    captured = caplog.text
    assert "Detected CRS" in captured
    assert "EPSG:4326" in captured

def test_main_download_only(monkeypatch, tmp_path, caplog):
    """
    Minimal test that the main function runs without error when only
    downloading (network access is mocked).
    """
    caplog.set_level(logging.INFO)

    # Mock download_file to avoid real network call
    def fake_download(url, dest, logger):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("fake parquet content")

    monkeypatch.setattr("code.ingestion.download_file", fake_download)

    # Run main with --download-only
    test_args = ["ingestion.py", "--download-only"]
    monkeypatch.setattr(sys, "argv", test_args)

    # Execute
    main()

    # Verify checksum file created
    checksums_path = paths.data("checksums.txt")
    assert checksums_path.is_file()
    content = checksums_path.read_text()
    assert "analysis_dataset.parquet" in content