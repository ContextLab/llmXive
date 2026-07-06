"""
Data schema definitions and Pydantic models for Track, Playlist, and Genre entities.

These models define the structure for ingested MPD data, matched MusicBrainz metadata,
and derived genre entities used throughout the pipeline.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import re

class Genre(BaseModel):
    """Represents a music genre entity."""
    name: str = Field(..., description="The name of the genre")
    id: Optional[str] = Field(None, description="Unique identifier for the genre (e.g., MusicBrainz ID)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Genre name cannot be empty")
        return v.strip().lower()

class Track(BaseModel):
    """Represents a music track with metadata from MPD and MusicBrainz."""
    track_id: str = Field(..., description="Unique identifier for the track (MPD track ID)")
    title: Optional[str] = Field(None, description="Track title")
    artist: Optional[str] = Field(None, description="Artist name")
    album: Optional[str] = Field(None, description="Album name")
    year: Optional[int] = Field(None, description="Release year")
    genres: List[Genre] = Field(default_factory=list, description="List of genres associated with this track")
    duration_ms: Optional[int] = Field(None, description="Track duration in milliseconds")
    popularity: Optional[int] = Field(None, description="Track popularity score (0-100)")
    isrc: Optional[str] = Field(None, description="International Standard Recording Code")
    
    @field_validator('year')
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 1900 or v > datetime.now().year + 1:
                raise ValueError(f"Year {v} is outside valid range (1900-{datetime.now().year + 1})")
        return v

class Playlist(BaseModel):
    """Represents a playlist entity from the MPD dataset."""
    playlist_id: str = Field(..., description="Unique identifier for the playlist")
    name: Optional[str] = Field(None, description="Playlist name")
    owner: Optional[str] = Field(None, description="Playlist owner")
    tracks: List[Track] = Field(default_factory=list, description="List of tracks in the playlist")
    created_at: Optional[datetime] = Field(None, description="Playlist creation timestamp")
    is_public: bool = Field(default=True, description="Whether the playlist is public")
    
    @property
    def track_count(self) -> int:
        """Returns the number of tracks in the playlist."""
        return len(self.tracks)

class TrackMetadata(BaseModel):
    """
    Intermediate schema for raw metadata before joining MPD and MusicBrainz data.
    Used during the ingestion and matching process.
    """
    mpd_track_id: str
    mpd_artist: Optional[str]
    mpd_album: Optional[str]
    mpd_year: Optional[int]
    mb_artist_name: Optional[str]
    mb_track_name: Optional[str]
    mb_release_year: Optional[int]
    mb_artist_id: Optional[str]
    mb_track_id: Optional[str]
    match_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    match_method: Optional[str] = Field(None, description="Method used for matching (e.g., 'exact', 'fuzzy')")
    
    @model_validator(mode='after')
    def validate_match(self):
        if self.match_confidence is not None and (self.match_confidence < 0.0 or self.match_confidence > 1.0):
            raise ValueError("match_confidence must be between 0.0 and 1.0")
        return self

class YearlyGenreEmbedding(BaseModel):
    """
    Schema for a yearly aggregated genre embedding vector.
    """
    year: int
    genre: str
    embedding_vector: List[float] = Field(..., description="The vector representation (dimension=100)")
    track_count: int = Field(..., description="Number of unique tracks used for this aggregation")
    coverage_flag: bool = Field(False, description="True if track_count < 1000 (low coverage)")
    
    @field_validator('embedding_vector')
    @classmethod
    def validate_embedding(cls, v: List[float]) -> List[float]:
        if len(v) != 100:
            raise ValueError(f"Embedding vector must have exactly 100 dimensions, got {len(v)}")
        return v

class SimilarityResult(BaseModel):
    """Schema for pairwise similarity results between yearly genre vectors."""
    year: int
    mean_off_diagonal_similarity: float
    intra_genre_variance: float
    sample_size: int = Field(..., description="Number of year pairs used in calculation")
    
    @field_validator('mean_off_diagonal_similarity', 'intra_genre_variance')
    @classmethod
    def validate_similarity_metrics(cls, v: float) -> float:
        if v < -1.0 or v > 1.0:
            raise ValueError(f"Similarity metric must be in range [-1, 1], got {v}")
        return v

class RegressionResult(BaseModel):
    """Schema for linear regression results on similarity trends."""
    slope: float
    intercept: float
    r_squared: float
    p_value: float
    confidence_interval_95: List[float] = Field(..., description="Lower and upper bounds of 95% CI for slope")
    n_observations: int
    flagged_low_coverage_years: List[int] = Field(default_factory=list, description="Years excluded due to low coverage")
    warning_high_missing_genre_rate: bool = Field(False, description="True if >20% missing genre tags detected")

class CooksDistanceReport(BaseModel):
    """Schema for Cook's Distance outlier analysis results."""
    year: int
    cooks_distance: float
    is_outlier: bool
    leverage: float
    residual: float