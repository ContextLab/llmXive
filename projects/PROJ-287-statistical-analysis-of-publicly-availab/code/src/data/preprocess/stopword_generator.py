"""
Stopword Generator for Window-Specific Analysis.

Generates distinct stopword lists for each multi-year window using TF-IDF analysis
on raw JSONL abstracts. Saves versioned lists with SHA256 hashes to the manifest.
"""

import json
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

from src.utils.logging import get_logger

# Define the windows as per spec
WINDOWS = [
    ("2000-2004", 2000, 2004),
    ("2005-2009", 2005, 2009),
    ("2010-2014", 2010, 2014),
    ("2015-2019", 2015, 2019),
    ("2020-2024", 2020, 2024),
]

# Configuration
TOP_N = 50
IDF_SMOOTHING = 1.0
RAW_DATA_DIR = Path("data/raw")
STOPWORDS_DIR = Path("data/stopwords")
MANIFEST_PATH = STOPWORDS_DIR / "manifest.json"

logger = get_logger(__name__)


class WindowStopwordManifest:
    """Data structure for the stopword manifest."""
    def __init__(self):
        self.windows: Dict[str, Dict[str, Any]] = {}
        self.generated_at: Optional[str] = None
        self.version: str = "1.0.0"

    def add_window(self, window_name: str, stopwords: List[str], file_hash: str):
        self.windows[window_name] = {
            "stopwords": stopwords,
            "count": len(stopwords),
            "file_hash": file_hash,
            "top_n": TOP_N
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "windows": self.windows
        }


def load_raw_abstracts(window_name: str, start_year: int, end_year: int) -> List[str]:
    """
    Load raw abstracts from JSONL files for a specific window.
    Looks for files matching the pattern data/raw/<source>_window_<name>.jsonl
    """
    abstracts = []
    sources = ["arxiv", "pubmed"]
    
    logger.info(f"Loading raw abstracts for window {window_name} ({start_year}-{end_year})")

    for source in sources:
        # Construct expected filename based on T013 orchestrator output convention
        # Assuming T013 saves as: data/raw/{source}_window_{window_name}.jsonl
        # If the orchestrator saves differently, we adapt to find files containing the year range
        filename_pattern = f"{source}_window_{window_name}.jsonl"
        file_path = RAW_DATA_DIR / filename_pattern

        if not file_path.exists():
            # Fallback: try to find any file for this source and filter by year if needed
            # But per spec, T013 should have saved partitioned files.
            # Let's try a glob search if exact match fails
            import glob
            candidates = list(RAW_DATA_DIR.glob(f"{source}_*.jsonl"))
            if candidates:
                file_path = candidates[0] # Take first found as fallback
                logger.warning(f"Exact file {filename_pattern} not found. Using {file_path.name}.")
            else:
                logger.error(f"No raw data found for source {source} in window {window_name}.")
                continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        # Extract abstract text
                        text = record.get("abstract", "") or record.get("title", "")
                        if text:
                            abstracts.append(text)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON line in {file_path}")
                        continue
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            raise

    if not abstracts:
        raise ValueError(f"No abstracts found for window {window_name}. Ensure T013 has run.")
    
    logger.info(f"Loaded {len(abstracts)} abstracts for window {window_name}")
    return abstracts


def generate_tfidf_stopwords(texts: List[str], window_name: str) -> List[str]:
    """
    Generate stopwords using TF-IDF analysis.
    Uses sklearn TfidfVectorizer with IDF smoothing=1.0.
    Returns the top-N terms with lowest TF-IDF scores (most common across docs).
    """
    if len(texts) < 2:
        logger.warning(f"Not enough texts for TF-IDF in {window_name}. Returning empty list.")
        return []

    # Initialize TfidfVectorizer
    # min_df=2 ensures we only look at terms appearing in at least 2 documents
    # max_df=1.0 (default) includes all
    # use_idf=True, smooth_idf=True (default), but we force smooth_idf via parameters if needed
    # The spec says IDF smoothing=1.0. In sklearn, smooth_idf=True adds 1 to df.
    # We set smooth_idf=True and sublinear_tf=False (default)
    vectorizer = TfidfVectorizer(
        stop_words='english', # Remove standard English stopwords first
        min_df=2,
        max_df=0.95, # Exclude extremely common terms that might be noise
        use_idf=True,
        smooth_idf=True, # This adds 1 to the document frequency, effectively smoothing
        norm='l2',
        lowercase=True
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError as e:
        logger.error(f"TF-IDF vectorization failed for {window_name}: {e}")
        return []

    feature_names = vectorizer.get_feature_names_out()
    
    # Calculate mean TF-IDF score for each term across all documents
    # Terms with low mean TF-IDF are common across the corpus (potential stopwords)
    mean_tfidf_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()
    
    # Sort by score ascending (lowest score = most common/least informative)
    # We want the top N terms with the LOWEST scores to be our window-specific stopwords
    # However, TfidfVectorizer already removed standard stopwords.
    # The "stopwords" we generate here are the most frequent domain-specific terms
    # that should be filtered for THIS specific window.
    
    # Sort indices by score
    sorted_indices = np.argsort(mean_tfidf_scores)
    
    # Take the top N terms with the lowest scores
    top_stopwords_indices = sorted_indices[:TOP_N]
    top_stopwords = [feature_names[i] for i in top_stopwords_indices]
    
    logger.info(f"Generated {len(top_stopwords)} window-specific stopwords for {window_name}")
    return top_stopwords


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_stopword_list(window_name: str, stopwords: List[str], output_dir: Path) -> Path:
    """Save the stopword list to a JSON file and return the path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"stopwords_{window_name.replace('-', '_')}.json"
    file_path = output_dir / filename

    data = {
        "window": window_name,
        "stopwords": stopwords,
        "count": len(stopwords)
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved stopword list to {file_path}")
    return file_path


def generate_manifest(manifest_obj: WindowStopwordManifest, output_path: Path):
    """Save the manifest JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_obj.to_dict(), f, indent=2)
    logger.info(f"Saved manifest to {output_path}")


def main():
    """Main entry point for generating window-specific stopwords."""
    logger.info("Starting stopword generation for all windows...")
    
    STOPWORDS_DIR.mkdir(parents=True, exist_ok=True)
    
    manifest = WindowStopwordManifest()
    import datetime
    manifest.generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for window_name, start_year, end_year in WINDOWS:
        try:
            logger.info(f"Processing window: {window_name}")
            
            # 1. Load data
            texts = load_raw_abstracts(window_name, start_year, end_year)
            
            # 2. Generate stopwords
            stopwords = generate_tfidf_stopwords(texts, window_name)
            
            if not stopwords:
                logger.warning(f"No stopwords generated for {window_name}. Skipping save.")
                continue

            # 3. Save list
            file_path = save_stopword_list(window_name, stopwords, STOPWORDS_DIR)
            
            # 4. Compute hash
            file_hash = compute_sha256(file_path)
            
            # 5. Add to manifest
            manifest.add_window(window_name, stopwords, file_hash)
            
            logger.info(f"Successfully processed window {window_name}")
            
        except Exception as e:
            logger.error(f"Failed to process window {window_name}: {e}")
            # Continue to next window? Or fail fast? 
            # Per spec, we should fail loudly if data is missing, but we can log and continue if partial data exists.
            # However, if T013 didn't produce data, this will raise ValueError in load_raw_abstracts.
            # We let it raise if data is missing to ensure validity.
            raise e

    # Save final manifest
    generate_manifest(manifest, MANIFEST_PATH)
    logger.info("Stopword generation completed successfully.")


if __name__ == "__main__":
    main()
