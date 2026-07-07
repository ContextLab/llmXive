"""
Unit tests for data models.

Tests cover validation, serialization, and utility methods for GameRecord,
TeamMetrics, and ModelResult classes.
"""
import pytest
from datetime import date
import json
import pandas as pd

from code.data_models import (
    GameRecord,
    TeamMetrics,
    ModelResult,
    create_data_models_dataframe,
    create_team_metrics_dataframe,
    create_model_results_dataframe
)


class TestGameRecord:
    """Tests for GameRecord dataclass."""
    
    def test_valid_game_record(self):
        """Test creation of a valid GameRecord."""
        record = GameRecord(
            game_id="2023-04-01-ATL-NYM",
            date=date(2023, 4, 1),
            home_team="NYM",
            away_team="ATL",
            home_score=5,
            away_score=3,
            home_wins=1,
            away_wins=1,
            home_losses=0,
            away_losses=0,
            park_factor=1.02
        )
        
        assert record.game_id == "2023-04-01-ATL-NYM"
        assert record.home_score == 5
        assert record.away_score == 3
        assert record.is_real_data is True
        
    def test_game_record_empty_game_id(self):
        """Test that empty game_id raises ValueError."""
        with pytest.raises(ValueError, match="game_id cannot be empty"):
            GameRecord(
                game_id="",
                date=date(2023, 4, 1),
                home_team="NYM",
                away_team="ATL",
                home_score=5,
                away_score=3,
                home_wins=1,
                away_wins=1,
                home_losses=0,
                away_losses=0
            )
            
    def test_game_record_negative_score(self):
        """Test that negative score raises ValueError."""
        with pytest.raises(ValueError, match="Scores cannot be negative"):
            GameRecord(
                game_id="2023-04-01-ATL-NYM",
                date=date(2023, 4, 1),
                home_team="NYM",
                away_team="ATL",
                home_score=-1,
                away_score=3,
                home_wins=1,
                away_wins=1,
                home_losses=0,
                away_losses=0
            )
            
    def test_game_record_invalid_park_factor(self):
        """Test that invalid park factor raises ValueError."""
        with pytest.raises(ValueError, match="Park factor must be positive"):
            GameRecord(
                game_id="2023-04-01-ATL-NYM",
                date=date(2023, 4, 1),
                home_team="NYM",
                away_team="ATL",
                home_score=5,
                away_score=3,
                home_wins=1,
                away_wins=1,
                home_losses=0,
                away_losses=0,
                park_factor=0.0
            )
            
    def test_to_dict(self):
        """Test conversion to dictionary."""
        record = GameRecord(
            game_id="2023-04-01-ATL-NYM",
            date=date(2023, 4, 1),
            home_team="NYM",
            away_team="ATL",
            home_score=5,
            away_score=3,
            home_wins=1,
            away_wins=1,
            home_losses=0,
            away_losses=0
        )
        
        data = record.to_dict()
        assert isinstance(data, dict)
        assert data['game_id'] == "2023-04-01-ATL-NYM"
        assert isinstance(data['date'], str)  # Date should be serialized
        assert data['date'] == "2023-04-01"
        
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'game_id': '2023-04-01-ATL-NYM',
            'date': '2023-04-01',
            'home_team': 'NYM',
            'away_team': 'ATL',
            'home_score': 5,
            'away_score': 3,
            'home_wins': 1,
            'away_wins': 1,
            'home_losses': 0,
            'away_losses': 0
        }
        
        record = GameRecord.from_dict(data)
        assert record.game_id == "2023-04-01-ATL-NYM"
        assert isinstance(record.date, date)
        assert record.date == date(2023, 4, 1)
        
    def test_to_dataframe_row(self):
        """Test conversion to DataFrame row."""
        record = GameRecord(
            game_id="2023-04-01-ATL-NYM",
            date=date(2023, 4, 1),
            home_team="NYM",
            away_team="ATL",
            home_score=5,
            away_score=3,
            home_wins=1,
            away_wins=1,
            home_losses=0,
            away_losses=0
        )
        
        row = record.to_dataframe_row()
        assert isinstance(row, dict)
        assert 'game_id' in row
        assert row['home_score'] == 5


