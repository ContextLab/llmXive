import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Add code/ to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in os.sys.path:
    os.sys.path.insert(0, str(code_dir))

from merge_datasets import merge_perovskite_datasets


class TestMergeDatasets:
    """Tests for the dataset merging logic (T012c)."""

    def test_merge_basic(self, tmp_path):
        """Test basic merge of two non-overlapping datasets."""
        # Create mock NREL data
        nrel_data = pd.DataFrame({
            "formula": ["ABX3", "ABY3"],
            "T_d": [500, 600],
            "source": ["NREL", "NREL"]
        })
        nrel_path = tmp_path / "nrel_perovskites.csv"
        nrel_data.to_csv(nrel_path, index=False)

        # Create mock MP data
        mp_data = pd.DataFrame({
            "formula": ["ABZ3", "ABW3"],
            "T_d": [700, 800],
            "source": ["MaterialsProject", "MaterialsProject"]
        })
        mp_path = tmp_path / "mp_perovskites.csv"
        mp_data.to_csv(mp_path, index=False)

        output_path = tmp_path / "perovskites_merged.csv"

        df_merged, dropped_count = merge_perovskite_datasets(nrel_path, mp_path, output_path)

        assert len(df_merged) == 4
        assert dropped_count == 0
        assert "formula" in df_merged.columns
        assert "T_d" in df_merged.columns
        assert "source" in df_merged.columns
        assert output_path.exists()

    def test_merge_duplicates_removed(self, tmp_path):
        """Test that duplicates based on formula and source are removed."""
        # Create NREL data with a duplicate row
        nrel_data = pd.DataFrame({
            "formula": ["ABX3", "ABX3", "ABY3"],
            "T_d": [500, 500, 600],
            "source": ["NREL", "NREL", "NREL"]
        })
        nrel_path = tmp_path / "nrel_perovskites.csv"
        nrel_data.to_csv(nrel_path, index=False)

        # Create MP data
        mp_data = pd.DataFrame({
            "formula": ["ABZ3"],
            "T_d": [700],
            "source": ["MaterialsProject"]
        })
        mp_path = tmp_path / "mp_perovskites.csv"
        mp_data.to_csv(mp_path, index=False)

        output_path = tmp_path / "perovskites_merged.csv"

        df_merged, dropped_count = merge_perovskite_datasets(nrel_path, mp_path, output_path)

        # Initial combined: 3 (NREL) + 1 (MP) = 4
        # Duplicates: 1 (the second ABX3/NREL row)
        # Expected final: 3
        assert len(df_merged) == 3
        assert dropped_count == 1
        # Verify unique formulas per source
        assert len(df_merged[(df_merged["formula"] == "ABX3") & (df_merged["source"] == "NREL")]) == 1

    def test_missing_source_column_added(self, tmp_path):
        """Test that missing 'source' columns are added automatically."""
        # NREL without source column
        nrel_data = pd.DataFrame({
            "formula": ["ABX3"],
            "T_d": [500]
        })
        nrel_path = tmp_path / "nrel_perovskites.csv"
        nrel_data.to_csv(nrel_path, index=False)

        # MP without source column
        mp_data = pd.DataFrame({
            "formula": ["ABZ3"],
            "T_d": [700]
        })
        mp_path = tmp_path / "mp_perovskites.csv"
        mp_data.to_csv(mp_path, index=False)

        output_path = tmp_path / "perovskites_merged.csv"

        df_merged, _ = merge_perovskite_datasets(nrel_path, mp_path, output_path)

        assert "source" in df_merged.columns
        assert set(df_merged["source"].unique()) == {"NREL", "MaterialsProject"}

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised if source file is missing."""
        non_existent = tmp_path / "missing.csv"
        output_path = tmp_path / "out.csv"

        with pytest.raises(FileNotFoundError):
            merge_perovskite_datasets(non_existent, non_existent, output_path)

    def test_empty_file_error(self, tmp_path):
        """Test that ValueError is raised if source file is empty."""
        nrel_path = tmp_path / "nrel.csv"
        nrel_path.touch() # Create empty file

        mp_data = pd.DataFrame({"formula": ["ABX3"], "T_d": [500], "source": ["MP"]})
        mp_path = tmp_path / "mp.csv"
        mp_path = tmp_path / "mp.csv"
        mp_data.to_csv(mp_path, index=False)

        output_path = tmp_path / "out.csv"

        with pytest.raises(ValueError, match="Source file is empty"):
            merge_perovskite_datasets(nrel_path, mp_path, output_path)