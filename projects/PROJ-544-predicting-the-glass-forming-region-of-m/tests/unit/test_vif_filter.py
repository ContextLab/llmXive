"""
Unit tests for code/descriptors/vif_filter.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Import the module functions
from code.descriptors.vif_filter import (
    load_vif_report,
    load_descriptors,
    filter_descriptors_by_vif,
    check_pca_trigger,
    perform_pca_reduction,
    VIF_THRESHOLD_REMOVAL,
    VIF_THRESHOLD_PCA_TRIGGER
)


class TestLoadVifReport:
    def test_load_valid_report(self, tmp_path):
        vif_data = {"atomic_size_mismatch": 2.5, "mixing_enthalpy": 5.0}
        report_path = tmp_path / "vif_report.json"
        with open(report_path, 'w') as f:
            json.dump(vif_data, f)

        result = load_vif_report(report_path)
        assert result == vif_data

    def test_load_nested_report(self, tmp_path):
        vif_data = {"vif_scores": {"atomic_size_mismatch": 2.5}}
        report_path = tmp_path / "vif_report.json"
        with open(report_path, 'w') as f:
            json.dump(vif_data, f)

        result = load_vif_report(report_path)
        assert result == {"atomic_size_mismatch": 2.5}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_vif_report(tmp_path / "nonexistent.json")


class TestLoadDescriptors:
    def test_load_valid_csv(self, tmp_path):
        df = pd.DataFrame({"id": [1, 2], "desc1": [1.0, 2.0]})
        csv_path = tmp_path / "desc.csv"
        df.to_csv(csv_path, index=False)

        result = load_descriptors(csv_path)
        assert result.equals(df)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_descriptors(tmp_path / "nonexistent.csv")


class TestFilterDescriptorsByVif:
    def test_filter_removes_high_vif(self):
        df = pd.DataFrame({
            "id": [1, 2],
            "desc1": [1.0, 2.0],
            "desc2": [3.0, 4.0]
        })
        vif_scores = {"desc1": 2.0, "desc2": 40.0} # desc2 > 33

        filtered_df, kept, removed = filter_descriptors_by_vif(
            df, vif_scores, VIF_THRESHOLD_REMOVAL
        )

        assert "desc1" in kept
        assert "desc2" in removed
        assert "desc2" not in filtered_df.columns
        assert "desc1" in filtered_df.columns
        assert "id" in filtered_df.columns

    def test_all_kept(self):
        df = pd.DataFrame({
            "id": [1],
            "desc1": [1.0]
        })
        vif_scores = {"desc1": 10.0} # < 33

        filtered_df, kept, removed = filter_descriptors_by_vif(
            df, vif_scores, VIF_THRESHOLD_REMOVAL
        )

        assert len(removed) == 0
        assert "desc1" in kept
        assert filtered_df.shape == df.shape


class TestCheckPcaTrigger:
    def test_all_above_threshold(self):
        scores = {"a": 6.0, "b": 10.0, "c": 5.1}
        assert check_pca_trigger(scores, VIF_THRESHOLD_PCA_TRIGGER) is True

    def test_one_below_threshold(self):
        scores = {"a": 6.0, "b": 4.9} # 4.9 <= 5.0
        assert check_pca_trigger(scores, VIF_THRESHOLD_PCA_TRIGGER) is False

    def test_empty_scores(self):
        assert check_pca_trigger({}, VIF_THRESHOLD_PCA_TRIGGER) is False


class TestPerformPcaReduction:
    def test_pca_reduces_dimensions(self):
        # Create a dataset with 3 highly correlated columns (to ensure PCA works well)
        np.random.seed(42)
        base = np.random.rand(100, 1)
        data = np.hstack([base + np.random.normal(0, 0.1, (100, 1)) for _ in range(3)])
        
        df = pd.DataFrame(data, columns=["desc1", "desc2", "desc3"])
        df["id"] = range(100)

        result_df, metadata = perform_pca_reduction(
            df, ["desc1", "desc2", "desc3"], n_components=2
        )

        # Check columns
        assert "desc1" not in result_df.columns
        assert "desc2" not in result_df.columns
        assert "desc3" not in result_df.columns
        assert "pca_comp_1" in result_df.columns
        assert "pca_comp_2" in result_df.columns
        assert "id" in result_df.columns

        # Check metadata
        assert "total_explained_variance" in metadata
        assert metadata["n_components_retained"] == 2
        assert len(metadata["components_matrix"]) == 2 # 2 components

    def test_variance_target_met(self):
        # Create perfect correlation (100% variance in 1st component)
        np.random.seed(42)
        base = np.random.rand(50, 1)
        data = np.hstack([base, base, base])
        
        df = pd.DataFrame(data, columns=["d1", "d2", "d3"])
        
        _, metadata = perform_pca_reduction(df, ["d1", "d2", "d3"], n_components=2)
        
        assert metadata["total_explained_variance"] > 0.90