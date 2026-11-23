"""
Data models for the pipeline.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import re

class Genre(BaseModel):
    name: str
    id: Optional[str] = None

class Track(BaseModel):
    id: str
    name: str
    artist: str
    year: Optional[int] = None
    genres: List[Genre] = []

class Playlist(BaseModel):
    id: str
    name: str
    tracks: List[Track] = []

class TrackMetadata(BaseModel):
    track_id: str
    artist_id: str
    year: int
    genre: str

class YearlyGenreEmbedding(BaseModel):
    year: int
    genre: str
    vector: List[float]

class SimilarityResult(BaseModel):
    year: int
    mean_off_diagonal_similarity: float
    intra_genre_variance: float

class RegressionResult(BaseModel):
    slope: float
    intercept: float
    p_value: float
    confidence_interval: List[float]
    r_squared: float

class CooksDistanceReport(BaseModel):
    year: int
    cooks_distance: float
    is_outlier: bool