class TestTeamMetrics:
    """Tests for TeamMetrics dataclass."""
    
    def test_valid_team_metrics(self):
        """Test creation of valid TeamMetrics."""
        metrics = TeamMetrics(
            team_id="NYY",
            season=2023,
            games_played=162,
            wins=100,
            losses=62,
            batting_average=0.265,
            era=3.45,
            woba=0.325,
            babip=0.295,
            runs_scored=815,
            runs_allowed=650,
            home_runs=210,
            strikeouts=1350,
            walks=520
        )
        
        assert metrics.team_id == "NYY"
        assert metrics.win_percentage() == pytest.approx(100/162)
        assert metrics.run_differential() == 165
        
    def test_team_metrics_invalid_games_played(self):
        """Test that invalid games_played raises ValueError."""
        with pytest.raises(ValueError, match="games_played must be positive"):
            TeamMetrics(
                team_id="NYY",
                season=2023,
                games_played=0,
                wins=0,
                losses=0,
                batting_average=0.265,
                era=3.45,
                woba=0.325,
                babip=0.295,
                runs_scored=0,
                runs_allowed=0,
                home_runs=0,
                strikeouts=0,
                walks=0
            )
            
    def test_team_metrics_negative_wins(self):
        """Test that negative wins raises ValueError."""
        with pytest.raises(ValueError, match="Wins and losses cannot be negative"):
            TeamMetrics(
                team_id="NYY",
                season=2023,
                games_played=162,
                wins=-1,
                losses=62,
                batting_average=0.265,
                era=3.45,
                woba=0.325,
                babip=0.295,
                runs_scored=815,
                runs_allowed=650,
                home_runs=210,
                strikeouts=1350,
                walks=520
            )
            
    def test_team_metrics_invalid_batting_average(self):
        """Test that invalid batting average raises ValueError."""
        with pytest.raises(ValueError, match="Batting average must be between 0 and 1"):
            TeamMetrics(
                team_id="NYY",
                season=2023,
                games_played=162,
                wins=100,
                losses=62,
                batting_average=1.5,
                era=3.45,
                woba=0.325,
                babip=0.295,
                runs_scored=815,
                runs_allowed=650,
                home_runs=210,
                strikeouts=1350,
                walks=520
            )
            
    def test_win_percentage(self):
        """Test win percentage calculation."""
        metrics = TeamMetrics(
            team_id="NYY",
            season=2023,
            games_played=162,
            wins=100,
            losses=62,
            batting_average=0.265,
            era=3.45,
            woba=0.325,
            babip=0.295,
            runs_scored=815,
            runs_allowed=650,
            home_runs=210,
            strikeouts=1350,
            walks=520
        )
        
        assert metrics.win_percentage() == pytest.approx(100/162)
        
    def test_run_differential(self):
        """Test run differential calculation."""
        metrics = TeamMetrics(
            team_id="NYY",
            season=2023,
            games_played=162,
            wins=100,
            losses=62,
            batting_average=0.265,
            era=3.45,
            woba=0.325,
            babip=0.295,
            runs_scored=815,
            runs_allowed=650,
            home_runs=210,
            strikeouts=1350,
            walks=520
        )
        
        assert metrics.run_differential() == 165
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = TeamMetrics(
            team_id="NYY",
            season=2023,
            games_played=162,
            wins=100,
            losses=62,
            batting_average=0.265,
            era=3.45,
            woba=0.325,
            babip=0.295,
            runs_scored=815,
            runs_allowed=650,
            home_runs=210,
            strikeouts=1350,
            walks=520
        )
        
        data = metrics.to_dict()
        assert isinstance(data, dict)
        assert data['team_id'] == "NYY"
        assert data['season'] == 2023
        
    def test_to_dataframe_row(self):
        """Test conversion to DataFrame row."""
        metrics = TeamMetrics(
            team_id="NYY",
            season=2023,
            games_played=162,
            wins=100,
            losses=62,
            batting_average=0.265,
            era=3.45,
            woba=0.325,
            babip=0.295,
            runs_scored=815,
            runs_allowed=650,
            home_runs=210,
            strikeouts=1350,
            walks=520
        )
        
        row = metrics.to_dataframe_row()
        assert isinstance(row, dict)
        assert 'win_pct' in row
        assert 'run_diff' in row
        assert row['win_pct'] == pytest.approx(100/162)
        assert row['run_diff'] == 165


