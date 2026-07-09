"""
Data entities for the Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue project.

This module defines the core data structures used throughout the pipeline:
- Movie: Represents a single movie with metadata and revenue data
- Review: Represents a single user review with timestamp and text
- SentimentScore: Represents a computed sentiment score for a time period
- TimeSeriesMovie: Represents a movie with aligned time-series data
- GenreAnalysis: Represents aggregated analysis results by genre

All entities are designed to be serializable to/from pandas DataFrames and
follow the schema contracts defined in specs/001-sentiment-revenue-lag-analysis/contracts/
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from enum import Enum

class MovieStatus(Enum):
    """Status of a movie in the analysis pipeline."""
    PENDING = "pending"
    PROCESSED = "processed"
    EXCLUDED = "excluded"
    ERROR = "error"


@dataclass
class Movie:
    """
    Represents a single movie with its metadata and revenue data.

    Attributes:
        movie_id: Unique identifier for the movie
        title: Movie title
        release_date: Original release date
        opening_weekend_revenue: Opening weekend box office revenue (static anchor)
        total_revenue: Total box office revenue
        budget: Production budget
        genres: List of genre names
        status: Current processing status
        metadata: Additional metadata as key-value pairs
    """
    movie_id: str
    title: str
    release_date: date
    opening_weekend_revenue: Optional[float] = None
    total_revenue: Optional[float] = None
    budget: Optional[float] = None
    genres: List[str] = field(default_factory=list)
    status: MovieStatus = MovieStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert movie to dictionary representation."""
        return {
            'movie_id': self.movie_id,
            'title': self.title,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'opening_weekend_revenue': self.opening_weekend_revenue,
            'total_revenue': self.total_revenue,
            'budget': self.budget,
            'genres': self.genres,
            'status': self.status.value,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Movie':
        """Create Movie instance from dictionary."""
        release_date = data.get('release_date')
        if isinstance(release_date, str):
            release_date = datetime.fromisoformat(release_date).date()
        elif isinstance(release_date, datetime):
            release_date = release_date.date()

        genres = data.get('genres', [])
        if isinstance(genres, str):
            # Handle comma-separated genres
            genres = [g.strip() for g in genres.split(',')]

        return cls(
            movie_id=data.get('movie_id', ''),
            title=data.get('title', ''),
            release_date=release_date,
            opening_weekend_revenue=data.get('opening_weekend_revenue'),
            total_revenue=data.get('total_revenue'),
            budget=data.get('budget'),
            genres=genres,
            status=MovieStatus(data.get('status', 'pending')),
            metadata=data.get('metadata', {})
        )

    @classmethod
    def from_dataframe_row(cls, row: pd.Series) -> 'Movie':
        """Create Movie instance from a pandas DataFrame row."""
        data = row.to_dict()
        return cls.from_dict(data)


@dataclass
class Review:
    """
    Represents a single user review.

    Attributes:
        review_id: Unique identifier for the review
        movie_id: Reference to the movie this review belongs to
        author: Review author name
        content: Full review text
        rating: User rating (if available)
        timestamp: When the review was posted
        metadata: Additional metadata
    """
    review_id: str
    movie_id: str
    author: Optional[str] = None
    content: str = ""
    rating: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert review to dictionary representation."""
        return {
            'review_id': self.review_id,
            'movie_id': self.movie_id,
            'author': self.author,
            'content': self.content,
            'rating': self.rating,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Review':
        """Create Review instance from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            review_id=data.get('review_id', ''),
            movie_id=data.get('movie_id', ''),
            author=data.get('author'),
            content=data.get('content', ''),
            rating=data.get('rating'),
            timestamp=timestamp,
            metadata=data.get('metadata', {})
        )


