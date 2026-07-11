import os
import sys
import json
import logging
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import from project utils and config
from utils import get_logger, tokenize_char_level_no_punct, save_json, load_json, ensure_dir
from config import load_config, set_seed, get_seed
from update_state import load_state, save_state, hash_artifact, register_artifact, update_artifact_hash

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "arxiv_subset.parquet"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
STATE_FILE = PROJECT_ROOT / "state" / "PROJ-809-llmxive-followup.yaml"

def download_arxiv_dataset(categories: List[str] = None, split: str = "train") -> Path:
    """
    Downloads the arXiv dataset filtered by categories and saves it to data/raw.
    Uses the 'arxiv' dataset package which is pip-installable.
    """
    if categories is None:
        categories = ["cs.CL", "physics.gen-ph", "q-bio.QM"]
    
    try:
        import datasets
        logger = get_logger(__name__)
        logger.info(f"Downloading arXiv dataset for categories: {categories}, split: {split}")
        
        # Load the arxiv dataset
        # Note: The 'arxiv' dataset in HuggingFace datasets contains abstracts and authors
        ds = datasets.load_dataset("arxiv", split=split)
        
        # Filter by categories if the dataset supports it
        # The 'arxiv' dataset usually has a 'categories' list field
        if 'categories' in ds.column_names:
            # Filter rows where any category matches our list
            mask = ds['categories'].apply(lambda cats: any(c in categories for c in cats))
            ds_filtered = ds.filter(mask)
        else:
            # Fallback if column name differs, though standard arxiv dataset has 'categories'
            logger.warning("Category column not found, downloading full split. Filtering might be needed manually.")
            ds_filtered = ds

        # Save to parquet
        ensure_dir(RAW_DATA_PATH.parent)
        output_path = RAW_DATA_PATH
        ds_filtered.to_parquet(str(output_path))
        logger.info(f"Dataset saved to {output_path}")
        return output_path
    except ImportError:
        raise ImportError("The 'datasets' package is required. Please install it via 'pip install datasets'.")
    except Exception as e:
        raise RuntimeError(f"Failed to download or process dataset: {e}")