class TestModelResult:
    """Tests for ModelResult dataclass."""
    
    def test_valid_model_result(self):
        """Test creation of valid ModelResult."""
        result = ModelResult(
            model_id="model-001",
            model_name="LogisticRegression",
            feature_set="traditional",
            train_roc_auc=0.85,
            test_roc_auc=0.82,
            train_log_loss=0.35,
            test_log_loss=0.38,
            train_brier=0.18,
            test_brier=0.20,
            hyperparameters={"C": 1.0, "penalty": "l2"},
            cv_scores=[0.84, 0.83, 0.85, 0.82, 0.84]
        )
        
        assert result.model_id == "model-001"
        assert result.generalization_gap() == pytest.approx(0.03)
        assert result.is_overfitting() is False
        
    def test_model_result_empty_model_id(self):
        """Test that empty model_id raises ValueError."""
        with pytest.raises(ValueError, match="model_id cannot be empty"):
            ModelResult(
                model_id="",
                model_name="LogisticRegression",
                feature_set="traditional",
                train_roc_auc=0.85,
                test_roc_auc=0.82,
                train_log_loss=0.35,
                test_log_loss=0.38,
                train_brier=0.18,
                test_brier=0.20
            )
            
    def test_model_result_invalid_roc_auc(self):
        """Test that invalid ROC-AUC raises ValueError."""
        with pytest.raises(ValueError, match="ROC-AUC must be between 0 and 1"):
            ModelResult(
                model_id="model-001",
                model_name="LogisticRegression",
                feature_set="traditional",
                train_roc_auc=1.5,
                test_roc_auc=0.82,
                train_log_loss=0.35,
                test_log_loss=0.38,
                train_brier=0.18,
                test_brier=0.20
            )
            
    def test_model_result_negative_log_loss(self):
        """Test that negative log-loss raises ValueError."""
        with pytest.raises(ValueError, match="Log-loss and Brier scores cannot be negative"):
            ModelResult(
                model_id="model-001",
                model_name="LogisticRegression",
                feature_set="traditional",
                train_roc_auc=0.85,
                test_roc_auc=0.82,
                train_log_loss=-0.1,
                test_log_loss=0.38,
                train_brier=0.18,
                test_brier=0.20
            )
            
    def test_generalization_gap(self):
        """Test generalization gap calculation."""
        result = ModelResult(
            model_id="model-001",
            model_name="LogisticRegression",
            feature_set="traditional",
            train_roc_auc=0.90,
            test_roc_auc=0.82,
            train_log_loss=0.35,
            test_log_loss=0.38,
            train_brier=0.18,
            test_brier=0.20
        )
        
        assert result.generalization_gap() == pytest.approx(0.08)
        
    def test_is_overfitting_true(self):
        """Test overfitting detection when gap is large."""
        result = ModelResult(
            model_id="model-001",
            model_name="LogisticRegression",
            feature_set="traditional",
            train_roc_auc=0.95,
            test_roc_auc=0.82,
            train_log_loss=0.35,
            test_log_loss=0.38,
            train_brier=0.18,
            test_brier=0.20
        )
        
        assert result.is_overfitting() is True
        
    def test_is_overfitting_false(self):
        """Test overfitting detection when gap is small."""
        result = ModelResult(
            model_id="model-001",
            model_name="LogisticRegression",
            feature_set="traditional",
            train_roc_auc=0.85,
            test_roc_auc=0.82,
            train_log_loss=0.35,
            test_log_loss=0.38,
            train_brier=0.18,
            test_brier=0.20
        )
        
        assert result.is_overfitting() is False
        
    def test_to_json(self):
        """Test conversion to JSON string."""
        result = ModelResult(
            model_id="model-001",
            model_name="LogisticRegression",
            feature_set="traditional",
            train_roc_auc=0.85,
            test_roc_auc=0.82,
            train_log_loss=0.35,
            test_log_loss=0.38,
            train_brier=0.18,
            test_brier=0.20
        )
        
        json_str = result.to_json()
        assert isinstance(json_str, str)
        assert "model-001" in json_str
        assert "LogisticRegression" in json_str
        
    def test_from_json(self):
        """Test creation from JSON string."""
        json_str = '''
        {
            "model_id": "model-001",
            "model_name": "LogisticRegression",
            "feature_set": "traditional",
            "train_roc_auc": 0.85,
            "test_roc_auc": 0.82,
            "train_log_loss": 0.35,
            "test_log_loss": 0.38,
            "train_brier": 0.18,
            "test_brier": 0.20,
            "hyperparameters": {},
            "cv_scores": [],
            "training_time": 0.0,
            "feature_importance": {},
            "is_real_data": true
        }
        '''
        
        result = ModelResult.from_json(json_str)
        assert result.model_id == "model-001"
        assert result.model_name == "LogisticRegression"
        
    def test_to_dataframe_row(self):
        """Test conversion to DataFrame row."""
        result = ModelResult(
            model_id="model-001",
            model_name="LogisticRegression",
            feature_set="traditional",
            train_roc_auc=0.85,
            test_roc_auc=0.82,
            train_log_loss=0.35,
            test_log_loss=0.38,
            train_brier=0.18,
            test_brier=0.20,
            cv_scores=[0.84, 0.83, 0.85, 0.82, 0.84]
        )
        
        row = result.to_dataframe_row()
        assert isinstance(row, dict)
        assert 'generalization_gap' in row
        assert 'is_overfitting' in row
        assert 'cv_mean' in row
        assert 'cv_std' in row
        assert row['generalization_gap'] == pytest.approx(0.03)
        assert row['cv_mean'] == pytest.approx(0.836)


