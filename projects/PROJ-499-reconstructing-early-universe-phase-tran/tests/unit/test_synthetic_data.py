import os
import json
import tempfile
import numpy as np
import healpy as hp
import pytest

# Ensure code is in path
sys_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
if sys_path not in os.sys.path:
    os.sys.path.insert(0, sys_path)

from synthetic_data import (
    generate_inflation_synthetic,
    generate_null_synthetic,
    generate_pt_synthetic,
    serialize_inflation_ground_truth,
    serialize_null_ground_truth,
    serialize_pt_ground_truth
)

class TestInflationSynthetic:
    def test_generates_inflation_map_file(self, tmp_path):
        """Test that generate_inflation_synthetic creates the FITS file."""
        output_path = str(tmp_path / "inflation_synthetic.fits")
        result = generate_inflation_synthetic(output_path, seed=42)
        
        assert os.path.exists(output_path), "Output FITS file was not created"
        assert result['model'] == 'inflation'
        assert abs(result['params']['r'] - 0.01) < 1e-6

    def test_inflation_map_is_valid_healpix(self, tmp_path):
        """Test that the generated file is a valid HEALPix map."""
        output_path = str(tmp_path / "inflation_synthetic.fits")
        generate_inflation_synthetic(output_path, seed=42)
        
        # Try to read it back
        m = hp.read_map(output_path)
        assert len(m) > 0
        assert hp.nside2npix(64) == len(m)

class TestNullSynthetic:
    def test_generates_null_map_file(self, tmp_path):
        """Test that generate_null_synthetic creates the FITS file."""
        output_path = str(tmp_path / "null_synthetic.fits")
        result = generate_null_synthetic(output_path, seed=44)
        
        assert os.path.exists(output_path), "Output FITS file was not created"
        assert result['model'] == 'null'

class TestGroundTruthSerialization:
    def test_serialize_inflation_ground_truth(self, tmp_path):
        """Test that serialize_inflation_ground_truth creates the JSON file."""
        output_path = str(tmp_path / "ground_truth_inflation.json")
        serialize_inflation_ground_truth(output_path)
        
        assert os.path.exists(output_path), "Ground truth JSON file was not created"
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['model_type'] == 'inflation'
        assert data['true_parameters']['r'] == 0.01
        assert data['true_parameters']['E_PT'] == 0.0

    def test_serialize_null_ground_truth(self, tmp_path):
        """Test that serialize_null_ground_truth creates the JSON file."""
        output_path = str(tmp_path / "ground_truth_null.json")
        serialize_null_ground_truth(output_path)
        
        assert os.path.exists(output_path), "Ground truth JSON file was not created"
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['model_type'] == 'null'
        assert data['true_parameters']['r'] == 0.0

class TestPTSynthetic:
    def test_generates_pt_map_file(self, tmp_path):
        """Test that generate_pt_synthetic creates the FITS file."""
        output_path = str(tmp_path / "pt_synthetic.fits")
        result = generate_pt_synthetic(output_path, seed=43)
        
        assert os.path.exists(output_path), "Output FITS file was not created"
        assert result['model'] == 'phase_transition'

    def test_serialize_pt_ground_truth(self, tmp_path):
        """Test that serialize_pt_ground_truth creates the JSON file."""
        output_path = str(tmp_path / "ground_truth_pt.json")
        serialize_pt_ground_truth(output_path)
        
        assert os.path.exists(output_path), "Ground truth JSON file was not created"
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['model_type'] == 'phase_transition'
        assert data['true_parameters']['E_PT'] == 1e15