def extract_authors_with_counts(df_path: Path) -> Dict[str, int]:
    """
    Reads the parquet file and extracts author counts.
    Returns a dictionary of author names to their document counts.
    """
    try:
        import pandas as pd
        df = pd.read_parquet(df_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read parquet file {df_path}: {e}")

    # Check for author column
    if 'authors' not in df.columns:
        # Try common alternatives
        if 'author' in df.columns:
            author_col = 'author'
        else:
            raise KeyError("No 'authors' or 'author' column found in dataset.")
    else:
        author_col = 'authors'

    # Flatten author lists if they are stored as lists of strings
    # Assuming the column contains lists of strings like ['Smith, John', 'Doe, Jane']
    all_authors = []
    for item in df[author_col]:
        if isinstance(item, list):
            all_authors.extend(item)
        elif isinstance(item, str):
            all_authors.append(item)
        # Ignore None or other types

    # Count occurrences
    from collections import Counter
    author_counts = Counter(all_authors)
    return dict(author_counts)

def log_author_collisions(author_counts: Dict[str, int], threshold: int = 50) -> List[str]:
    """
    Logs warnings for authors appearing more than the threshold times.
    Returns a list of author names that triggered the warning.
    """
    logger = get_logger(__name__)
    collision_authors = []
    for author, count in author_counts.items():
        if count > threshold:
            collision_authors.append(author)
            logger.warning(f"Author '{author}' appears {count} times, exceeding threshold of {threshold}.")
    return collision_authors

def generate_collision_report(collision_authors: List[str], output_path: Path) -> None:
    """
    Writes the collision report to a JSON file.
    """
    ensure_dir(output_path.parent)
    report = {
        "threshold": 50,
        "collision_authors": collision_authors,
        "count": len(collision_authors)
    }
    save_json(report, output_path)

def update_state_with_collision_status(collision_authors: List[str], state_file: Path) -> None:
    """
    Updates the state file with the collision status.
    """
    state = load_state(state_file)
    state["collision_status"] = {
        "manual_review_required": len(collision_authors) > 0,
        "critical_threshold_exceeded": False, # Logic for critical threshold can be added here
        "flagged_authors": collision_authors
    }
    save_state(state, state_file)

def preprocess_abstracts(df_path: Path, output_dir: Path) -> Tuple[Path, Path]:
    """
    Reads the parquet file, filters abstracts < 6 chars,
    preprocesses them (lowercase, remove punctuation, tokenize to char sequences),
    and saves the result.
    
    Also organizes data by author into subdirectories.
    """
    try:
        import pandas as pd
        df = pd.read_parquet(df_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read parquet file {df_path}: {e}")

    # Determine author column
    author_col = 'authors' if 'authors' in df.columns else ('author' if 'author' in df.columns else None)
    if not author_col:
        raise KeyError("No author column found in dataset.")
    
    # Determine abstract column
    abstract_col = 'abstract' if 'abstract' in df.columns else None
    if not abstract_col:
        raise KeyError("No 'abstract' column found in dataset.")

    # Filter abstracts < 6 characters
    original_count = len(df)
    # Ensure abstract is string before length check
    df = df[df[abstract_col].apply(lambda x: isinstance(x, str) and len(x) >= 6)]
    filtered_count = len(df)
    
    logger = get_logger(__name__)
    logger.info(f"Filtered {original_count - filtered_count} abstracts shorter than 6 characters.")

    # Prepare output directory structure
    ensure_dir(output_dir)
    processed_data_path = output_dir / "corpus.json"
    
    corpus_data = []
    author_folders = {} # Map author_name -> list of texts

    for _, row in df.iterrows():
        authors_raw = row[author_col]
        abstract = row[abstract_col]
        
        # Handle authors (take first if list)
        if isinstance(authors_raw, list) and len(authors_raw) > 0:
            primary_author = authors_raw[0]
        elif isinstance(authors_raw, str):
            primary_author = authors_raw
        else:
            continue # Skip rows with no valid author

        # Preprocess text:
        # 1. Lowercase
        # 2. Remove punctuation (using utils function which handles char-level no punct)
        # 3. Tokenize to character sequences (string of chars)
        
        # The utils function tokenize_char_level_no_punct returns a string of chars without punctuation
        # We need to ensure it's lowercased first.
        processed_text = tokenize_char_level_no_punct(abstract.lower())
        
        if not processed_text:
            continue # Skip if empty after processing

        # Store in corpus
        corpus_data.append({
            "author": primary_author,
            "text": processed_text,
            "original_length": len(abstract),
            "processed_length": len(processed_text)
        })

        # Organize by author for file output
        if primary_author not in author_folders:
            author_folders[primary_author] = []
        author_folders[primary_author].append(processed_text)

    # Save the flat corpus JSON
    save_json(corpus_data, processed_data_path)
    logger.info(f"Saved processed corpus to {processed_data_path}")

    # Save individual author files for convenience (optional but good for structure)
    # Create author directories
    for author, texts in author_folders.items():
        # Sanitize author name for directory
        safe_author = re.sub(r'[^\w\s-]', '_', author).strip()
        author_dir = output_dir / safe_author
        ensure_dir(author_dir)
        
        for i, text in enumerate(texts):
            # Save each text as a file
            file_path = author_dir / f"text_{i:05d}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
    
    logger.info(f"Saved author-specific files to {output_dir}")
    return processed_data_path, output_dir

def save_processed_corpus(corpus_data: List[Dict], output_path: Path) -> None:
    """
    Helper to save the processed corpus list to a JSON file.
    """
    ensure_dir(output_path.parent)
    save_json(corpus_data, output_path)

def main():
    """
    Main entry point for data ingestion and preprocessing.
    """
    logger = get_logger(__name__)
    set_seed(42) # Deterministic behavior

    # 1. Download (if not exists)
    if not RAW_DATA_PATH.exists():
        logger.info("Raw dataset not found. Downloading...")
        download_arxiv_dataset()
    else:
        logger.info(f"Raw dataset found at {RAW_DATA_PATH}")

    # 2. Extract authors and check collisions
    author_counts = extract_authors_with_counts(RAW_DATA_PATH)
    collision_authors = log_author_collisions(author_counts)
    
    # 3. Generate collision report
    collision_report_path = PROCESSED_DATA_PATH / "collision_report.json"
    generate_collision_report(collision_authors, collision_report_path)
    
    # 4. Update state with collision status
    update_state_with_collision_status(collision_authors, STATE_FILE)

    # 5. Preprocess abstracts (T014 implementation)
    # This function handles:
    # - Filtering < 6 chars (FR-002 edge case)
    # - Lowercasing
    # - Removing punctuation
    # - Tokenization to character sequences
    logger.info("Starting preprocessing...")
    processed_corpus_path, author_dir = preprocess_abstracts(RAW_DATA_PATH, PROCESSED_DATA_PATH)
    
    # 6. Hash artifacts and update state
    corpus_hash = hash_artifact(processed_corpus_path)
    logger.info(f"Processed corpus hash: {corpus_hash}")
    
    state = load_state(STATE_FILE)
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    state["artifacts"]["processed_corpus"] = {
        "path": str(processed_corpus_path),
        "hash": corpus_hash,
        "type": "json"
    }
    save_state(state, STATE_FILE)
    logger.info("State updated with processed corpus hash.")

    logger.info("Data ingestion and preprocessing complete.")

if __name__ == "__main__":
    main()