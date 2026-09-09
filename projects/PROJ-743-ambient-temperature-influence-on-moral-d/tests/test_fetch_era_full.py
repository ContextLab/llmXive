"""
Tests for T002c: fetch_era_full.py
Note: These are unit tests for logic. Integration tests require CDS API credentials.
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module functions
from fetch_era_full import frange, tile_overlaps_bbox, ensure_directories

class TestFrange:
    def test_frange_basic(self):
        result = list(frange(0, 1, 0.5))
        assert len(result) == 2
        assert abs(result[0] - 0.0) < 0.0001
        assert abs(result[1] - 0.5) < 0.0001

    def test_frange_step(self):
        result = list(frange(0, 3, 1.0))
        assert result == [0.0, 1.0, 2.0]

class TestTileOverlapsBbox:
    def test_complete_overlap(self):
        # Tile completely inside bbox
        tile = (10, 10, 20, 20)
        bbox = (0, 0, 30, 30)
        assert tile_overlaps_bbox(tile, bbox) is True

    def test_no_overlap_lat(self):
        # Tile above bbox
        tile = (40, 0, 50, 10)
        bbox = (0, 0, 30, 10)
        assert tile_overlaps_bbox(tile, bbox) is False

    def test_no_overlap_lon(self):
        # Tile to the right of bbox
        tile = (0, 40, 10, 50)
        bbox = (0, 0, 10, 30)
        assert tile_overlaps_bbox(tile, bbox) is False

    def test_edge_touch(self):
        # Tile touches edge
        tile = (30, 0, 40, 10)
        bbox = (0, 0, 30, 10)
        assert tile_overlaps_bbox(tile, bbox) is True

class TestEnsureDirectories:
    def test_creates_dirs(self, tmp_path):
        # Mock PROJECT_ROOT to use tmp_path
        import fetch_era_full
        original_root = fetch_era_full.PROJECT_ROOT
        fetch_era_full.PROJECT_ROOT = tmp_path
        
        try:
            ensure_directories()
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "external").exists()
            assert (tmp_path / "results" / "logs").exists()
            assert (tmp_path / "data" / "raw" / "era5_raw_chunks").exists()
        finally:
            fetch_era_full.PROJECT_ROOT = original_root