@dataclass
class SentimentScore:
    """
    Represents a computed sentiment score for a specific time period.

    Attributes:
        movie_id: Reference to the movie
        period_start: Start of the time period (e.g., week start)
        period_end: End of the time period (e.g., week end)
        sentiment_score: VADER compound sentiment score (-1 to 1)
        review_count: Number of reviews in this period
        positive_ratio: Ratio of positive reviews
        negative_ratio: Ratio of negative reviews
        neutral_ratio: Ratio of neutral reviews
        metadata: Additional metadata
    """
    movie_id: str
    period_start: datetime
    period_end: datetime
    sentiment_score: float
    review_count: int
    positive_ratio: float = 0.0
    negative_ratio: float = 0.0
    neutral_ratio: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert sentiment score to dictionary representation."""
        return {
            'movie_id': self.movie_id,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'sentiment_score': self.sentiment_score,
            'review_count': self.review_count,
            'positive_ratio': self.positive_ratio,
            'negative_ratio': self.negative_ratio,
            'neutral_ratio': self.neutral_ratio,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentimentScore':
        """Create SentimentScore instance from dictionary."""
        period_start = datetime.fromisoformat(data['period_start'])
        period_end = datetime.fromisoformat(data['period_end'])

        return cls(
            movie_id=data.get('movie_id', ''),
            period_start=period_start,
            period_end=period_end,
            sentiment_score=float(data.get('sentiment_score', 0.0)),
            review_count=int(data.get('review_count', 0)),
            positive_ratio=float(data.get('positive_ratio', 0.0)),
            negative_ratio=float(data.get('negative_ratio', 0.0)),
            neutral_ratio=float(data.get('neutral_ratio', 0.0)),
            metadata=data.get('metadata', {})
        )


@dataclass
class TimeSeriesMovie:
    """
    Represents a movie with aligned time-series sentiment data.

    This entity combines the static revenue anchor with weekly sentiment scores,
    creating a unified view for temporal analysis.

    Attributes:
        movie: The underlying Movie object
        sentiment_series: List of sentiment scores ordered by time period
        first_review_date: Date of first review
        last_review_date: Date of last review
        total_weeks: Number of weeks with review data
        main_genre: Primary genre for grouping
    """
    movie: Movie
    sentiment_series: List[SentimentScore] = field(default_factory=list)
    first_review_date: Optional[datetime] = None
    last_review_date: Optional[datetime] = None
    total_weeks: int = 0
    main_genre: Optional[str] = None

    def __post_init__(self):
        """Calculate derived attributes after initialization."""
        if self.sentiment_series:
            # Sort by period_start
            self.sentiment_series.sort(key=lambda x: x.period_start)
            self.first_review_date = self.sentiment_series[0].period_start
            self.last_review_date = self.sentiment_series[-1].period_end
            self.total_weeks = len(self.sentiment_series)

            if not self.main_genre and self.movie.genres:
                self.main_genre = self.movie.genres[0]

    def get_weekly_sentiment(self) -> List[float]:
        """Get list of sentiment scores in chronological order."""
        return [s.sentiment_score for s in self.sentiment_series]

    def get_weekly_counts(self) -> List[int]:
        """Get list of review counts in chronological order."""
        return [s.review_count for s in self.sentiment_series]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert time series movie to pandas DataFrame."""
        rows = []
        for score in self.sentiment_series:
            row = {
                'movie_id': self.movie.movie_id,
                'title': self.movie.title,
                'release_date': self.movie.release_date.isoformat() if self.movie.release_date else None,
                'opening_weekend_revenue': self.movie.opening_weekend_revenue,
                'total_revenue': self.movie.total_revenue,
                'genres': ','.join(self.movie.genres),
                'main_genre': self.main_genre,
                'period_start': score.period_start.isoformat(),
                'period_end': score.period_end.isoformat(),
                'sentiment_score': score.sentiment_score,
                'review_count': score.review_count,
                'positive_ratio': score.positive_ratio,
                'negative_ratio': score.negative_ratio,
                'neutral_ratio': score.neutral_ratio
            }
            rows.append(row)

        return pd.DataFrame(rows)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, movie: Optional[Movie] = None) -> 'TimeSeriesMovie':
        """
        Create TimeSeriesMovie from a pandas DataFrame.

        Args:
            df: DataFrame with time series data (one row per week)
            movie: Optional Movie object. If None, will be inferred from first row
        """
        if df.empty:
            return cls(movie=movie) if movie else cls(movie=Movie(movie_id="", title="", release_date=None))

        # Infer movie from first row if not provided
        if movie is None:
            first_row = df.iloc[0]
            genres_str = first_row.get('genres', '')
            genres = [g.strip() for g in genres_str.split(',')] if genres_str else []

            release_date = first_row.get('release_date')
            if isinstance(release_date, str):
                release_date = datetime.fromisoformat(release_date).date()

            movie = Movie(
                movie_id=first_row.get('movie_id', ''),
                title=first_row.get('title', ''),
                release_date=release_date,
                opening_weekend_revenue=first_row.get('opening_weekend_revenue'),
                total_revenue=first_row.get('total_revenue'),
                genres=genres,
                main_genre=first_row.get('main_genre')
            )

        # Build sentiment series
        sentiment_series = []
        for _, row in df.iterrows():
            period_start = datetime.fromisoformat(row['period_start'])
            period_end = datetime.fromisoformat(row['period_end'])

            score = SentimentScore(
                movie_id=row['movie_id'],
                period_start=period_start,
                period_end=period_end,
                sentiment_score=float(row['sentiment_score']),
                review_count=int(row['review_count']),
                positive_ratio=float(row.get('positive_ratio', 0.0)),
                negative_ratio=float(row.get('negative_ratio', 0.0)),
                neutral_ratio=float(row.get('neutral_ratio', 0.0))
            )
            sentiment_series.append(score)

        return cls(
            movie=movie,
            sentiment_series=sentiment_series
        )


