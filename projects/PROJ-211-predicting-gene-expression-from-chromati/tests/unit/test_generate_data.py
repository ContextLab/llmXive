"""
Unit tests for the synthetic data generator.

Tests verify:
- Seed reproducibility
- Output file existence
- Schema validity (columns, data types)
- Dimension constraints
"""

import os
import csv
import pytest
import pandas as pd
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from generate_data import (
    set_seed,
    generate_gene_coordinates,
    generate_peak_coordinates,
    generate_counts_matrix,
    CELL_LINES,
    NUM_GENES,
    NUM_PEAKS,
    SEED,
)

class TestSeedReproducibility:
    """Test that setting the seed produces deterministic results."""

    def test_set_seed_determinism(self):
        """Verify that setting seed twice produces same random values."""
        set_seed(SEED)
        val1 = random.random()

        set_seed(SEED)
        val2 = random.random()

        assert val1 == val2, "Seed setting is not deterministic"

    def test_numpy_seed_determinism(self):
        """Verify numpy seed setting is deterministic."""
        set_seed(SEED)
        arr1 = np.random.rand(5)

        set_seed(SEED)
        arr2 = np.random.rand(5)

        assert np.array_equal(arr1, arr2), "Numpy seed setting is not deterministic"

class TestGeneCoordinates:
    """Test synthetic gene coordinate generation."""

    def test_correct_number_of_genes(self):
        """Verify we generate the expected number of genes."""
        genes_df = generate_gene_coordinates(NUM_GENES)
        assert len(genes_df) == NUM_GENES

    def test_required_columns(self):
        """Verify gene DataFrame has required columns."""
        genes_df = generate_gene_coordinates(NUM_GENES)
        required_cols = ["gene_id", "chrom", "start", "strand"]
        for col in required_cols:
            assert col in genes_df.columns, f"Missing column: {col}"

    def test_gene_id_format(self):
        """Verify gene IDs follow expected format."""
        genes_df = generate_gene_coordinates(10)
        for gene_id in genes_df["gene_id"]:
            assert gene_id.startswith("GENE_"), f"Invalid gene_id format: {gene_id}"
            assert len(gene_id) == 10, f"Gene ID length mismatch: {gene_id}"

    def test_chromosome_values(self):
        """Verify chromosome values are valid."""
        genes_df = generate_gene_coordinates(100)
        valid_chroms = [f"chr{i}" for i in range(1, 23)] + ["chrX", "chrY"]
        for chrom in genes_df["chrom"]:
            assert chrom in valid_chroms, f"Invalid chromosome: {chrom}"

    def test_strand_values(self):
        """Verify strand values are valid."""
        genes_df = generate_gene_coordinates(100)
        valid_strands = ["+", "-"]
        for strand in genes_df["strand"]:
            assert strand in valid_strands, f"Invalid strand: {strand}"

class TestPeakCoordinates:
    """Test synthetic peak coordinate generation."""

    def test_correct_number_of_peaks(self):
        """Verify we generate the expected number of peaks."""
        peaks_df = generate_peak_coordinates(NUM_PEAKS, generate_gene_coordinates(10))
        assert len(peaks_df) == NUM_PEAKS

    def test_required_columns(self):
        """Verify peak DataFrame has required columns."""
        peaks_df = generate_peak_coordinates(NUM_PEAKS, generate_gene_coordinates(10))
        required_cols = ["chrom", "start", "end", "name", "score", "strand"]
        for col in required_cols:
            assert col in peaks_df.columns, f"Missing column: {col}"

    def test_bed_format_constraints(self):
        """Verify BED format constraints (start < end)."""
        peaks_df = generate_peak_coordinates(100, generate_gene_coordinates(10))
        for _, row in peaks_df.iterrows():
            assert row["start"] < row["end"], "BED start must be less than end"
            assert row["end"] - row["start"] <= 1000, "Peak width exceeds max (1000)"
            assert row["end"] - row["start"] >= 100, "Peak width below min (100)"

    def test_peak_id_format(self):
        """Verify peak IDs follow expected format."""
        peaks_df = generate_peak_coordinates(10, generate_gene_coordinates(10))
        for peak_id in peaks_df["name"]:
            assert peak_id.startswith("PEAK_"), f"Invalid peak_id format: {peak_id}"

class TestCountsMatrix:
    """Test synthetic count matrix generation."""

    def test_correct_dimensions(self):
        """Verify count matrix has correct dimensions."""
        genes_df = generate_gene_coordinates(NUM_GENES)
        peaks_df = generate_peak_coordinates(NUM_PEAKS, genes_df)
        counts_df = generate_counts_matrix(genes_df, peaks_df, CELL_LINES)

        assert counts_df.shape[0] == NUM_GENES, f"Wrong number of rows: {counts_df.shape[0]}"
        assert counts_df.shape[1] == len(CELL_LINES), "Wrong number of columns"

    def test_cell_line_columns(self):
        """Verify columns match expected cell lines."""
        genes_df = generate_gene_coordinates(NUM_GENES)
        peaks_df = generate_peak_coordinates(NUM_PEAKS, genes_df)
        counts_df = generate_counts_matrix(genes_df, peaks_df, CELL_LINES)

        for cell_line in CELL_LINES:
            assert cell_line in counts_df.columns, f"Missing cell line: {cell_line}"

    def test_non_negative_counts(self):
        """Verify all counts are non‑negative."""
        genes_df = generate_gene_coordinates(NUM_GENES)
        peaks_df = generate_peak_coordinates(NUM_PEAKS, genes_df)
        counts_df = generate_counts_matrix(genes_df, peaks_df, CELL_LINES)

        assert (counts_df >= 0).all().all(), "Found negative counts"

    def test_integer_counts(self):
        """Verify counts are integers."""
        genes_df = generate_gene_coordinates(NUM_GENES)
        peaks_df = generate_peak_coordinates(NUM_PEAKS, genes_df)
        counts_df = generate_counts_matrix(genes_df, peaks_df, CELL_LINES)

        # All values should be whole numbers
        assert counts_df.applymap(lambda x: float(x).is_integer()).all().all()

class TestIntegration:
    """Integration test for the full generation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Redirect output to a temporary directory."""
        self.original_raw = Path("data/raw")
        self.temp_raw = tmp_path / "raw"
        self.temp_raw.mkdir(parents=True, exist_ok=True)

        # Monkey‑patch the paths inside the module
        import importlib
        import generate_data

        generate_data.Path = lambda *p: Path(*p)  # ensure Path works normally
        generate_data.base_dir = self.temp_raw  # used in main()
        yield
        # No explicit teardown needed

    def test_file_creation(self):
        """Run the generator and check that files exist and are non‑empty."""
        import generate_data

        generate_data.main()

        counts_file = self.temp_raw / "synthetic_counts.csv"
        peaks_file = self.temp_raw / "synthetic_peaks.bed"
        checksum_file = self.temp_raw / "checksums.csv"

        for f in (counts_file, peaks_file, checksum_file):
            assert f.exists(), f"{f} was not created"
            assert f.stat().st_size > 0, f"{f} is empty"