"""
Agency Scoring Module.

This module computes agency scores from conversation transcripts by detecting
linguistic markers and aggregating them with configurable weights.
"""

from .compute_scores import compute_agency_scores, main as scores_main
from .detect_markers import detect_markers, main as markers_main
from .ingest_transcripts import ingest_transcripts, main as ingest_main

__all__ = [
    "compute_agency_scores",
    "detect_markers",
    "ingest_transcripts",
    "main",
    "scores_main",
    "markers_main",
    "ingest_main",
]
