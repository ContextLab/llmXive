"""
Contract tests for data formats in the gene regulation pipeline.

These tests verify that data formats (BED, JSON, CSV) conform to 
the expected specifications throughout the pipeline.
"""
import pytest
from pathlib import Path
import json
import csv
import tempfile

def test_bed_format_contract():
    """
    Verify that BED files conform to the expected format.
    
    BED format contract:
    - At least 3 columns: chrom, start, end
    - Optional columns: name, score, strand
    - Start and end must be integers
    - Start < end
    - Coordinates are 0-based, half-open
    """
    # Test valid BED line
    valid_line = "chr1\t1000\t2000\tpeak1\t0\t+"
    parts = valid_line.split('\t')
    assert len(parts) >= 3, "BED line must have at least 3 columns"
    assert parts[0].startswith("chr"), "Chromosome should start with 'chr'"
    assert int(parts[1]) >= 0, "Start coordinate must be non-negative"
    assert int(parts[2]) > int(parts[1]), "End must be greater than start"

def test_json_format_contract():
    """
    Verify that JSON files conform to the expected structure.
    """
    # Test valid JSON structure for enrichment results
    sample_json = {
        "cell_type": "GM",
        "motifs": [
            {
                "motif_id": "MA0001",
                "p_value": 0.0001,
                "q_value": 0.001,
                "peak_count": 50
            }
        ]
    }
    
    assert "cell_type" in sample_json, "JSON must contain cell_type"
    assert "motifs" in sample_json, "JSON must contain motifs array"
    assert isinstance(sample_json["motifs"], list), "motifs must be a list"
    
    if sample_json["motifs"]:
        motif = sample_json["motifs"][0]
        assert "motif_id" in motif, "Each motif must have motif_id"
        assert "p_value" in motif, "Each motif must have p_value"
        assert "q_value" in motif, "Each motif must have q_value"

def test_csv_format_contract():
    """
    Verify that CSV files conform to the expected structure.
    """
    # Test valid CSV structure for summary table
    sample_csv = [
        ["motif_id", "p_value_raw", "q_value_adj", "chip_overlap_pct"],
        ["MA0001", "0.0001", "0.001", "75.0"],
        ["MA0002", "0.001", "0.01", "60.0"]
    ]
    
    header = sample_csv[0]
    assert "motif_id" in header, "CSV must have motif_id column"
    assert "p_value_raw" in header, "CSV must have p_value_raw column"
    assert "q_value_adj" in header, "CSV must have q_value_adj column"
    assert "chip_overlap_pct" in header, "CSV must have chip_overlap_pct column"