@dataclass
class GenreAnalysis:
    """
    Represents aggregated analysis results for a specific genre.

    Attributes:
        genre: Genre name
        movie_count: Number of movies in this genre
        avg_lag_weeks: Average optimal lag between sentiment and revenue
        lag_confidence_interval: 95% confidence interval for lag [low, high]
        avg_decay_rate: Average sentiment decay rate
        decay_p_value: P-value for decay slope significance
        correlation_profile: List of correlation values at different lags
        metadata: Additional analysis metadata
    """
    genre: str
    movie_count: int
    avg_lag_weeks: float
    lag_confidence_interval: List[float] = field(default_factory=list)
    avg_decay_rate: Optional[float] = None
    decay_p_value: Optional[float] = None
    correlation_profile: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert genre analysis to dictionary representation."""
        return {
            'genre': self.genre,
            'movie_count': self.movie_count,
            'avg_lag_weeks': self.avg_lag_weeks,
            'lag_confidence_interval': self.lag_confidence_interval,
            'avg_decay_rate': self.avg_decay_rate,
            'decay_p_value': self.decay_p_value,
            'correlation_profile': self.correlation_profile,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GenreAnalysis':
        """Create GenreAnalysis instance from dictionary."""
        return cls(
            genre=data.get('genre', ''),
            movie_count=int(data.get('movie_count', 0)),
            avg_lag_weeks=float(data.get('avg_lag_weeks', 0.0)),
            lag_confidence_interval=data.get('lag_confidence_interval', []),
            avg_decay_rate=data.get('avg_decay_rate'),
            decay_p_value=data.get('decay_p_value'),
            correlation_profile=data.get('correlation_profile', []),
            metadata=data.get('metadata', {})
        )

    def to_dataframe_row(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for DataFrame row."""
        row = {
            'genre': self.genre,
            'movie_count': self.movie_count,
            'avg_lag_weeks': self.avg_lag_weeks,
            'lag_ci_lower': self.lag_confidence_interval[0] if len(self.lag_confidence_interval) > 0 else None,
            'lag_ci_upper': self.lag_confidence_interval[1] if len(self.lag_confidence_interval) > 1 else None,
            'avg_decay_rate': self.avg_decay_rate,
            'decay_p_value': self.decay_p_value
        }
        row.update(self.metadata)
        return row


def create_sample_movie() -> Movie:
    """Create a sample movie for testing purposes."""
    return Movie(
        movie_id="test_001",
        title="Test Movie",
        release_date=date(2023, 1, 15),
        opening_weekend_revenue=15000000.0,
        total_revenue=50000000.0,
        budget=20000000.0,
        genres=["Action", "Adventure"],
        status=MovieStatus.PROCESSED
    )

def create_sample_sentiment_score() -> SentimentScore:
    """Create a sample sentiment score for testing purposes."""
    start = datetime(2023, 1, 15, 0, 0, 0)
    end = datetime(2023, 1, 22, 0, 0, 0)
    return SentimentScore(
        movie_id="test_001",
        period_start=start,
        period_end=end,
        sentiment_score=0.65,
        review_count=150,
        positive_ratio=0.6,
        negative_ratio=0.2,
        neutral_ratio=0.2
    )

if __name__ == "__main__":
    # Test entity creation and serialization
    movie = create_sample_movie()
    print(f"Created movie: {movie.title} ({movie.movie_id})")
    print(f"Genres: {movie.genres}")
    print(f"Revenue: ${movie.opening_weekend_revenue:,.0f}")

    sentiment = create_sample_sentiment_score()
    print(f"\nCreated sentiment score: {sentiment.sentiment_score:.2f}")
    print(f"Review count: {sentiment.review_count}")

    ts_movie = TimeSeriesMovie(movie=movie, sentiment_series=[sentiment])
    print(f"\nTime series movie: {ts_movie.movie.title}")
    print(f"Weeks of data: {ts_movie.total_weeks}")

    df = ts_movie.to_dataframe()
    print(f"\nDataFrame shape: {df.shape}")
    print(df.head())

    # Test GenreAnalysis
    analysis = GenreAnalysis(
        genre="Action",
        movie_count=100,
        avg_lag_weeks=2.5,
        lag_confidence_interval=[1.8, 3.2],
        avg_decay_rate=-0.05,
        decay_p_value=0.023
    )
    print(f"\nGenre analysis for {analysis.genre}:")
    print(f"  Avg lag: {analysis.avg_lag_weeks:.1f} weeks")
    print(f"  CI: {analysis.lag_confidence_interval}")
    print(f"  Decay rate: {analysis.avg_decay_rate:.3f}")
    print(f"  P-value: {analysis.decay_p_value:.4f}")