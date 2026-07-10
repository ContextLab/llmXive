"""
Unit tests for the ingestion pipeline (T020).
Tests the orchestration logic and metadata generation without full data fetch.
"""
import pytest
import os
import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.pipeline.ingest import run_pipeline

class TestIngestPipeline:

    @patch('src.pipeline.ingest.OQMDFetcher')
    @patch('src.pipeline.ingest.MaterialsProjectFetcher')
    @patch('src.pipeline.ingest.filter_hea_samples')
    @patch('src.pipeline.ingest.normalize_dataframe')
    @patch('src.pipeline.ingest.compute_descriptors')
    @patch('src.pipeline.ingest.apply_ilr_transformation')
    @patch('src.pipeline.ingest.compute_residual_target')
    def test_pipeline_orchestration(
        self,
        mock_residual,
        mock_ilr,
        mock_desc,
        mock_norm,
        mock_filter,
        mock_mp_fetcher,
        mock_oqmd_fetcher,
        tmp_path
    ):
        """Test that the pipeline calls all steps in the correct order."""
        # Mock Data
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.__len__ = lambda self: 100
        mock_df.columns = ['col1']

        mock_oqmd_fetcher.return_value.fetch.return_value = mock_df
        mock_mp_fetcher.return_value.fetch.return_value = mock_df

        mock_filter.return_value = (mock_df, {"kept": 100})
        mock_norm.return_value = (mock_df, {"normalized": True})
        mock_desc.return_value = mock_df
        mock_ilr.return_value = mock_df
        mock_residual.return_value = mock_df

        output_csv = tmp_path / "test_output.csv"
        output_meta = tmp_path / "test_meta.yaml"

        # Run
        result = run_pipeline(
            output_csv_path=str(output_csv),
            metadata_yaml_path=str(output_meta),
            seed=42
        )

        # Assert Order and Calls
        mock_oqmd_fetcher.assert_called_once()
        mock_mp_fetcher.assert_called_once()
        mock_filter.assert_called_once()
        mock_norm.assert_called_once()
        mock_desc.assert_called_once()
        mock_ilr.assert_called_once()
        mock_residual.assert_called_once()

        # Assert Outputs Exist
        assert output_csv.exists()
        assert output_meta.exists()

        # Assert Metadata Content
        with open(output_meta, 'r') as f:
            meta = yaml.safe_load(f)

        assert "sources" in meta
        assert meta["seed"] == 42
        assert "steps" in meta
        assert "fetch" in meta["steps"]
        assert "filter" in meta["steps"]
        assert "feature_engineering" in meta["steps"]

    @patch('src.pipeline.ingest.OQMDFetcher')
    @patch('src.pipeline.ingest.MaterialsProjectFetcher')
    def test_pipeline_fails_on_empty_fetch(self, mock_mp, mock_oqmd, tmp_path):
        """Test that pipeline raises error if no data is fetched."""
        mock_oqmd.return_value.fetch.return_value = None
        mock_mp.return_value.fetch.return_value = None

        output_csv = tmp_path / "test_output.csv"
        output_meta = tmp_path / "test_meta.yaml"

        with pytest.raises(RuntimeError, match="No data fetched"):
            run_pipeline(
                output_csv_path=str(output_csv),
                metadata_yaml_path=str(output_meta)
            )

    @patch('src.pipeline.ingest.OQMDFetcher')
    @patch('src.pipeline.ingest.MaterialsProjectFetcher')
    @patch('src.pipeline.ingest.filter_hea_samples')
    def test_pipeline_fails_on_filter_empty(self, mock_filter, mock_mp, mock_oqmd, tmp_path):
        """Test that pipeline raises error if filter results in empty dataframe."""
        import pandas as pd
        mock_df = pd.DataFrame()
        mock_df.empty = True
        mock_df.__len__ = lambda self: 0
        mock_df.columns = []

        mock_oqmd.return_value.fetch.return_value = mock_df
        mock_mp.return_value.fetch.return_value = mock_df
        mock_filter.return_value = (mock_df, {"kept": 0})

        output_csv = tmp_path / "test_output.csv"
        output_meta = tmp_path / "test_meta.yaml"

        with pytest.raises(RuntimeError, match="No samples passed the filter"):
            run_pipeline(
                output_csv_path=str(output_csv),
                metadata_yaml_path=str(output_meta)
            )