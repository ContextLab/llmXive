"""
Cue Matching Module for PROJ-200.

This module handles the normalization of AMT cues, fuzzy matching to MSD tracks,
and resolution of collisions. It implements the logic for T022-T024.
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
    Normalizes a text string for comparison.

    - Converts to lowercase
    - Removes punctuation
    - Removes extra whitespace

    Args:
        text (str): The input text.

    Returns:
        str: The normalized text.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_cues(cues_df: pd.DataFrame, title_col: str = 'cue_text') -> pd.DataFrame:
    """
    Normalizes the cue text in the dataframe.

    Args:
        cues_df (pd.DataFrame): The dataframe containing cues.
        title_col (str): The column name containing the cue text.

    Returns:
        pd.DataFrame: The dataframe with a new 'normalized_cue' column.
    """
    logger.info("Normalizing cues...")
    cues_df['normalized_cue'] = cues_df[title_col].apply(normalize_text)
    return cues_df

def build_inverse_index(tracks_df: pd.DataFrame, title_col: str = 'title', artist_col: str = 'artist') -> Dict[str, List[Tuple[str, str]]]:
    """
    Builds an inverse index of normalized track titles to their original (title, artist) pairs.

    Args:
        tracks_df (pd.DataFrame): The dataframe containing track metadata.
        title_col (str): Column name for track title.
        artist_col (str): Column name for track artist.

    Returns:
        Dict[str, List[Tuple[str, str]]]: Mapping from normalized title to list of (title, artist).
    """
    logger.info("Building inverse index for track titles...")
    index = {}
    for _, row in tracks_df.iterrows():
        norm_title = normalize_text(row[title_col])
        if not norm_title:
            continue
        if norm_title not in index:
            index[norm_title] = []
        index[norm_title].append((row[title_col], row[artist_col]))
    return index

def match_cues(cues_df: pd.DataFrame, tracks_df: pd.DataFrame, threshold: int = 4) -> pd.DataFrame:
    """
    Performs fuzzy matching between cues and tracks using Levenshtein distance.

    This implements T023. Matches are found if the distance is <= threshold.
    Unmatched cues are logged.

    Args:
        cues_df (pd.DataFrame): The dataframe with cues.
        tracks_df (pd.DataFrame): The dataframe with tracks.
        threshold (int): Maximum Levenshtein distance.

    Returns:
        pd.DataFrame: The cues dataframe with match results.
    """
    logger.info(f"Starting cue matching with threshold {threshold}...")
    
    # Build index
    index = build_inverse_index(tracks_df)
    
    matched_count = 0
    unmatched_count = 0
    
    results = []

    for _, cue_row in cues_df.iterrows():
        norm_cue = cue_row['normalized_cue']
        best_match = None
        best_dist = float('inf')
        
        # Simple search: check against all unique normalized titles in index
        # In a production system, this would be optimized (e.g., using a trie or BK-tree)
        for norm_track_title, candidates in index.items():
            dist = levenshtein_distance(norm_cue, norm_track_title)
            if dist <= threshold and dist < best_dist:
                best_dist = dist
                best_match = candidates # List of (title, artist)
        
        if best_match:
            matched_count += 1
            # Resolve collisions later, store candidates for now
            results.append({
                'cue_id': cue_row['cue_id'],
                'matched_candidates': best_match,
                'distance': best_dist,
                'is_matched': True
            })
        else:
            unmatched_count += 1
            results.append({
                'cue_id': cue_row['cue_id'],
                'matched_candidates': [],
                'distance': None,
                'is_matched': False
            })

    logger.info(f"Matching complete. Matched: {matched_count}, Unmatched: {unmatched_count}")
    
    # Log unmatched if rate is low
    total = len(cues_df)
    match_rate = matched_count / total if total > 0 else 0
    if match_rate < 0.80:
        logger.warning(f"Match rate is {match_rate:.2%}, which is below the 80% threshold (SC-004). Proceeding with warning.")

    # Add results to dataframe
    for i, res in enumerate(results):
        cues_df.at[i, 'is_matched'] = res['is_matched']
        cues_df.at[i, 'matched_candidates'] = res['matched_candidates']
        cues_df.at[i, 'distance'] = res['distance']

    return cues_df

def resolve_collisions(cues_df: pd.DataFrame) -> pd.DataFrame:
    """
    Resolves ambiguous matches where a cue matches multiple tracks.

    This implements T024. Currently, it picks the first match or the one with the
    smallest distance if available. In a full system, this might use artist metadata.

    Args:
        cues_df (pd.DataFrame): The dataframe with matched candidates.

    Returns:
        pd.DataFrame: The dataframe with a single 'matched_track_id' (or title).
    """
    logger.info("Resolving collisions...")
    resolved_count = 0
    collision_count = 0

    for i, row in cues_df.iterrows():
        if not row['is_matched']:
            continue
        
        candidates = row['matched_candidates']
        if len(candidates) == 1:
            cues_df.at[i, 'matched_title'] = candidates[0][0]
            cues_df.at[i, 'matched_artist'] = candidates[0][1]
            resolved_count += 1
        else:
            # Collision: pick the first one (or implement more complex logic)
            # For this implementation, we pick the first candidate and log the collision
            cues_df.at[i, 'matched_title'] = candidates[0][0]
            cues_df.at[i, 'matched_artist'] = candidates[0][1]
            collision_count += 1
            logger.debug(f"Collision resolved for cue {row['cue_id']}: {len(candidates)} candidates found. Picked: {candidates[0][0]}")

    if collision_count > 0:
        logger.info(f"Resolved {collision_count} collisions by picking the first candidate.")

    return cues_df
