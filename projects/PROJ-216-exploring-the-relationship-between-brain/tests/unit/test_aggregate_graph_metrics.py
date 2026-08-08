import os
import sys
import csv
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.aggregate_graph_metrics import (
    load_preprocessed_subjects,
    aggregate_metrics_to_csv,
    main,
)


class TestLoadPreprocessedSubjects:
    def test_load_preprocessed_subjects_found(self, tmp_path):
        # Create mock directory structure
        sub_dir = tmp_path / "sub-01"
        sub_dir.mkdir()
        nifti = sub_dir / "preprocessed.nii.gz"
        nifti.touch()

        subjects = load_preprocessed_subjects(tmp_path, ["sub-01"])
        assert len(subjects) == 1
        assert subjects[0]["subject_id"] == "sub-01"
        assert subjects[0]["nifti_path"] == str(nifti)

    def test_load_preprocessed_subjects_missing(self, tmp_path, capsys):
        # Create directory but no file
        sub_dir = tmp_path / "sub-02"
        sub_dir.mkdir()

        subjects = load_preprocessed_subjects(tmp_path, ["sub-02"])
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert len(subjects) == 0


class TestAggregateMetricsToCsv:
    def test_aggregate_metrics_to_csv(self, tmp_path):
        # Mock subjects
        subjects = [
            {"subject_id": "sub-01", "nifti_path": str(tmp_path / "fake.nii.gz")}
        ]

        # Mock compute_graph_metrics
        with patch("code.aggregate_graph_metrics.compute_graph_metrics") as mock_compute:
            mock_compute.return_value = {
                "global_efficiency": 0.5,
                "clustering_coefficient": 0.3,
                "modularity": 0.4,
            }

            output_path = tmp_path / "output.csv"
            aggregate_metrics_to_csv(subjects, output_path)

            assert output_path.exists()

            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 3
            assert rows[0]["subject_id"] == "sub-01"
            assert rows[0]["metric_name"] == "global_efficiency"
            assert rows[0]["value"] == "0.5"


class TestMain:
    @patch("code.aggregate_graph_metrics.load_preprocessed_subjects")
    @patch("code.aggregate_graph_metrics.aggregate_metrics_to_csv")
    @patch("code.aggregate_graph_metrics.get_sample_limit")
    def test_main_success(
        self, mock_get_limit, mock_agg, mock_load, tmp_path, monkeypatch
    ):
        # Setup mocks
        mock_get_limit.return_value = {"n": 10}
        mock_load.return_value = [{"subject_id": "sub-01", "nifti_path": "fake.nii"}]

        # Change to tmp_dir for file writing
        monkeypatch.chdir(tmp_path)

        # Create necessary dirs
        (tmp_path / "data" / "processed").mkdir(parents=True)

        # Run main
        main()

        mock_load.assert_called_once()
        mock_agg.assert_called_once()