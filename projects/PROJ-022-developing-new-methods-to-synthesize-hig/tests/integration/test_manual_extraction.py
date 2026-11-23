"""
Integration tests for manual literature extraction module.

Tests the end-to-end flow of loading and parsing manual extraction CSV files.
"""

import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from ingestion.manual_extraction import (
    load_manual_csv,
    parse_manual_records,
    extract_manual_literature_data
)
from utils.errors import ConfigurationError, ValidationError


class TestManualExtraction:
    """Integration tests for manual extraction functionality."""

    @pytest.fixture
    def sample_csv_content(self):
        """Sample CSV content for testing."""
        return """smiles,polymer_name,permeability_co2,permeability_o2,selectivity_co2_o2,source_reference
"CC(C)(C)c1ccc(cc1)S(=O)(=O)c2ccc(cc2)Nc3ccc(cc3)Nc4ccc(cc4)S(=O)(=O)c5ccc(cc5)C(C)(C)C",Poly(ether sulfone) derivative,12.5,2.1,5.95,"Smith et al., J. Membr. Sci. 2022"
"CC1=CC(=C(C=C1NC(=O)C2=CC(=CC=C2C(=O)NC3=CC=C(C=C3)C(=O)O)C(=O)NC4=CC(=CC=C4)C(=O)O)C5=CC(=CC=C5C(=O)NC6=CC(=CC=C6)C(=O)O)C(=O)O)O",Polyimide-cellulose hybrid,8.2,1.4,5.86,"Chen et al., Polymer 2023"
"""

    @pytest.fixture
    def temp_csv_file(self, sample_csv_content):
        """Create a temporary CSV file with sample content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_input_dir(self, sample_csv_content):
        """Create a temporary directory with a CSV file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, "test_extraction.csv")
            with open(csv_path, 'w') as f:
                f.write(sample_csv_content)
            yield temp_dir

    def test_load_manual_csv_success(self, temp_csv_file):
        """Test successful loading of a valid CSV file."""
        df = load_manual_csv(temp_csv_file)
        assert len(df) == 2
        assert 'smiles' in df.columns
        assert 'polymer_name' in df.columns
        assert 'permeability_co2' in df.columns
        assert 'selectivity_co2_o2' in df.columns

    def test_load_manual_csv_missing_file(self):
        """Test loading a non-existent file raises ConfigurationError."""
        with pytest.raises(ConfigurationError):
            load_manual_csv("non_existent_file.csv")

    def test_load_manual_csv_missing_columns(self, temp_csv_content):
        """Test loading a CSV with missing required columns raises ValidationError."""
        invalid_content = """smiles,polymer_name
"CC(C)(C)c1ccc(cc1)",Test Polymer
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(invalid_content)
            temp_path = f.name

        try:
            with pytest.raises(ValidationError):
                load_manual_csv(temp_path)
        finally:
            os.unlink(temp_path)

    def test_parse_manual_records(self, temp_csv_file):
        """Test parsing DataFrame rows to PolymerRecord objects."""
        df = load_manual_csv(temp_csv_file)
        records = parse_manual_records(df)

        assert len(records) == 2
        assert records[0].polymer_name == "Poly(ether sulfone) derivative"
        assert records[0].permeability_co2 == 12.5
        assert records[0].source_type == "manual_extraction"

    def test_extract_manual_literature_data(self, temp_input_dir):
        """Test end-to-end extraction from directory."""
        output_path = os.path.join(temp_input_dir, "output.csv")
        df = extract_manual_literature_data(temp_input_dir, output_path)

        assert len(df) == 2
        assert os.path.exists(output_path)
        assert 'smiles' in df.columns
        assert 'source_type' in df.columns

    def test_extract_manual_literature_data_no_files(self):
        """Test extraction from directory with no CSV files raises ConfigurationError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ConfigurationError):
                extract_manual_literature_data(temp_dir)

    def test_extract_manual_literature_data_no_directory(self):
        """Test extraction from non-existent directory raises ConfigurationError."""
        with pytest.raises(ConfigurationError):
            extract_manual_literature_data("non_existent_directory")

    def test_extract_manual_literature_data_partial_failure(self, sample_csv_content):
        """Test extraction continues when one file fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a valid file
            valid_path = os.path.join(temp_dir, "valid.csv")
            with open(valid_path, 'w') as f:
                f.write(sample_csv_content)

            # Create an invalid file (missing columns)
            invalid_path = os.path.join(temp_dir, "invalid.csv")
            with open(invalid_path, 'w') as f:
                f.write("smiles,polymer_name\n\"CC\",Test\n")

            output_path = os.path.join(temp_dir, "output.csv")
            df = extract_manual_literature_data(temp_dir, output_path)

            # Should have records from valid file only
            assert len(df) == 2
            assert os.path.exists(output_path)