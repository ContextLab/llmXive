"""
Base data models for the sports prediction pipeline.

Defines core data structures for game records, team metrics, and model results.
These classes provide validation, serialization, and type safety for the pipeline.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import date
import json
import numpy as np
import pandas as pd


@dataclass
class GameRecord:
    """
    Represents a single game record with essential metadata and outcomes.
    
    Attributes:
        game_id: Unique identifier for the game
        date: Date of the game
        home_team: Home team identifier
        away_team: Away team identifier
        home_score: Final score for home team
        away_score: Final score for away team
        home_wins: Total wins for home team at time of game
        away_wins: Total wins for away team at time of game
        home_losses: Total losses for home team at time of game
        away_losses: Total losses for away team at time of game
        park_factor: Park factor adjustment (1.0 = neutral)
        weather_temp: Temperature in Fahrenheit (optional)
        wind_speed: Wind speed in mph (optional)
        is_real_data: Flag indicating if data is from real source or synthetic
    """
    game_id: str
    date: date
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    home_wins: int
    away_wins: int
    home_losses: int
    away_losses: int
    park_factor: float = 1.0
    weather_temp: Optional[float] = None
    wind_speed: Optional[float] = None
    is_real_data: bool = True
    
    def __post_init__(self):
        """Validate required fields and types."""
        if not self.game_id:
            raise ValueError("game_id cannot be empty")
        if not self.home_team or not self.away_team:
            raise ValueError("Team identifiers cannot be empty")
        if self.home_score < 0 or self.away_score < 0:
            raise ValueError("Scores cannot be negative")
        if self.park_factor <= 0:
            raise ValueError("Park factor must be positive")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling date serialization."""
        data = asdict(self)
        if isinstance(data['date'], date):
            data['date'] = data['date'].isoformat()
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameRecord':
        """Create instance from dictionary, parsing date if needed."""
        if 'date' in data and isinstance(data['date'], str):
            data['date'] = date.fromisoformat(data['date'])
        return cls(**data)
        
    def to_dataframe_row(self) -> Dict[str, Any]:
        """Convert to a flat dictionary suitable for DataFrame rows."""
        row = self.to_dict()
        # Flatten nested structures if any
        return row


@dataclass
class TeamMetrics:
    """
    Aggregated metrics for a team over a specified period.
    
    Attributes:
        team_id: Team identifier
        season: Season year
        games_played: Total games played
        wins: Total wins
        losses: Total losses
        batting_average: Team batting average
        era: Earned run average
        woba: Weighted on-base average
        babip: Batting average on balls in play
        runs_scored: Total runs scored
        runs_allowed: Total runs allowed
        home_runs: Total home runs
        strikeouts: Total strikeouts
        walks: Total walks
        park_adjusted_metrics: Dictionary of park-adjusted advanced metrics
        is_real_data: Flag indicating if metrics are from real source
    """
    team_id: str
    season: int
    games_played: int
    wins: int
    losses: int
    batting_average: float
    era: float
    woba: float
    babip: float
    runs_scored: int
    runs_allowed: int
    home_runs: int
    strikeouts: int
    walks: int
    park_adjusted_metrics: Dict[str, float] = field(default_factory=dict)
    is_real_data: bool = True
    
    def __post_init__(self):
        """Validate metrics."""
        if self.games_played <= 0:
            raise ValueError("games_played must be positive")
        if self.wins < 0 or self.losses < 0:
            raise ValueError("Wins and losses cannot be negative")
        if not (0 <= self.batting_average <= 1):
            raise ValueError("Batting average must be between 0 and 1")
        if self.era < 0:
            raise ValueError("ERA cannot be negative")
        if not (0 <= self.woba <= 1):
            raise ValueError("wOBA must be between 0 and 1")
        if not (0 <= self.babip <= 1):
            raise ValueError("BABIP must be between 0 and 1")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMetrics':
        """Create instance from dictionary."""
        return cls(**data)
        
    def win_percentage(self) -> float:
        """Calculate win percentage."""
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played
        
    def run_differential(self) -> int:
        """Calculate run differential."""
        return self.runs_scored - self.runs_allowed
        
    def to_dataframe_row(self) -> Dict[str, Any]:
        """Convert to a flat dictionary suitable for DataFrame rows."""
        row = self.to_dict()
        row['win_pct'] = self.win_percentage()
        row['run_diff'] = self.run_differential()
        return row


