import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Import the function to test
# Note: The import path assumes tests are run from the project root or with code in PYTHONPATH
# The agent prompt says "code/tests/conftest.py" exists, so we assume standard project structure.
# We will import directly from the module file if needed, but standard practice is:
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from mock_data import generate_mock_dataset


class TestMockDataGeneration:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for each test and clean up afterwards."""
        self.temp_dir = Path(tempfile.mkdtemp())
        yield self.temp_dir
        shutil.rmtree(self.temp_dir)

    def test_files_created(self, setup_teardown):
        """Test that all expected CSV files are created."""
        output_dir = setup_teardown
        generate_mock_dataset(output_dir=output_dir, num_accessions=10, num_snps=50)
        
        assert (output_dir / "accessions.csv").exists()
        assert (output_dir / "phenotypes.csv").exists()
        assert (output_dir / "genotypes.csv").exists()

    def test_accessions_schema(self, setup_teardown):
        """Test that accessions.csv has the correct columns and types."""
        output_dir = setup_teardown
        generate_mock_dataset(output_dir=output_dir, num_accessions=10, num_snps=50)
        
        df = pd.read_csv(output_dir / "accessions.csv")
        
        expected_cols = ["accession_id", "country", "latitude", "longitude", "collection_year"]
        assert list(df.columns) == expected_cols
        
        assert len(df) == 10
        assert df["accession_id"].dtype == "object"
        assert df["country"].dtype == "object"
        assert np.issubdtype(df["latitude"].dtype, np.floating)
        assert np.issubdtype(df["longitude"].dtype, np.floating)
        assert np.issubdtype(df["collection_year"].dtype, np.integer)

    def test_phenotypes_schema(self, setup_teardown):
        """Test that phenotypes.csv has the correct columns and structure."""
        output_dir = setup_dir = setup_teardown
        generate_mock_dataset(output_dir=output_dir, num_accessions=10, num_snps=50)
        
        df = pd.read_csv(output_dir / "phenotypes.csv")
        
        expected_cols = ["accession_id", "nutrient_condition", "root_length", "root_angle", "lateral_root_count", "branching_density"]
        assert list(df.columns) == expected_cols
        
        # 10 accessions * 3 conditions = 30 rows
        assert len(df) == 30
        
        # Check nutrient conditions
        conditions = df["nutrient_condition"].unique()
        assert set(conditions) == {"Low_N", "High_N", "Control"}

    def test_genotypes_schema_and_encoding(self, setup_teardown):
        """Test that genotypes.csv has the correct columns and SNP encoding (0, 1, 2)."""
        output_dir = setup_teardown
        num_accessions = 10
        num_snps = 50
        generate_mock_dataset(output_dir=output_dir, num_accessions=num_accessions, num_snps=num_snps)
        
        df = pd.read_csv(output_dir / "genotypes.csv")
        
        # Check accession_id column
        assert "accession_id" in df.columns
        assert len(df) == num_accessions
        
        # Check SNP columns
        snp_cols = [col for col in df.columns if col.startswith("SNP_")]
        assert len(snp_cols) == num_snps
        
        # Check that all SNP values are 0, 1, or 2
        for col in snp_cols:
            unique_vals = set(df[col].unique())
            assert unique_vals.issubset({0, 1, 2}), f"Column {col} contains invalid values: {unique_vals}"

    def test_data_consistency(self, setup_teardown):
        """Test that accessions in all files match."""
        output_dir = setup_teardown
        num_accessions = 10
        generate_mock_dataset(output_dir=output_dir, num_accessions=num_accessions, num_snps=50)
        
        accessions_df = pd.read_csv(output_dir / "accessions.csv")
        phenotypes_df = pd.read_csv(output_dir / "phenotypes.csv")
        genotypes_df = pd.read_csv(output_dir / "genotypes.csv")
        
        accessions_in_pheno = set(phenotypes_df["accession_id"].unique())
        accessions_in_genotypes = set(genotypes_df["accession_id"].unique())
        accessions_in_meta = set(accessions_df["accession_id"].unique())
        
        assert accessions_in_pheno == accessions_in_meta
        assert accessions_in_genotypes == accessions_in_meta

    def test_reproducibility(self, setup_teardown):
        """Test that running the function twice produces the same output."""
        output_dir1 = setup_teardown / "run1"
        output_dir2 = setup_teardown / "run2"
        
        generate_mock_dataset(output_dir=output_dir1, num_accessions=10, num_snps=50)
        generate_mock_dataset(output_dir=output_dir2, num_accessions=10, num_snps=50)
        
        df1 = pd.read_csv(output_dir1 / "genotypes.csv")
        df2 = pd.read_csv(output_dir2 / "genotypes.csv")
        
        assert df1.equals(df2)