"""
Configuration constants specific to the PROJ-540 pipeline.

Centralizes paths and thresholds used across the research modules.
"""

from pathlib import Path

# Project relative paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Analysis thresholds
MIN_SAMPLE_SIZE_POWER = 30
LOW_POWER_WARNING_THRESHOLD = 100
HIGH_ENGAGEMENT_PERCENTILE = 0.75  # Top 25%
ENGAGEMENT_CORRELATION_THRESHOLD = 0.3

# Variable names (canonical)
VAR_NEWS_EXPOSURE = "news_exposure_freq"
VAR_ANXIETY_SCORE = "anxiety_score"
VAR_BASELINE_ANXIETY = "baseline_anxiety"
VAR_AGE = "age"
VAR_GENDER = "gender"
VAR_SOCIAL_MEDIA_ENGAGEMENT = "social_media_engagement"

REQUIRED_COLUMNS = [
    VAR_NEWS_EXPOSURE,
    VAR_ANXIETY_SCORE,
    VAR_BASELINE_ANXIETY,
    VAR_AGE,
    VAR_GENDER
]

MODEL_FORMULA = f"{VAR_ANXIETY_SCORE} ~ {VAR_NEWS_EXPOSURE} + {VAR_BASELINE_ANXIETY} + {VAR_AGE} + {VAR_GENDER}"