@dataclass
class ModelResult:
    """
    Stores results from a model training and evaluation run.
    
    Attributes:
        model_id: Unique identifier for the model run
        model_name: Name of the model type (e.g., "LogisticRegression")
        feature_set: Name of the feature set used (e.g., "traditional", "advanced")
        train_roc_auc: ROC-AUC on training set
        test_roc_auc: ROC-AUC on test set
        train_log_loss: Log-loss on training set
        test_log_loss: Log-loss on test set
        train_brier: Brier score on training set
        test_brier: Brier score on test set
        hyperparameters: Dictionary of hyperparameters used
        cv_scores: List of cross-validation scores
        training_time: Time taken for training in seconds
        feature_importance: Dictionary of feature importances (if applicable)
        is_real_data: Flag indicating if evaluation used real data
        timestamp: Timestamp when result was generated
    """
    model_id: str
    model_name: str
    feature_set: str
    train_roc_auc: float
    test_roc_auc: float
    train_log_loss: float
    test_log_loss: float
    train_brier: float
    test_brier: float
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    cv_scores: List[float] = field(default_factory=list)
    training_time: float = 0.0
    feature_importance: Dict[str, float] = field(default_factory=dict)
    is_real_data: bool = True
    timestamp: str = field(default_factory=lambda: pd.Timestamp.now().isoformat())
    
    def __post_init__(self):
        """Validate metrics."""
        if not self.model_id:
            raise ValueError("model_id cannot be empty")
        if not self.model_name:
            raise ValueError("model_name cannot be empty")
        if not self.feature_set:
            raise ValueError("feature_set cannot be empty")
            
        # Validate metrics are in valid ranges
        for metric in [self.train_roc_auc, self.test_roc_auc]:
            if not (0 <= metric <= 1):
                raise ValueError("ROC-AUC must be between 0 and 1")
                
        for metric in [self.train_log_loss, self.test_log_loss, self.train_brier, self.test_brier]:
            if metric < 0:
                raise ValueError("Log-loss and Brier scores cannot be negative")
                
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelResult':
        """Create instance from dictionary."""
        return cls(**data)
        
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
        
    @classmethod
    def from_json(cls, json_str: str) -> 'ModelResult':
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
        
    def generalization_gap(self) -> float:
        """Calculate the gap between training and test ROC-AUC."""
        return self.train_roc_auc - self.test_roc_auc
        
    def is_overfitting(self, threshold: float = 0.05) -> bool:
        """Check if the model is overfitting based on generalization gap."""
        return self.generalization_gap() > threshold
        
    def to_dataframe_row(self) -> Dict[str, Any]:
        """Convert to a flat dictionary suitable for DataFrame rows."""
        row = self.to_dict()
        row['generalization_gap'] = self.generalization_gap()
        row['is_overfitting'] = self.is_overfitting()
        row['cv_mean'] = np.mean(self.cv_scores) if self.cv_scores else 0.0
        row['cv_std'] = np.std(self.cv_scores) if self.cv_scores else 0.0
        return row


def create_data_models_dataframe(records: List[GameRecord]) -> pd.DataFrame:
    """
    Convert a list of GameRecord instances to a pandas DataFrame.
    
    Args:
        records: List of GameRecord instances
        
    Returns:
        DataFrame with one row per game record
    """
    if not records:
        return pd.DataFrame()
        
    data = [record.to_dataframe_row() for record in records]
    return pd.DataFrame(data)


def create_team_metrics_dataframe(metrics_list: List[TeamMetrics]) -> pd.DataFrame:
    """
    Convert a list of TeamMetrics instances to a pandas DataFrame.
    
    Args:
        metrics_list: List of TeamMetrics instances
        
    Returns:
        DataFrame with one row per team metrics record
    """
    if not metrics_list:
        return pd.DataFrame()
        
    data = [metric.to_dataframe_row() for metric in metrics_list]
    return pd.DataFrame(data)


def create_model_results_dataframe(results_list: List[ModelResult]) -> pd.DataFrame:
    """
    Convert a list of ModelResult instances to a pandas DataFrame.
    
    Args:
        results_list: List of ModelResult instances
        
    Returns:
        DataFrame with one row per model result
    """
    if not results_list:
        return pd.DataFrame()
        
    data = [result.to_dataframe_row() for result in results_list]
    return pd.DataFrame(data)
