"""
Unit tests for bin_mapping.py
"""
import pytest
import json
import os
import numpy as np
from pathlib import Path
import tempfile

# Import the functions to test
from src.ingestion.bin_mapping import (
    generate_ir_bins,
    generate_nmr_bins,
    generate_bin_mapping,
    IR_START, IR_END, NMR_MIN, NMR_MAX
)
from src.utils.io import read_json_file

class TestBinMappingGeneration:
    def test_ir_bins_structure(self):
        """Test that IR bins are generated with correct structure and interpolation method."""
        num_bins = 100
        result = generate_ir_bins(IR_START, IR_END, num_bins)

        assert result["type"] == "IR"
        assert "linear" in result["description"].lower()
        assert result["num_bins"] == num_bins
        assert result["interpolation_method"] == "linear"
        assert "bin_edges" in result
        assert "bin_centers" in result
        assert len(result["bin_edges"]) == num_bins + 1
        assert len(result["bin_centers"]) == num_bins

    def test_ir_bins_values(self):
        """Test that IR bins cover the correct range."""
        num_bins = 100
        result = generate_ir_bins(IR_START, IR_END, num_bins)

        # Check start and end
        assert result["bin_edges"][0] == IR_START
        assert result["bin_edges"][-1] == IR_END

        # Check that edges are monotonically decreasing (4000 -> 400)
        edges = result["bin_edges"]
        for i in range(len(edges) - 1):
            assert edges[i] >= edges[i+1]

    def test_nmr_bins_structure(self):
        """Test that NMR bins are generated with correct structure."""
        num_bins = 100
        result = generate_nmr_bins(NMR_MAX, NMR_MIN, num_bins)

        assert result["type"] == "NMR"
        assert "linear" in result["description"].lower()
        assert result["num_bins"] == num_bins
        assert result["interpolation_method"] == "linear"
        assert "bin_edges" in result
        assert "bin_centers" in result

    def test_nmr_bins_values(self):
        """Test that NMR bins cover the correct range."""
        num_bins = 100
        result = generate_nmr_bins(NMR_MAX, NMR_MIN, num_bins)

        # Check start and end
        assert result["bin_edges"][0] == NMR_MAX
        assert result["bin_edges"][-1] == NMR_MIN

    def test_generate_bin_mapping_writes_file(self):
        """Test that generate_bin_mapping writes a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_bin_mapping.json")

            generate_bin_mapping(output_path, ir_bins=50, nmr_bins=50)

            assert os.path.exists(output_path)

            # Read and validate
            data = read_json_file(output_path)

            assert "spectra" in data
            assert "IR" in data["spectra"]
            assert "NMR" in data["spectra"]
            assert data["spectra"]["IR"]["interpolation_method"] == "linear"
            assert data["spectra"]["NMR"]["interpolation_method"] == "linear"

            # Check explicit description requirements
            assert "linear interpolation" in data["spectra"]["IR"]["description"].lower()
            assert "linear interpolation" in data["spectra"]["NMR"]["description"].lower()

    def test_bin_mapping_contains_required_descriptions(self):
        """Verify the specific descriptions required by the task are present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_bin_mapping.json")
            generate_bin_mapping(output_path, ir_bins=10, nmr_bins=10)
            data = read_json_file(output_path)

            ir_desc = data["spectra"]["IR"]["description"]
            nmr_desc = data["spectra"]["NMR"]["description"]

            # Task requirement: 'Bins [variable range]: IR (linear interpolation)'
            assert "IR" in ir_desc
            assert "linear interpolation" in ir_desc
            assert "variable range" in ir_desc

            # Task requirement: 'Bins: NMR -12 ppm (linear interpolation)'
            assert "NMR" in nmr_desc
            assert "-12 ppm" in nmr_desc
            assert "linear interpolation" in nmr_desc