import sys
import pytest
import pandas as pd
from pathlib import Path

# Ensure src is in path for imports if running from tests dir
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.model import validate_strains, load_and_validate_aggregated_dataset
from src.config import DATA_PROCESSED_PATH


class TestValidateStrains:
    def test_passes_with_5_strains(self, caplog):
        """Test that validation passes with exactly 5 unique strains."""
        data = {
            "strain_accession": ["A", "B", "C", "D", "E"],
            "isg_score": [1.0, 2.0, 3.0, 4.0, 5.0],
            "feature1": [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        df = pd.DataFrame(data)

        # Should not raise SystemExit
        result = validate_strains(df)
        assert result is None
        assert "Validation passed" in caplog.text

    def test_passes_with_more_than_5_strains(self, caplog):
        """Test that validation passes with > 5 unique strains."""
        data = {
            "strain_accession": ["A", "B", "C", "D", "E", "F", "G"],
            "isg_score": [1.0] * 7,
            "feature1": [0.1] * 7
        }
        df = pd.DataFrame(data)

        result = validate_strains(df)
        assert result is None

    def test_aborts_with_less_than_5_strains(self, caplog):
        """Test that validation aborts with < 5 unique strains."""
        data = {
            "strain_accession": ["A", "B", "C", "D"],
            "isg_score": [1.0, 2.0, 3.0, 4.0],
            "feature1": [0.1, 0.2, 0.3, 0.4]
        }
        df = pd.DataFrame(data)

        with pytest.raises(SystemExit) as exc_info:
            validate_strains(df)

        assert exc_info.value.code == 1
        assert "ABORT" in caplog.text
        assert "Insufficient strain diversity" in caplog.text

    def test_aborts_if_column_missing(self, caplog):
        """Test that validation aborts if 'strain_accession' column is missing."""
        data = {
            "other_col": ["A", "B", "C"],
            "isg_score": [1.0, 2.0, 3.0]
        }
        df = pd.DataFrame(data)

        with pytest.raises(SystemExit) as exc_info:
            validate_strains(df)

        assert exc_info.value.code == 1
        assert "Missing required column" in caplog.text

class TestLoadAndValidateAggregatedDataset:
    def test_loads_and_validates_existing_file(self, tmp_path, monkeypatch):
        """Test loading a valid file from a temporary directory."""
        # Create a valid CSV
        csv_path = tmp_path / "aggregated_dataset.csv"
        data = {
            "strain_accession": ["A", "B", "C", "D", "E"],
            "isg_score": [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        # Monkeypatch the default path logic if necessary, but here we pass explicit path
        # The function defaults to DATA_PROCESSED_PATH, so we test with explicit path
        df = load_and_validate_aggregated_dataset(file_path=csv_path)

        assert len(df) == 5
        assert df["strain_accession"].nunique() == 5

    def test_aborts_if_file_not_found(self, caplog):
        """Test that the function aborts if the file does not exist."""
        fake_path = Path("/nonexistent/path/aggregated_dataset.csv")

        with pytest.raises(SystemExit) as exc_info:
            load_and_validate_aggregated_dataset(file_path=fake_path)

        assert exc_info.value.code == 1
        assert "File not found" in caplog.text

    def test_aborts_if_file_has_insufficient_strains(self, tmp_path, caplog):
        """Test that the function aborts if the loaded file has < 5 strains."""
        csv_path = tmp_path / "aggregated_dataset.csv"
        data = {
            "strain_accession": ["A", "B"],
            "isg_score": [1.0, 2.0]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        with pytest.raises(SystemExit) as exc_info:
            load_and_validate_aggregated_dataset(file_path=csv_path)

        assert exc_info.value.code == 1
        assert "Insufficient strain diversity" in caplog.text
