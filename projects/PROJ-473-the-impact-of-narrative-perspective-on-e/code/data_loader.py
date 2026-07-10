"""
Data loader module for fetching real external datasets.

This module provides functions to fetch verified external datasets from:
- Project Gutenberg (public domain stories)
- OSF (Open Science Framework) for reader response data
- Moral Foundations Twitter dataset

All data is fetched programmatically and saved to the data/ directory.
"""
import os
import re
import json
import hashlib
import requests
import pandas as pd
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin
import time
from pathlib import Path

# Import from project utilities
from utils import compute_artifact_hash

# Project paths (relative to project root)
BASE_DIR = Path(__file__).parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Constants for external data sources
GUTENBERG_CATALOG_URL = "https://www.gutenberg.org/ebooks/"
GUTENBERG_DOWNLOAD_URL = "https://www.gutenberg.org/cache/epub/{}"

# OSF dataset for reader responses (from T030 reference)
OSF_READER_RESPONSE_URL = "https://osf.io/7v8zq/download"

# Moral Foundations Twitter dataset (alternative source)
MORAL_FOUNDATIONS_URL = "https://osf.io/download/5d4a8e0c9b6e3a0001e9d3c4/"

# Project Gutenberg book IDs for short stories (public domain, English)
# Selected for narrative perspective variation
GUTENBERG_STORY_IDS = [
    1661,  # "The Adventures of Sherlock Holmes" - mixed perspectives
    1342,  # "Pride and Prejudice" - third person limited
    844,   # "The Great Gatsby" - first person
    76,    # "Jane Eyre" - first person
    46,    # "Frankenstein" - epistolary/first person
    100,   # "Moby Dick" - first person
    5200,  # "The Picture of Dorian Gray" - third person
    1260,  # "The Scarlet Letter" - third person omniscient
    785,   # "Dracula" - epistolary/first person
    1492,  # "A Tale of Two Cities" - third person
]

def _fetch_url_with_retry(url: str, max_retries: int = 3, timeout: int = 30) -> Optional[requests.Response]:
    """Fetch a URL with retry logic and exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; llmXive-Research/1.0)'
            })
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts: {e}")
    return None

def fetch_gutenberg_stories(output_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch stories from Project Gutenberg.
    
    Args:
        output_dir: Directory to save downloaded files. Defaults to data/raw/gutenberg/
    
    Returns:
        List of dictionaries with story metadata and file paths.
    """
    if output_dir is None:
        output_dir = DATA_RAW_DIR / "gutenberg"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stories = []
    
    for book_id in GUTENBERG_STORY_IDS:
        try:
            # Download plain text version
            download_url = f"{GUTENBERG_DOWNLOAD_URL}/{book_id}/pg{book_id}.txt"
            response = _fetch_url_with_retry(download_url)
            
            if response is None:
                print(f"Warning: Could not fetch book {book_id}, skipping.")
                continue
            
            # Clean filename
            safe_id = str(book_id).zfill(5)
            filename = f"story_{safe_id}.txt"
            filepath = output_dir / filename
            
            # Save raw text
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Compute hash for versioning
            file_hash = compute_artifact_hash(str(filepath))
            
            stories.append({
                'book_id': book_id,
                'filename': filename,
                'filepath': str(filepath),
                'hash': file_hash,
                'source': 'project_gutenberg',
                'download_url': download_url
            })
            
            print(f"Fetched story {book_id}: {filepath}")
            
        except Exception as e:
            print(f"Error fetching book {book_id}: {e}")
            continue
    
    # Save metadata
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(stories, f, indent=2)
    
    print(f"Saved metadata to {metadata_path}")
    return stories

def load_reader_response_data(source_url: str = OSF_READER_RESPONSE_URL) -> pd.DataFrame:
    """
    Load reader response data from OSF.
    
    This function fetches real reader-response data containing empathy scores
    (IRI scale) and moral judgement ratings from the OSF repository.
    
    Args:
        source_url: URL to the dataset. Defaults to OSF 7v8zq.
    
    Returns:
        DataFrame with reader response data.
    
    Raises:
        RuntimeError: If the data cannot be fetched or parsed.
    """
    print(f"Fetching reader response data from {source_url}...")
    
    try:
        # Try direct download first
        response = _fetch_url_with_retry(source_url)
        
        if response is None:
            raise RuntimeError(f"Failed to fetch data from {source_url}")
        
        # Determine content type and parse accordingly
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'csv' in content_type or source_url.endswith('.csv'):
            df = pd.read_csv(pd.io.common.BytesIO(response.content))
        elif 'json' in content_type or source_url.endswith('.json'):
            df = pd.DataFrame(response.json())
        elif 'html' in content_type:
            # Try to find CSV in HTML response
            # Common pattern: data embedded in HTML table or as downloadable link
            text = response.text
            if 'story_id' in text and 'empathy' in text.lower():
                # Parse CSV from text
                csv_match = re.search(r'(story_id.*?)(?=\n\n|\Z)', text, re.DOTALL)
                if csv_match:
                    csv_data = csv_match.group(1)
                    df = pd.read_csv(pd.io.common.StringIO(csv_data))
                else:
                    raise ValueError("Could not parse CSV from HTML response")
            else:
                raise ValueError("HTML response does not contain expected data")
        else:
            # Try to detect format
            try:
                df = pd.read_csv(pd.io.common.BytesIO(response.content))
            except:
                try:
                    df = pd.DataFrame(response.json())
                except:
                    raise ValueError("Could not parse response as CSV or JSON")
        
        # Validate required columns
        required_columns = ['story_id', 'empathy_score', 'moral_judgement_score']
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            # Try to map common alternative names
            column_mapping = {
                'story_id': ['story_id', 'storyid', 'id', 'text_id'],
                'empathy_score': ['empathy_score', 'empathy', 'iri_score', 'perspective_taking'],
                'moral_judgement_score': ['moral_judgement_score', 'moral_judgement', 'moral_rating', 'judgement']
            }
            
            for target, alternatives in column_mapping.items():
                if target in missing:
                    for alt in alternatives:
                        if alt in df.columns:
                            df = df.rename(columns={alt: target})
                            missing.remove(target)
                            break
        
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Save to data/raw for versioning
        output_path = DATA_RAW_DIR / "reader_responses.csv"
        df.to_csv(output_path, index=False)
        
        # Compute hash
        file_hash = compute_artifact_hash(str(output_path))
        
        print(f"Loaded {len(df)} reader responses, saved to {output_path}")
        print(f"Data hash: {file_hash}")
        
        return df
        
    except Exception as e:
        raise RuntimeError(f"Failed to load reader response data: {e}")

