import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from src.data_acquisition import (
    fetch_geo_dataset,
    parse_geo_metadata,
    check_response_labels,
    run_geo_acquisition,
    write_feasibility_gate_result,
    run_feasibility_gate
)

class TestGEOAcquisition:
    def test_fetch_geo_dataset_missing(self, tmp_path):
        """Test fetching a non-existent GEO ID returns None."""
        result = fetch_geo_dataset("GSE000000", tmp_path)
        assert result is None

    def test_parse_geo_metadata_no_labels(self, tmp_path):
        """Test parsing a file without response labels returns None."""
        # Create a dummy file with no keywords
        dummy_file = tmp_path / "GSE12345.gz"
        dummy_file.write_text("This is a test file with no response keywords.")
        
        # We need a gz file for the function to work properly with gzip.open
        # But for this test, we can mock or create a valid gz.
        # Let's create a valid gz file
        import gzip
        gz_file = tmp_path / "GSE12345_real.gz"
        with gzip.open(gz_file, 'wt') as f:
            f.write("This is a test file with no response keywords.")
        
        result = parse_geo_metadata(gz_file)
        assert result is None

    def test_parse_geo_metadata_with_labels(self, tmp_path):
        """Test parsing a file with response labels returns metadata."""
        import gzip
        gz_file = tmp_path / "GSE12345_real.gz"
        with gzip.open(gz_file, 'wt') as f:
            f.write("This file contains response data and CR/PR labels.")
        
        result = parse_geo_metadata(gz_file)
        assert result is not None
        assert 'found_keywords' in result
        assert len(result['found_keywords']) > 0

    def test_run_feasibility_gate_insufficient_geo(self, tmp_path):
        """Test that the gate halts if GEO count < 2."""
        gate_file = tmp_path / "feasibility_gate.json"
        result = run_feasibility_gate(tcga_count=5, geo_count=1, gate_file=gate_file)
        
        assert result is False
        assert gate_file.exists()
        with open(gate_file) as f:
            data = json.load(f)
        assert data['status'] == 'halted'
        assert data['reason'] == 'insufficient_geo_datasets'

    def test_run_feasibility_gate_insufficient_tcga(self, tmp_path):
        """Test that the gate halts if TCGA count < 3."""
        gate_file = tmp_path / "feasibility_gate.json"
        result = run_feasibility_gate(tcga_count=2, geo_count=5, gate_file=gate_file)
        
        assert result is False
        assert gate_file.exists()
        with open(gate_file) as f:
            data = json.load(f)
        assert data['status'] == 'halted'
        assert data['reason'] == 'insufficient_tcga_types'

    def test_run_feasibility_gate_success(self, tmp_path):
        """Test that the gate passes if counts are sufficient."""
        gate_file = tmp_path / "feasibility_gate.json"
        result = run_feasibility_gate(tcga_count=3, geo_count=2, gate_file=gate_file)
        
        assert result is True
        assert gate_file.exists()
        with open(gate_file) as f:
            data = json.load(f)
        assert data['status'] == 'ready'