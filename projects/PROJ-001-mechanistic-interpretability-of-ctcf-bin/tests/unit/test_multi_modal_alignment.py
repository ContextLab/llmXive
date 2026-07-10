"""
Unit tests for multi-modal alignment in CTCF binding site analysis.

This module verifies:
1. Correct alignment of sequence, ATAC-seq, and histone mark data across modalities.
2. Proper handling and exclusion of entries with missing data.
3. Integrity of the unified dataset structure post-alignment.

Tests are designed to run against the data pipeline outputs defined in tasks.md,
specifically validating the exclusion logic for cell types with missing ATAC-seq data.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any
import pytest
import numpy as np
import pandas as pd

# Add project root to path to import code modules
# Assuming tests are at tests/unit/ and code is at code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.extract_features import align_modalities, process_window_data
from data.ingest import load_manifest


class TestMultiModalAlignment:
    """Tests for multi-modal data alignment and missing data handling."""

    def _create_mock_manifest(self, tmp_path: Path) -> Path:
        """Create a mock manifest.json with varied data availability."""
        manifest_data = {
            "cell_types": [
                {
                    "name": "K562",
                    "has_chipseq": True,
                    "has_atac": True,
                    "has_h3k27ac": True,
                    "files": {
                        "chipseq": "data/raw/k562_chipseq.bw",
                        "atac": "data/raw/k562_atac.bw",
                        "h3k27ac": "data/raw/k562_h3k27ac.bw"
                    }
                },
                {
                    "name": "GM12878",
                    "has_chipseq": True,
                    "has_atac": False,  # Missing ATAC-seq
                    "has_h3k27ac": True,
                    "files": {
                        "chipseq": "data/raw/gm12878_chipseq.bw",
                        "h3k27ac": "data/raw/gm12878_h3k27ac.bw"
                    }
                },
                {
                    "name": "HEK293",
                    "has_chipseq": True,
                    "has_atac": True,
                    "has_h3k27ac": False,  # Missing H3K27ac
                    "files": {
                        "chipseq": "data/raw/hek293_chipseq.bw",
                        "atac": "data/raw/hek293_atac.bw"
                    }
                }
            ],
            "version": "1.0"
        }
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        return manifest_path

    def _create_mock_feature_data(self, tmp_path: Path, cell_type: str) -> Path:
        """Create mock extracted feature data for a specific cell type."""
        # Simulate 1000bp windows (500 left + 500 right)
        num_windows = 10
        data = {
            "cell_type": cell_type,
            "windows": []
        }
        
        for i in range(num_windows):
            window_data = {
                "window_id": f"{cell_type}_win_{i}",
                "sequence": "A" * 1000,  # Mock sequence
                "peak_center": 5000 + i * 1000,
                "chipseq_signal": [0.5 + i * 0.1] * 100,  # Mock signal
                "atac_signal": [0.2 + i * 0.05] * 100 if cell_type != "GM12878" else None,
                "h3k27ac_signal": [0.3 + i * 0.02] * 100 if cell_type != "HEK293" else None
            }
            data["windows"].append(window_data)
        
        feature_path = tmp_path / f"features_{cell_type}.json"
        with open(feature_path, 'w') as f:
            json.dump(data, f)
        return feature_path

    def test_align_modalities_excludes_missing_atac(self, tmp_path: Path):
        """Verify that cell types with missing ATAC-seq data are excluded."""
        manifest_path = self._create_mock_manifest(tmp_path)
        
        # Create feature files for all cell types
        self._create_mock_feature_data(tmp_path, "K562")
        self._create_mock_feature_data(tmp_path, "GM12878")  # Missing ATAC
        self._create_mock_feature_data(tmp_path, "HEK293")   # Missing H3K27ac
        
        # Load manifest
        manifest = load_manifest(str(manifest_path))
        
        # Get feature file paths
        feature_files = {
            ct["name"]: str(tmp_path / f"features_{ct['name']}.json")
            for ct in manifest["cell_types"]
        }
        
        # Run alignment
        aligned_data, excluded_cells = align_modalities(
            manifest=manifest,
            feature_files=feature_files,
            required_modalities=["chipseq", "atac"]
        )
        
        # Assertions
        assert "GM12878" in excluded_cells, "GM12878 should be excluded due to missing ATAC-seq"
        assert "K562" not in excluded_cells, "K562 should be included"
        assert "HEK293" in excluded_cells, "HEK293 should be excluded due to missing ATAC-seq requirement"
        
        # Verify aligned data only contains K562
        assert len(aligned_data) == 1
        assert "K562" in aligned_data
        assert aligned_data["K562"]["cell_type"] == "K562"

    def test_align_modalities_handles_partial_data(self, tmp_path: Path):
        """Verify alignment handles cells with some modalities missing but not all required ones."""
        manifest_data = {
            "cell_types": [
                {
                    "name": "H1-HESC",
                    "has_chipseq": True,
                    "has_atac": True,
                    "has_h3k27ac": False,  # Missing H3K27ac but not required
                    "files": {
                        "chipseq": "data/raw/h1_chipseq.bw",
                        "atac": "data/raw/h1_atac.bw"
                    }
                }
            ]
        }
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Create feature file
        feature_path = self._create_mock_feature_data(tmp_path, "H1-HESC")
        
        manifest = load_manifest(str(manifest_path))
        feature_files = {"H1-HESC": str(feature_path)}
        
        # Run alignment with only chipseq and atac required
        aligned_data, excluded_cells = align_modalities(
            manifest=manifest,
            feature_files=feature_files,
            required_modalities=["chipseq", "atac"]
        )
        
        # H1-HESC should NOT be excluded since required modalities are present
        assert "H1-HESC" not in excluded_cells
        assert len(aligned_data) == 1

    def test_process_window_data_handles_null_signals(self, tmp_path: Path):
        """Verify that process_window_data correctly handles null signal values."""
        # Create a window with null ATAC signal
        window_data = {
            "window_id": "test_win_1",
            "sequence": "A" * 1000,
            "peak_center": 5000,
            "chipseq_signal": [0.5] * 100,
            "atac_signal": None,  # Null ATAC signal
            "h3k27ac_signal": [0.3] * 100
        }
        
        # This should raise an error or return a filtered result
        # depending on implementation
        try:
            result = process_window_data(window_data, required_modalities=["atac"])
            # If implementation allows partial data, verify nulls are handled
            assert result is not None
        except ValueError as e:
            # Expected if strict exclusion is enforced
            assert "missing required modality" in str(e).lower()

    def test_alignment_preserves_sequence_length(self, tmp_path: Path):
        """Verify that aligned data preserves the expected sequence length."""
        manifest_path = self._create_mock_manifest(tmp_path)
        self._create_mock_feature_data(tmp_path, "K562")
        
        manifest = load_manifest(str(manifest_path))
        feature_files = {"K562": str(tmp_path / "features_K562.json")}
        
        aligned_data, _ = align_modalities(
            manifest=manifest,
            feature_files=feature_files,
            required_modalities=["chipseq", "atac"]
        )
        
        # Check sequence length in aligned data
        for window in aligned_data["K562"]["windows"]:
            assert len(window["sequence"]) == 1000, "Sequence length should be 1000bp"

    def test_exclusion_reasons_logged(self, tmp_path: Path):
        """Verify that exclusion reasons are properly recorded."""
        manifest_path = self._create_mock_manifest(tmp_path)
        self._create_mock_feature_data(tmp_path, "K562")
        self._create_mock_feature_data(tmp_path, "GM12878")
        
        manifest = load_manifest(str(manifest_path))
        feature_files = {
            "K562": str(tmp_path / "features_K562.json"),
            "GM12878": str(tmp_path / "features_GM12878.json")
        }
        
        aligned_data, excluded_cells = align_modalities(
            manifest=manifest,
            feature_files=feature_files,
            required_modalities=["chipseq", "atac"]
        )
        
        # Verify exclusion reasons are included
        assert "GM12878" in excluded_cells
        assert "missing" in str(excluded_cells["GM12878"]).lower() or "required" in str(excluded_cells["GM12878"]).lower()

    def test_empty_result_when_all_excluded(self, tmp_path: Path):
        """Verify behavior when all cell types are excluded."""
        manifest_data = {
            "cell_types": [
                {
                    "name": "Cell1",
                    "has_chipseq": True,
                    "has_atac": False,
                    "has_h3k27ac": False,
                    "files": {"chipseq": "data/raw/cell1_chipseq.bw"}
                },
                {
                    "name": "Cell2",
                    "has_chipseq": False,
                    "has_atac": False,
                    "has_h3k27ac": False,
                    "files": {}
                }
            ]
        }
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        manifest = load_manifest(str(manifest_path))
        feature_files = {
            "Cell1": str(tmp_path / "features_Cell1.json"),
            "Cell2": str(tmp_path / "features_Cell2.json")
        }
        
        aligned_data, excluded_cells = align_modalities(
            manifest=manifest,
            feature_files=feature_files,
            required_modalities=["chipseq", "atac"]
        )
        
        assert len(aligned_data) == 0
        assert len(excluded_cells) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])