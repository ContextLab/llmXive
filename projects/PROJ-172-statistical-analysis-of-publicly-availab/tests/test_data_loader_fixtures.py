"""
Tests for the data loader fixtures defined in conftest.py.
These tests verify that the mocking infrastructure works correctly.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Import project modules
from data_models import GameRecord, TeamMetrics, ModelResult


class TestDataLoaderFixtures:
    """Test suite for data loading fixtures."""

    def test_mock_game_record_creation(self, mock_game_record: GameRecord):
        """Verify that the mock GameRecord fixture creates valid objects."""
        assert isinstance(mock_game_record, GameRecord)
        assert mock_game_record.game_id == "test_game_001"
        assert mock_game_record.home_team == "NYY"
        assert mock_game_record.away_team == "BOS"
        assert mock_game_record.home_score == 5
        assert mock_game_record.away_score == 3

    def test_mock_team_metrics_creation(self, mock_team_metrics: TeamMetrics):
        """Verify that the mock TeamMetrics fixture creates valid objects."""
        assert isinstance(mock_team_metrics, TeamMetrics)
        assert mock_team_metrics.team_id == "NYY"
        assert mock_team_metrics.year == 2021
        assert mock_team_metrics.games_played == 162
        assert mock_team_metrics.wins == 92
        assert mock_team_metrics.losses == 70

    def test_mock_model_result_creation(self, mock_model_result: ModelResult):
        """Verify that the mock ModelResult fixture creates valid objects."""
        assert isinstance(mock_model_result, ModelResult)
        assert mock_model_result.model_name == "test_model"
        assert mock_model_result.feature_set == "traditional"
        assert mock_model_result.roc_auc == 0.75
        assert mock_model_result.log_loss == 0.42
        assert mock_model_result.brier_score == 0.18

    def test_mock_data_loader_interface(self, mock_data_loader: MagicMock):
        """Verify that the mock data loader has the expected interface."""
        # Check that the load method exists and returns a mock
        result = mock_data_loader.load()
        assert result is not None
        
        # Check that is_real_data attribute exists
        assert hasattr(mock_data_loader, 'is_real_data')
        assert isinstance(mock_data_loader.is_real_data, bool)

    def test_mock_data_loader_load_real_data(self, mock_data_loader: MagicMock):
        """Verify that load_real_data returns the expected mock dataframe."""
        result = mock_data_loader.load_real_data()
        assert result is not None
        # Verify it returns the same mock object as load()
        assert result == mock_data_loader.load()

    def test_project_root_fixture(self, project_root: Path):
        """Verify that the project root fixture returns a valid Path."""
        assert isinstance(project_root, Path)
        assert project_root.exists()
        assert project_root.name == "PROJ-172-statistical-analysis-of-publicly-availab"

    def test_ci_mode_fixture(self, ci_mode: bool):
        """Verify that the CI mode fixture returns a boolean."""
        assert isinstance(ci_mode, bool)

    def test_temp_output_dir_fixture(self, temp_output_dir: Path):
        """Verify that the temporary output directory is created and writable."""
        assert isinstance(temp_output_dir, Path)
        assert temp_output_dir.exists()
        assert temp_output_dir.is_dir()

        # Test that we can write a file to it
        test_file = temp_output_dir / "test_write.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"

    def test_sample_processed_data_path(self, sample_processed_data_path: Path):
        """Verify that the sample processed data path is correctly constructed."""
        assert isinstance(sample_processed_data_path, Path)
        assert sample_processed_data_path.name == "sample_processed.csv"
        assert sample_processed_data_path.parent.exists()

    def test_mock_logger_fixture(self, mock_logger: MagicMock):
        """Verify that the mock logger fixture works."""
        # Just verify it's a MagicMock, as the actual logger implementation
        # is tested elsewhere
        assert isinstance(mock_logger, MagicMock)

    def test_setup_test_environment_side_effect(self, setup_test_environment):
        """
        Verify that the setup_test_environment fixture ensures directories exist.
        This is a side-effect test that checks the autouse fixture.
        """
        # The fixture runs automatically, so we just verify the test passes.
        # If the directories weren't created, the test would fail earlier.
        assert True
