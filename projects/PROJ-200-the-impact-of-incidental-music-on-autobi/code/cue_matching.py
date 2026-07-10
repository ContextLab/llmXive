"""
Cue Matching Module for the Impact of Incidental Music on Autobiographical Memory Retrieval project.

This module handles the parsing of AMT free-text cues, fuzzy string matching to MSD tracks
using Levenshtein distance, and resolution of ambiguous matches.

Functions:
  normalize_text: Normalizes text for matching (lowercase, remove punctuation).
  normalize_cues: Applies text normalization to AMT cues.
  build_inverse_index: Creates a searchable index of MSD track titles.
  match_cues: Performs fuzzy matching with Levenshtein distance <= 4.
  resolve_collisions: Resolves ambiguous matches (same title/artist).
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import pandas as pd
from python_levenshtein import distance as levenshtein_distance
from config import get_project_root, get_config_dict

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Normalizes text for matching by converting to lowercase and removing punctuation.

    Args:
        text: Input string to normalize.

    Returns:
        Normalized string.
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation and extra whitespace
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_cues(df: pd.DataFrame, cue_col: str = 'cue_text') -> pd.DataFrame:
    """
    Applies text normalization to AMT cues.

    Args:
        df: DataFrame containing AMT cues.
        cue_col: Name of the cue text column.

    Returns:
        DataFrame with normalized cue text in a new column 'normalized_cue'.
    """
    logger.info(f"Normalizing {len(df)} cues")
    df = df.copy()
    df['normalized_cue'] = df[cue_col].apply(normalize_text)
    logger.info("Cue normalization complete")
    return df

def build_inverse_index(df_tracks: pd.DataFrame, title_col: str = 'title',
                        artist_col: str = 'artist') -> Dict[str, List[Tuple[str, str]]]:
    """
    Creates a searchable index of MSD track titles.

    Args:
        df_tracks: DataFrame containing MSD track information.
        title_col: Name of the title column.
        artist_col: Name of the artist column.

    Returns:
        Dictionary mapping normalized titles to list of (title, artist) tuples.
    """
    logger.info("Building inverse index of track titles")
    index = {}
    
    for _, row in df_tracks.iterrows():
        title = row[title_col]
        artist = row[artist_col]
        normalized_title = normalize_text(title)
        
        if normalized_title not in index:
            index[normalized_title] = []
        index[normalized_title].append((title, artist))
    
    logger.info(f"Built index with {len(index)} unique normalized titles")
    return index

def match_cues(df_cues: pd.DataFrame, df_tracks: pd.DataFrame, 
               threshold: int = 4, cue_col: str = 'normalized_cue',
               title_col: str = 'title', artist_col: str = 'artist') -> pd.DataFrame:
    """
    Performs fuzzy matching with Levenshtein distance <= 4.

    Args:
        df_cues: DataFrame with normalized cues.
        df_tracks: DataFrame with MSD track information.
        threshold: Maximum Levenshtein distance for a match.
        cue_col: Name of the normalized cue column.
        title_col: Name of the track title column.
        artist_col: Name of the track artist column.

    Returns:
        DataFrame with matched track information and match status.
    """
    logger.info(f"Matching cues with Levenshtein threshold = {threshold}")
    
    # Build inverse index
    track_index = build_inverse_index(df_tracks, title_col, artist_col)
    
    # Prepare results
    results = []
    unmatched_count = 0
    
    for _, cue_row in df_cues.iterrows():
        cue_text = cue_row[cue_col]
        best_match = None
        min_distance = float('inf')
        
        # Check against indexed titles
        for normalized_title, track_info_list in track_index.items():
            dist = levenshtein_distance(cue_text, normalized_title)
            if dist < min_distance:
                min_distance = dist
                best_match = track_info_list[0]  # Take first match for now
        
        if min_distance <= threshold:
            results.append({
                'cue_id': cue_row.get('cue_id', None),
                'matched_title': best_match[0],
                'matched_artist': best_match[1],
                'match_distance': min_distance,
                'is_match': True
            })
        else:
            results.append({
                'cue_id': cue_row.get('cue_id', None),
                'matched_title': None,
                'matched_artist': None,
                'match_distance': min_distance,
                'is_match': False
            })
            unmatched_count += 1
    
    df_matched = pd.DataFrame(results)
    match_rate = 1 - (unmatched_count / len(df_cues))
    
    logger.info(f"Matching complete: {match_rate:.2%} match rate ({unmatched_count} unmatched)")
    return df_matched

def resolve_collisions(df_matched: pd.DataFrame, threshold: int = 4) -> pd.DataFrame:
    """
    Resolves ambiguous matches (same title/artist) and logs collisions.

    Args:
        df_matched: DataFrame with matched cues.
        threshold: Maximum Levenshtein distance for a match.

    Returns:
        DataFrame with resolved matches.
    """
    logger.info("Resolving match collisions")
    
    df = df_matched.copy()
    collisions = 0
    
    # Group by matched title and artist to find collisions
    # For this implementation, we assume the first match is the best
    # In a more complex scenario, we might use additional heuristics
    
    df = df.sort_values('match_distance')
    df = df.drop_duplicates(subset=['cue_id'], keep='first')
    
    logger.info("Collision resolution complete")
    return df
