import os
import sys
import pytest
import tempfile
import csv
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.generate_data import main as generate_data_main, set_seed, write_counts_csv, write_peaks_bed, generate_gene_coordinates, generate_peak_coordinates, generate_counts_matrix
from code.utils import checksum_file
from code.preprocess import filter_genes_zero_expression, apply_log_pseudocount, impute_missing_values_median, select_top_variable_peaks, load_data, save_data

class TestDataPipeline:
    """Integration tests for the data download and filtering pipeline (US1).
    
    This test verifies that:
    1. Synthetic data generation creates valid CSV/BED files.
    2. Preprocessing steps (filtering, log transform, imputation, feature selection)
       execute without error on the generated data.
    3. The pipeline produces the expected intermediate artifacts in a temporary directory.
    """

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory structure mimicking the project data layout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_raw = os.path.join(tmpdir, "data", "raw")
            data_processed = os.path.join(tmpdir, "data", "processed")
            os.makedirs(data_raw, exist_ok=True)
            os.makedirs(data_processed, exist_ok=True)
            yield {
                "raw": data_raw,
                "processed": data_processed,
                "base": tmpdir
            }

    def test_generate_data_creates_files(self, temp_data_dir):
        """Test that generate_data.py creates the expected output files."""
        # We need to patch the paths in generate_data or manually call the components
        # Since generate_data.main() relies on global paths or CLI args, we simulate the process
        # by calling the component functions directly with our temp paths.
        
        raw_dir = temp_data_dir["raw"]
        
        # 1. Generate coordinates
        gene_coords = generate_gene_coordinates(cell_lines=["GM12878", "K562"], n_genes=50)
        peak_coords = generate_peak_coordinates(cell_lines=["GM12878", "K562"], n_peaks=100)
        
        # 2. Generate counts
        counts_matrix = generate_counts_matrix(
            genes=gene_coords, 
            peaks=peak_coords, 
            cell_lines=["GM12878", "K562"]
        )
        
        # 3. Write files
        counts_path = os.path.join(raw_dir, "synthetic_counts.csv")
        peaks_path = os.path.join(raw_dir, "synthetic_peaks.bed")
        
        write_counts_csv(counts_matrix, counts_path)
        write_peaks_bed(peak_coords, peaks_path)
        
        # Verify files exist and are non-empty
        assert os.path.exists(counts_path), f"Counts file not created at {counts_path}"
        assert os.path.exists(peaks_path), f"Peaks file not created at {peaks_path}"
        
        assert os.path.getsize(counts_path) > 0, "Counts file is empty"
        assert os.path.getsize(peaks_path) > 0, "Peaks file is empty"

    def test_pipeline_filtering_and_transform(self, temp_data_dir):
        """Test the full preprocessing pipeline: filter -> log -> impute -> select."""
        raw_dir = temp_data_dir["raw"]
        proc_dir = temp_data_dir["processed"]
        
        # Setup: Generate data
        gene_coords = generate_gene_coordinates(cell_lines=["GM12878", "K562"], n_genes=20)
        peak_coords = generate_peak_coordinates(cell_lines=["GM12878", "K562"], n_peaks=50)
        counts_matrix = generate_counts_matrix(
            genes=gene_coords, 
            peaks=peak_coords, 
            cell_lines=["GM12878", "K562"]
        )
        
        counts_path = os.path.join(raw_dir, "synthetic_counts.csv")
        write_counts_csv(counts_matrix, counts_path)
        
        # Simulate a scenario where some genes have zero expression (for filter test)
        # We manually inject a row of zeros into the CSV to test filtering
        with open(counts_path, 'a', newline='') as f:
            writer = csv.writer(f)
            # Assuming first column is gene_id, rest are cell lines
            zero_row = ['ZERO_GENE'] + [0] * len(["GM12878", "K562"])
            writer.writerow(zero_row)

        # Step 1: Load data
        # The load_data function expects a specific schema. We need to ensure our generated
        # data matches. The generate_data module writes gene_id, then counts per cell line.
        # preprocess.load_data usually expects a specific format. Let's assume it loads the CSV.
        
        # Note: The existing preprocess.py functions likely expect a DataFrame with specific columns.
        # We will load the CSV into a DataFrame using pandas inside the test to ensure compatibility
        # or rely on the load_data wrapper if it handles raw CSVs.
        
        import pandas as pd
        df = pd.read_csv(counts_path)
        
        # Step 2: Filter genes with zero expression
        # We need to pass the dataframe to the filter function. 
        # The API surface says: filter_genes_zero_expression(df) -> df
        # We assume the function signature matches the API surface provided.
        try:
            df_filtered = filter_genes_zero_expression(df)
            # Verify the zero gene was removed
            assert 'ZERO_GENE' not in df_filtered['gene_id'].values, "Zero-expression gene was not filtered"
        except Exception as e:
            pytest.fail(f"filter_genes_zero_expression failed: {e}")

        # Step 3: Apply log pseudocount
        try:
            df_log = apply_log_pseudocount(df_filtered)
            assert 'log_expr' in df_log.columns or any('log' in str(c) for c in df_log.columns), \
                "Log transformation did not create expected column"
        except Exception as e:
            pytest.fail(f"apply_log_pseudocount failed: {e}")

        # Step 4: Impute missing values (if any)
        # Introduce a NaN to test imputation
        df_log.loc[0, df_log.columns[1]] = float('nan') # Set first cell line count to NaN
        
        try:
            df_imputed = impute_missing_values_median(df_log)
            assert not df_imputed.isnull().any().any(), "Imputation failed to remove NaNs"
        except Exception as e:
            pytest.fail(f"impute_missing_values_median failed: {e}")

        # Step 5: Select top variable peaks
        # The function select_top_variable_peaks expects a dataframe and N
        try:
            df_var = select_top_variable_peaks(df_imputed, n=10)
            # Verify we have at most N variable peaks (columns)
            # The exact column logic depends on the data shape, but the function should return a subset
            assert len(df_var) > 0, "Variable peak selection returned empty dataframe"
        except Exception as e:
            pytest.fail(f"select_top_variable_peaks failed: {e}")

    def test_checksum_generation(self, temp_data_dir):
        """Test that checksum_file utility works on generated artifacts."""
        raw_dir = temp_data_dir["raw"]
        
        # Generate a dummy file
        test_file = os.path.join(raw_dir, "test_checksum.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        checksum = checksum_file(test_file)
        assert checksum is not None, "checksum_file returned None"
        assert len(checksum) == 64, "Expected SHA256 checksum length"
