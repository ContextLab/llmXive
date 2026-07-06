import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.analysis.descriptor_ranking import (
    load_feature_importance_results,
    select_top_descriptors_subset,
    save_descriptor_subset,
    run_descriptor_ranking,
)


class TestLoadFeatureImportanceResults:
    def test_load_valid_csv(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        data = {
            "descriptor": ["A", "B", "C"],
            "importance_score": [0.5, 0.3, 0.2],
            "variance_explained": [0.5, 0.3, 0.2]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        result = load_feature_importance_results(csv_path)
        
        assert len(result) == 3
        assert "descriptor" in result.columns
        assert "variance_explained" in result.columns
        assert "cumulative_variance" in result.columns

    def test_missing_columns(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        data = {"descriptor": ["A"]}
        pd.DataFrame(data).to_csv(csv_path, index=False)

        with pytest.raises(ValueError, match="missing required columns"):
            load_feature_importance_results(csv_path)

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_feature_importance_results(tmp_path / "nonexistent.csv")


class TestSelectTopDescriptorsSubset:
    def test_threshold_met(self):
        data = {
            "descriptor": ["A", "B", "C", "D"],
            "importance_score": [0.4, 0.3, 0.2, 0.1],
            "variance_explained": [0.4, 0.3, 0.2, 0.1],
            "cumulative_variance": [0.4, 0.7, 0.9, 1.0]
        }
        df = pd.DataFrame(data)

        # Threshold 0.60 should select A and B (cumulative 0.7)
        descriptors, scores, cum_var = select_top_descriptors_subset(df, threshold=0.60)

        assert descriptors == ["A", "B"]
        assert scores == [0.4, 0.3]
        assert abs(cum_var - 0.7) < 1e-6

    def test_threshold_not_met_take_all(self):
        data = {
            "descriptor": ["A", "B"],
            "importance_score": [0.3, 0.2],
            "variance_explained": [0.3, 0.2],
            "cumulative_variance": [0.3, 0.5]
        }
        df = pd.DataFrame(data)

        # Threshold 0.60 is not met even with all, should take all
        descriptors, scores, cum_var = select_top_descriptors_subset(df, threshold=0.60)

        assert descriptors == ["A", "B"]
        assert cum_var == 0.5

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["descriptor", "importance_score", "variance_explained"])
        
        with pytest.raises(ValueError, match="empty"):
            select_top_descriptors_subset(df)

    def test_unsorted_input(self):
        # Input is not sorted by importance
        data = {
            "descriptor": ["C", "A", "B"],
            "importance_score": [0.2, 0.4, 0.3],
            "variance_explained": [0.2, 0.4, 0.3],
            "cumulative_variance": [0.2, 0.6, 0.9] # This is wrong for unsorted, func should re-sort
        }
        df = pd.DataFrame(data)

        # Function should sort by importance_score desc first
        descriptors, scores, cum_var = select_top_descriptors_subset(df, threshold=0.50)

        # Expected order: A (0.4), B (0.3) -> Cumulative 0.7 >= 0.5
        assert descriptors == ["A", "B"]
        assert scores == [0.4, 0.3]


class TestSaveDescriptorSubset:
    def test_save_correct_format(self, tmp_path):
        output_path = tmp_path / "result.json"
        descriptors = ["feat1", "feat2"]
        scores = [0.5, 0.2]
        cum_var = 0.7
        threshold = 0.60

        save_descriptor_subset(descriptors, scores, cum_var, threshold, output_path)

        assert output_path.exists()
        
        with open(output_path) as f:
            data = json.load(f)

        assert data["threshold"] == 0.60
        assert data["cumulative_variance_achieved"] == 0.7
        assert data["num_descriptors_selected"] == 2
        assert len(data["selected_descriptors"]) == 2
        assert data["selected_descriptors"][0]["name"] == "feat1"
        assert data["selected_descriptors"][0]["variance_explained"] == 0.5


class TestRunDescriptorRanking:
    def test_end_to_end(self, tmp_path):
        # Create input CSV
        input_path = tmp_path / "feature_importance.csv"
        data = {
            "descriptor": ["D1", "D2", "D3", "D4"],
            "importance_score": [0.5, 0.2, 0.15, 0.15],
            "variance_explained": [0.5, 0.2, 0.15, 0.15]
        }
        pd.DataFrame(data).to_csv(input_path, index=False)

        output_path = tmp_path / "subset.json"

        result = run_descriptor_ranking(input_path, output_path, threshold=0.65)

        assert result["selected_count"] == 2 # D1 (0.5) + D2 (0.2) = 0.7 >= 0.65
        assert result["cumulative_variance"] == 0.7
        
        assert output_path.exists()
        with open(output_path) as f:
            saved_data = json.load(f)
        
        assert saved_data["num_descriptors_selected"] == 2
        assert saved_data["selected_descriptors"][0]["name"] == "D1"
        assert saved_data["selected_descriptors"][1]["name"] == "D2"