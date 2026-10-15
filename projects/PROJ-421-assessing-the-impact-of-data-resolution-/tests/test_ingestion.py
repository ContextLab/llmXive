"""
Tests for the NLCD data ingestion script (T001).
"""
import json
from pathlib import Path

import rasterio
import pytest

from config import (
    DATA_RAW_DIR,
    NLCD_OUTPUT_FILENAME,
    NLCD_METADATA_FILENAME,
    NLCD_URL,
)
from code.data_ingestion import run_ingestion

@pytest.fixture(scope="module")
def ingested_paths(tmp_path_factory):
    """
    Run the ingestion once and provide the paths to the raster and metadata.
    """
    # Ensure we use the project‑wide raw directory (it will be created by the script)
    raster_path = run_ingestion()
    meta_path = Path(raster_path).parent / NLCD_METADATA_FILENAME
    return raster_path, meta_path

def test_raster_exists(ingested_paths):
    raster_path, _ = ingested_paths
    assert raster_path.is_file(), "Raster file was not created"

def test_metadata_exists_and_valid(ingested_paths):
    _, meta_path = ingested_paths
    assert meta_path.is_file(), "Metadata JSON was not created"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Basic schema checks
    assert "source_url" in meta and meta["source_url"] == NLCD_URL
    assert "crs" in meta and meta["crs"] == "EPSG:5070"
    # pixel size should be (30.0, 30.0) (allow tiny floating error)
    px = meta.get("pixel_size_m")
    assert isinstance(px, list) or isinstance(px, tuple)
    assert abs(px[0] - 30.0) < 0.01 and abs(px[1] - 30.0) < 0.01
    assert "dtype" in meta and meta["dtype"] in ("uint8", "uint16", "int16")
    assert isinstance(meta.get("class_list"), list) and len(meta["class_list"]) > 0

def test_raster_properties_match_metadata(ingested_paths):
    raster_path, meta_path = ingested_paths
    with rasterio.open(str(raster_path)) as src:
        crs = src.crs.to_string()
        transform = src.transform
        pixel_size = (abs(transform.a), abs(transform.e))
        dtype = src.dtypes[0]

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert crs == meta["crs"]
    assert abs(pixel_size[0] - meta["pixel_size_m"][0]) < 0.001
    assert abs(pixel_size[1] - meta["pixel_size_m"][1]) < 0.001
    assert dtype == meta["dtype"]
