"""
Cue Matching Module for the Impact of Incidental Music on Autobiographical Memory Retrieval.

This module handles the normalization of memory cues, fuzzy matching to track titles,
and resolution of ambiguous matches.

Functions:
  - normalize_text: Standardize text for comparison.
  - normalize_cues: Process the AMT cues dataframe.
  - build_inverse_index: Create a searchable index of MSD titles.
  - match_cues: Perform fuzzy matching with Levenshtein distance.
  - resolve_collisions: Handle ambiguous matches.
  - main: Orchestrates the matching pipeline.
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import pandas as pd
from python_levenshtein import distance as levenshtein_distance

from config import get_project_root, get_config_dict
from utils import get_logger

logger = get_logger(__name__)

def normalize_text(text: str) -> str:
    """
    Normalize text: lowercase, remove punctuation, strip whitespace.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_cues(amt_df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize AMT cues and load MSD track titles into a searchable index.
    """
    logger.info("Normalizing cues...")
    df = amt_df.copy()
    if "cue_text" not in df.columns:
        raise ValueError("AMT dataset missing 'cue_text' column.")
    if "msd_title" not in df.columns:
        raise ValueError("MSD dataset missing 'msd_title' column (or title column).")

    df["normalized_cue"] = df["cue_text"].apply(normalize_text)
    # Assuming MSD has a 'title' column
    if "title" in df.columns:
        df["normalized_title"] = df["title"].apply(normalize_text)
    elif "track_title" in df.columns:
        df["normalized_title"] = df["track_title"].apply(normalize_text)
    else:
        raise ValueError("No title column found in MSD data.")

    return df

def build_inverse_index(df: pd.DataFrame, title_col: str = "normalized_title") -> Dict[str, List[str]]:
    """
    Build an inverse index mapping normalized titles to track_ids.
    """
    index = {}
    for _, row in df.iterrows():
        key = row[title_col]
        tid = row["track_id"]
        if key not in index:
            index[key] = []
        index[key].append(tid)
    return index

def match_cues(cues_df: pd.DataFrame, threshold: int = 4) -> pd.DataFrame:
    """
    Perform fuzzy matching with Levenshtein distance <= threshold.
    Logs unmatched cues.
    """
    logger.info(f"Matching cues with Levenshtein threshold={threshold}")
    config = get_config_dict()
    threshold = config.get("levenshtein_threshold", threshold)

    results = []
    unmatched = []

    # Create index from cues_df (assuming it has normalized_title and track_id)
    # If cues_df is just AMT, we need to join with MSD first or pass MSD separately.
    # Assuming cues_df is the result of normalize_cues which merged AMT and MSD.
    # If not merged, we need to iterate over unique titles.

    # Simplified: Assume cues_df has 'normalized_cue' and we search against unique 'normalized_title'
    unique_titles = cues_df[["normalized_title", "track_id"]].drop_duplicates()
    title_list = unique_titles["normalized_title"].tolist()

    for _, row in cues_df.iterrows():
        cue = row["normalized_cue"]
        if not cue:
            unmatched.append(row)
            continue

        best_match = None
        best_dist = float('inf')

        for title in title_list:
            d = levenshtein_distance(cue, title)
            if d < best_dist:
                best_dist = d
                best_match = title

        if best_dist <= threshold:
            # Find the track_id for best_match
            tid = unique_titles[unique_titles["normalized_title"] == best_match]["track_id"].iloc[0]
            results.append({
                "user_id": row.get("user_id"),
                "cue_text": row["cue_text"],
                "matched_track_id": tid,
                "match_distance": best_dist
            })
        else:
            unmatched.append(row)

    matched_df = pd.DataFrame(results)
    logger.info(f"Matched {len(matched_df)} cues, {len(unmatched)} unmatched.")

    # Log unmatched
    root = get_project_root()
    log_path = root / "data" / "audit_log.txt"
    with open(log_path, "a") as f:
        f.write(f"\n--- Matching Audit ---\n")
        f.write(f"Matched: {len(matched_df)}, Unmatched: {len(unmatched)}\n")

    return matched_df

def resolve_collisions(matched_df: pd.DataFrame) -> pd.DataFrame:
    """
    Resolve ambiguous matches (same title/artist) and log collisions.
    For simplicity, we assume track_id is unique after matching.
    If multiple track_ids have the same title, we might need artist info.
    Here we just log if a track_id appears multiple times with different cues (normal)
    or if a cue matches multiple track_ids (collision).
    """
    logger.info("Resolving collisions...")
    # Assuming matched_df has matched_track_id.
    # If a cue matched multiple titles (not handled in simple match_cues above), we'd handle here.
    # Since match_cues picks the best, collisions are rare unless exact ties.
    # We'll just log the distribution.
    counts = matched_df["matched_track_id"].value_counts()
    logger.info(f"Track distribution: {len(counts)} unique tracks matched.")
    return matched_df

def main():
    """
    Orchestrate the cue matching pipeline.
    """
    logger.info("Starting cue matching pipeline...")
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load AMT and MSD
    # Assuming they are in data/raw/ from T013
    amt_path = root / "data" / "raw" / "amt_cues.csv"
    msd_path = root / "data" / "raw" / "msd_tracks.csv"

    if not amt_path.exists() or not msd_path.exists():
        raise FileNotFoundError("Raw data files not found. Run ingestion first.")

    amt_df = pd.read_csv(amt_path)
    msd_df = pd.read_csv(msd_path)

    # Normalize
    # We need to merge AMT and MSD to have titles available for matching?
    # Or match AMT cues against MSD titles.
    # Let's assume we merge them on nothing, just to have both in one DF for matching logic.
    # Actually, we iterate AMT cues and compare to MSD titles.
    # So we normalize both.
    amt_df["normalized_cue"] = amt_df["cue_text"].apply(normalize_text)
    msd_df["normalized_title"] = msd_df["title"].apply(normalize_text)

    # Match
    matched_df = match_cues(amt_df)

    # Resolve
    matched_df = resolve_collisions(matched_df)

    # Save
    output_path = processed_dir / "matched_cues.parquet"
    matched_df.to_parquet(output_path, index=False)

    logger.info(f"Matching complete. Output saved to {output_path}")
    return matched_df

if __name__ == "__main__":
    main()