class TestDataFrameHelpers:
    """Tests for DataFrame helper functions."""
    
    def test_create_data_models_dataframe(self):
        """Test creation of DataFrame from GameRecord list."""
        records = [
            GameRecord(
                game_id="2023-04-01-ATL-NYM",
                date=date(2023, 4, 1),
                home_team="NYM",
                away_team="ATL",
                home_score=5,
                away_score=3,
                home_wins=1,
                away_wins=1,
                home_losses=0,
                away_losses=0
            ),
            GameRecord(
                game_id="2023-04-02-ATL-NYM",
                date=date(2023, 4, 2),
                home_team="NYM",
                away_team="ATL",
                home_score=2,
                away_score=4,
                home_wins=1,
                away_wins=2,
                home_losses=1,
                away_losses=1
            )
        ]
        
        df = create_data_models_dataframe(records)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'game_id' in df.columns
        
    def test_create_data_models_dataframe_empty(self):
        """Test creation of DataFrame from empty list."""
        df = create_data_models_dataframe([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        
    def test_create_team_metrics_dataframe(self):
        """Test creation of DataFrame from TeamMetrics list."""
        metrics_list = [
            TeamMetrics(
                team_id="NYY",
                season=2023,
                games_played=162,
                wins=100,
                losses=62,
                batting_average=0.265,
                era=3.45,
                woba=0.325,
                babip=0.295,
                runs_scored=815,
                runs_allowed=650,
                home_runs=210,
                strikeouts=1350,
                walks=520
            ),
            TeamMetrics(
                team_id="BOS",
                season=2023,
                games_played=162,
                wins=90,
                losses=72,
                batting_average=0.270,
                era=4.10,
                woba=0.330,
                babip=0.300,
                runs_scored=750,
                runs_allowed=700,
                home_runs=190,
                strikeouts=1250,
                walks=480
            )
        ]
        
        df = create_team_metrics_dataframe(metrics_list)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'team_id' in df.columns
        assert 'win_pct' in df.columns
        
    def test_create_team_metrics_dataframe_empty(self):
        """Test creation of DataFrame from empty list."""
        df = create_team_metrics_dataframe([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        
    def test_create_model_results_dataframe(self):
        """Test creation of DataFrame from ModelResult list."""
        results_list = [
            ModelResult(
                model_id="model-001",
                model_name="LogisticRegression",
                feature_set="traditional",
                train_roc_auc=0.85,
                test_roc_auc=0.82,
                train_log_loss=0.35,
                test_log_loss=0.38,
                train_brier=0.18,
                test_brier=0.20,
                cv_scores=[0.84, 0.83, 0.85, 0.82, 0.84]
            ),
            ModelResult(
                model_id="model-002",
                model_name="RandomForest",
                feature_set="advanced",
                train_roc_auc=0.88,
                test_roc_auc=0.84,
                train_log_loss=0.30,
                test_log_loss=0.35,
                train_brier=0.15,
                test_brier=0.18,
                cv_scores=[0.85, 0.84, 0.86, 0.83, 0.85]
            )
        ]
        
        df = create_model_results_dataframe(results_list)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'model_id' in df.columns
        assert 'generalization_gap' in df.columns
        
    def test_create_model_results_dataframe_empty(self):
        """Test creation of DataFrame from empty list."""
        df = create_model_results_dataframe([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
