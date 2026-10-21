import os
import pytest
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")

def test_downloaded_files_exist():
    """Verify that all required cell line files and the gene coords file exist."""
    cell_lines = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
    for cl in cell_lines:
        counts_file = RAW_DIR / f"encode_counts_{cl}.csv"
        peaks_file = RAW_DIR / f"encode_peaks_{cl}.bed"
        assert counts_file.exists(), f"Missing counts file for {cl}"
        assert peaks_file.exists(), f"Missing peaks file for {cl}"
        assert counts_file.stat().st_size > 0, f"Empty counts file for {cl}"
        assert peaks_file.stat().st_size > 0, f"Empty peaks file for {cl}"
    
    gene_coords = RAW_DIR / "gene_coords.bed"
    assert gene_coords.exists(), "Missing gene_coords.bed"
    assert gene_coords.stat().st_size > 0, "Empty gene_coords.bed"

def test_counts_column_headers():
    """Verify that RNA-seq counts CSVs have correct headers."""
    cell_lines = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
    for cl in cell_lines:
        df = pd.read_csv(RAW_DIR / f"encode_counts_{cl}.csv")
        expected_cols = ["gene_id", "gene_name", "cell_line", "count"]
        assert all(col in df.columns for col in expected_cols), f"Incorrect columns in {cl} counts"

def test_peaks_format():
    """Verify that accessibility BED files have 6 columns."""
    cell_lines = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
    for cl in cell_lines:
        with open(RAW_DIR / f"encode_peaks_{cl}.bed", "r") as f:
            first_line = f.readline()
            assert len(first_line.strip().split("\t")) == 6, f"BED file for {cl} does not have 6 columns"

def test_gene_coords_format():
    """Verify that gene_coords.bed has 6 columns."""
    with open(RAW_DIR / "gene_coords.bed", "r") as f:
        first_line = f.readline()
        assert len(first_line.strip().split("\t")) == 6, "gene_coords.bed does not have 6 columns"

def test_checksums_recorded():
    """Verify that checksums.csv exists and contains entries."""
    checksum_file = RAW_DIR / "checksums.csv"
    assert checksum_file.exists(), "checksums.csv not found"
    df = pd.read_csv(checksum_file)
    assert not df.empty, "checksums.csv is empty"
    assert "filename" in df.columns and "sha256" in df.columns
    # Expect at least 11 files (5 counts, 5 peaks, 1 gene_coords)
    assert len(df) >= 11