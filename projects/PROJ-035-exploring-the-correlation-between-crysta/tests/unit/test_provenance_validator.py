import pytest
import pandas as pd
import tempfile
from pathlib import Path
import json
import sys
import os

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cleaning.provenance_validator import (
    is_valid_source_reference,
    validate_provenance,
    filter_valid_provenance,
    save_validation_report,
    main
)

class TestIsValidSourceReference:
    def test_valid_doi(self):
        assert is_valid_source_reference("10.1038/s41586-021-03819-2")[0] is True
        assert is_valid_source_reference("DOI: 10.1103/PhysRevLett.123.012345")[0] is True

    def test_valid_pmid(self):
        # Pattern: 10.\d{4}/\d+
        assert is_valid_source_reference("10.1234/56789")[0] is True
        assert is_valid_source_reference("PMID: 10.0000/123456")[0] is True

    def test_valid_nist(self):
        assert is_valid_source_reference("NIST-ABC123")[0] is True
        assert is_valid_source_reference("Reference: NIST-X9Y8Z")[0] is True

    def test_invalid_reference(self):
        assert is_valid_source_reference("Some random text")[0] is False
        assert is_valid_source_reference("")[0] is False
        assert is_valid_source_reference(None)[0] is False
        assert is_valid_source_reference("10.123/invalid-format-no-slash")[0] is False # DOI needs slash usually, but regex is 10.xxxx/...

    def test_missing_reference(self):
        assert is_valid_source_reference("")[0] is False
        assert is_valid_source_reference("   ")[0] is False

class TestValidateProvenance:
    def test_validate_mixed_data(self):
        data = {
            "id": [1, 2, 3, 4],
            "source_reference": [
                "10.1038/nature12345",
                "NIST-TEST001",
                "Invalid Reference",
                None
            ]
        }
        df = pd.DataFrame(data)
        results = validate_provenance(df, "source_reference")
        
        assert results["total_count"] == 4
        assert results["valid_count"] == 2
        assert results["invalid_count"] == 2
        assert len(results["failed_indices"]) == 2
        assert 2 in results["failed_indices"]
        assert 3 in results["failed_indices"]

    def test_validate_all_valid(self):
        data = {
            "id": [1, 2],
            "source_reference": ["10.1000/1234", "NIST-VALID"]
        }
        df = pd.DataFrame(data)
        results = validate_provenance(df, "source_reference")
        
        assert results["valid_count"] == 2
        assert results["invalid_count"] == 0

    def test_validate_missing_column(self):
        df = pd.DataFrame({"id": [1]})
        with pytest.raises(ValueError):
            validate_provenance(df, "non_existent_column")

class TestFilterValidProvenance:
    def test_filter_mixed(self):
        data = {
            "id": [1, 2, 3],
            "source_reference": ["10.1000/123", "Bad", "NIST-OK"]
        }
        df = pd.DataFrame(data)
        filtered = filter_valid_provenance(df, "source_reference")
        
        assert len(filtered) == 2
        assert list(filtered["id"]) == [1, 3]

    def test_filter_all_invalid(self):
        data = {
            "id": [1, 2],
            "source_reference": ["Bad", "Worse"]
        }
        df = pd.DataFrame(data)
        filtered = filter_valid_provenance(df, "source_reference")
        
        assert len(filtered) == 0

class TestSaveValidationReport:
    def test_save_report(self):
        results = {
            "total_count": 10,
            "valid_count": 5,
            "invalid_count": 5,
            "failed_indices": [1, 3],
            "failed_reasons": ["Missing", "Invalid"]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            save_validation_report(results, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded["total_count"] == 10
            assert loaded["invalid_count"] == 5

class TestMain:
    def test_main_missing_input(self, capsys):
        # Create a temp dir that doesn't have the expected file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to tmpdir to simulate missing file
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                # Ensure data/raw doesn't exist
                (Path(tmpdir) / "data").mkdir()
                # Run main
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
            finally:
                os.chdir(old_cwd)

    def test_main_success_with_mock_file(self, tmp_path):
        # Create a mock input file
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        input_file = data_dir / "thermal_raw.csv"
        input_file.write_text("structure_id,thermal_conductivity,source_reference\n1,10.5,10.1000/123\n2,12.0,NIST-TEST")
        
        # Run main in the temp directory
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            main()
            # Check output
            report_path = tmp_path / "data" / "cleaned" / "provenance_report.json"
            assert report_path.exists()
            with open(report_path, 'r') as f:
                report = json.load(f)
            assert report["valid_count"] == 2
            assert report["invalid_count"] == 0
        finally:
            os.chdir(old_cwd)