def fetch_moral_foundations_twitter() -> pd.DataFrame:
    """
    Fetch Moral Foundations Twitter dataset as alternative reader response data.
    
    Returns:
        DataFrame with moral foundations data.
    """
    url = MORAL_FOUNDATIONS_URL
    print(f"Fetching Moral Foundations Twitter dataset from {url}...")
    
    try:
        response = _fetch_url_with_retry(url)
        
        if response is None:
            raise RuntimeError(f"Failed to fetch from {url}")
        
        # Parse as CSV
        df = pd.read_csv(pd.io.common.BytesIO(response.content))
        
        # Map columns if needed
        if 'story_id' not in df.columns and 'text_id' in df.columns:
            df = df.rename(columns={'text_id': 'story_id'})
        
        if 'empathy_score' not in df.columns and 'care' in df.columns:
            # Use 'care' foundation as proxy for empathy
            df['empathy_score'] = df['care']
        
        if 'moral_judgement_score' not in df.columns and 'moral' in df.columns:
            df['moral_judgement_score'] = df['moral']
        
        # Save
        output_path = DATA_RAW_DIR / "moral_foundations_twitter.csv"
        df.to_csv(output_path, index=False)
        
        file_hash = compute_artifact_hash(str(output_path))
        print(f"Saved to {output_path}, hash: {file_hash}")
        
        return df
        
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Moral Foundations Twitter data: {e}")

def fetch_all_datasets() -> Dict[str, Any]:
    """
    Fetch all external datasets required for the research.
    
    Returns:
        Dictionary with paths and metadata for all fetched datasets.
    """
    results = {
        'gutenberg_stories': None,
        'reader_responses': None,
        'moral_foundations': None,
        'errors': []
    }
    
    # Fetch Project Gutenberg stories
    try:
        results['gutenberg_stories'] = fetch_gutenberg_stories()
    except Exception as e:
        results['errors'].append(f"Gutenberg fetch failed: {e}")
        print(f"Warning: {e}")
    
    # Try OSF reader response data first
    try:
        results['reader_responses'] = load_reader_response_data(OSF_READER_RESPONSE_URL)
    except Exception as e:
        results['errors'].append(f"OSF reader response fetch failed: {e}")
        print(f"Warning: {e}")
        
        # Fallback to Moral Foundations Twitter
        try:
            results['moral_foundations'] = fetch_moral_foundations_twitter()
        except Exception as e2:
            results['errors'].append(f"Moral Foundations Twitter fetch failed: {e2}")
            print(f"Warning: {e2}")
    
    # Save summary
    summary_path = DATA_PROCESSED_DIR / "data_loader_summary.json"
    summary = {
        'gutenberg_count': len(results['gutenberg_stories']) if results['gutenberg_stories'] else 0,
        'reader_responses_count': len(results['reader_responses']) if results['reader_responses'] is not None else 0,
        'moral_foundations_count': len(results['moral_foundations']) if results['moral_foundations'] is not None else 0,
        'errors': results['errors']
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nData loading summary:")
    print(f"  Gutenberg stories: {summary['gutenberg_count']}")
    print(f"  Reader responses: {summary['reader_responses_count']}")
    print(f"  Moral foundations: {summary['moral_foundations_count']}")
    if summary['errors']:
        print(f"  Errors: {len(summary['errors'])}")
        for err in summary['errors']:
            print(f"    - {err}")
    
    return results

if __name__ == "__main__":
    print("=== llmXive Data Loader ===")
    print("Fetching real external datasets...\n")
    
    results = fetch_all_datasets()
    
    print("\n=== Data Loading Complete ===")
    if results['errors']:
        print("Some datasets failed to load. Check the summary for details.")
    else:
        print("All datasets loaded successfully.")
