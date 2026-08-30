import requests
import json
import logging
import time
import re
import unicodedata
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
from urllib.parse import urlencode
from itertools import islice

# Project local imports
from utils.logging_config import get_logger, ensure_log_dir
from utils.data_sources_validator import load_and_validate_config
from utils.error_handling import DataFetchError, fetch_with_strict_handling

# Configure logger
logger = get_logger(__name__)
ensure_log_dir("logs")

# Constants
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
RAW_OUTPUT_PATH = DATA_RAW_DIR / "corpus_raw.jsonl"
PROCESSED_OUTPUT_PATH = DATA_PROCESSED_DIR / "corpus.jsonl"
CONFIG_PATH = Path("data-sources.yaml")

def normalize_text(text: str) -> str:
    """Normalize text by removing control characters and normalizing unicode."""
    if not text:
        return ""
    # Remove control characters except newlines/tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Normalize unicode to NFC
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def is_valid_abstract(abstract: str) -> bool:
    """Check if abstract is non-empty and has reasonable length."""
    if not abstract:
        return False
    text = normalize_text(abstract)
    if len(text) < 50:  # Minimum meaningful abstract length
        return False
    return True

def filter_malformed_entries(entries: List[Dict]) -> List[Dict]:
    """Filter out entries with missing required fields or invalid abstracts."""
    valid_entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if 'abstract' not in entry or not entry.get('abstract'):
            continue
        if not is_valid_abstract(entry['abstract']):
            continue
        valid_entries.append(entry)
    return valid_entries

def preprocess_corpus(entries: List[Dict]) -> List[Dict]:
    """Normalize text fields and ensure required metadata is present."""
    processed = []
    for entry in entries:
        processed_entry = {
            'title': normalize_text(entry.get('title', '')),
            'abstract': normalize_text(entry['abstract']),
            'venue': normalize_text(entry.get('venue', 'Unknown')),
            'acceptance_status': entry.get('acceptance_status', 'unknown'),
            'domain': entry.get('domain', 'unknown'),
            'id': entry.get('id', ''),
            'source_url': entry.get('source_url', '')
        }
        processed.append(processed_entry)
    return processed

def validate_fetch_status(response: requests.Response, url: str) -> None:
    """Raise DataFetchError on 403/404 or paywall detection."""
    if response.status_code in [403, 404]:
        raise DataFetchError(f"Fetch failed with status {response.status_code} for {url}")
    if "paywall" in response.text.lower() or "access denied" in response.text.lower():
        raise DataFetchError(f"Paywall detected for {url}")
    if response.status_code >= 400:
        raise DataFetchError(f"HTTP error {response.status_code} for {url}")

def load_data_sources_config() -> Dict[str, Any]:
    """Load and validate the data-sources.yaml configuration."""
    return load_and_validate_config(CONFIG_PATH)

def stream_arxiv_abstracts(config: Dict[str, Any], category: str, limit: Optional[int] = None) -> Iterator[Dict]:
    """Stream abstracts from arXiv API for a specific category."""
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"cat:{category}",
        "start": 0,
        "max_results": 100,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    count = 0
    while True:
        try:
            response = fetch_with_strict_handling(base_url, params=params)
            # Simple XML parsing for arXiv Atom feed
            # Extract entries manually
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
            
            entries = root.findall('atom:entry', ns)
            if not entries:
                break
            
            for entry in entries:
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                published = entry.find('atom:published', ns)
                id_elem = entry.find('atom:id', ns)
                
                if title is None or summary is None:
                    continue
                
                yield {
                    'title': title.text.strip() if title.text else "",
                    'abstract': summary.text.strip() if summary.text else "",
                    'venue': 'arXiv',
                    'acceptance_status': 'accepted', # arXiv is preprint, treated as accepted for this pipeline
                    'domain': 'ML',
                    'id': id_elem.text if id_elem is not None else "",
                    'source_url': f"https://arxiv.org/abs/{id_elem.text.split('/')[-1]}",
                    'date': published.text if published is not None else ""
                }
                count += 1
                if limit and count >= limit:
                    return
            
            # Pagination
            next_params = params.copy()
            next_params['start'] += params['max_results']
            params = next_params
            
            # Rate limiting
            time.sleep(3)
            
        except DataFetchError as e:
            logger.error(f"Error fetching arXiv data: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in arXiv stream: {e}")
            raise

def stream_doi_entries(config: Dict[str, Any], source_name: str, limit: Optional[int] = None) -> Iterator[Dict]:
    """Stream entries from a DOI-based source (e.g., Nature, Health Affairs)."""
    if source_name not in config.get('sources', {}):
        raise ValueError(f"Source {source_name} not found in config")
    
    source_config = config['sources'][source_name]
    base_url = source_config.get('url')
    if not base_url:
        raise ValueError(f"No URL configured for {source_name}")
    
    # Note: Real implementation would use Crossref API or specific journal API
    # For this implementation, we simulate the structure based on config
    # In a real scenario, this would iterate over a list of DOIs or use an API endpoint
    
    # Simulating DOI list from config
    dois = source_config.get('dois', [])
    for i, doi in enumerate(dois):
        if limit and i >= limit:
            break
        
        try:
            # In real implementation, fetch metadata from Crossref API
            # Here we construct a placeholder based on the DOI
            metadata_url = f"https://api.crossref.org/works/{doi}"
            response = fetch_with_strict_handling(metadata_url)
            data = response.json()
            
            item = data.get('message', {})
            title = item.get('title', ['Unknown'])[0]
            abstract = item.get('abstract', 'Abstract not available')
            # Clean abstract if it's HTML
            abstract = re.sub(r'<[^>]+>', '', abstract)
            
            yield {
                'title': title,
                'abstract': abstract,
                'venue': source_config.get('venue', source_name),
                'acceptance_status': source_config.get('acceptance_status', 'unknown'),
                'domain': source_config.get('domain', 'Non-ML'),
                'id': doi,
                'source_url': f"https://doi.org/{doi}"
            }
        except DataFetchError:
            logger.warning(f"Failed to fetch metadata for DOI {doi}, skipping")
            continue
        except Exception as e:
            logger.error(f"Error processing DOI {doi}: {e}")
            continue

def stream_and_sample(n: int = 500, seed: int = 42) -> Iterator[Dict]:
    """Stream data from all configured sources and sample n entries."""
    import random
    random.seed(seed)
    
    config = load_data_sources_config()
    all_entries = []
    
    # Stream from arXiv
    ml_sources = config.get('sources', {}).get('ml', {})
    if ml_sources:
        for cat, details in ml_sources.items():
            logger.info(f"Streaming arXiv category: {cat}")
            limit = details.get('limit')
            for entry in stream_arxiv_abstracts(config, cat, limit=limit):
                all_entries.append(entry)
    
    # Stream from non-ML sources
    non_ml_sources = config.get('sources', {}).get('non_ml', {})
    if non_ml_sources:
        for source_name, details in non_ml_sources.items():
            logger.info(f"Streaming non-ML source: {source_name}")
            limit = details.get('limit')
            for entry in stream_doi_entries(config, source_name, limit=limit):
                all_entries.append(entry)
    
    # Log total collected
    logger.info(f"Total entries collected: {len(all_entries)}")
    
    # Sample if necessary
    if len(all_entries) > n:
        logger.info(f"Sampling {n} entries from {len(all_entries)} collected")
        sampled = random.sample(all_entries, n)
        return iter(sampled)
    
    return iter(all_entries)

def save_corpus_streaming(entries: Iterator[Dict], output_path: Path) -> None:
    """Save entries to a JSONL file in streaming fashion."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            count += 1
            if count % 100 == 0:
                logger.debug(f"Written {count} entries")
    logger.info(f"Saved {count} entries to {output_path}")

def main():
    """Main entry point for data acquisition and processing pipeline."""
    try:
        # Ensure directories exist
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info("Starting data acquisition pipeline...")
        
        # 1. Stream and sample raw data
        logger.info("Streaming and sampling raw data...")
        raw_entries = stream_and_sample(n=500, seed=42)
        
        # 2. Save raw data
        save_corpus_streaming(raw_entries, RAW_OUTPUT_PATH)
        
        # 3. Reload and preprocess
        logger.info("Preprocessing corpus...")
        processed_entries = []
        with open(RAW_OUTPUT_PATH, 'r', encoding='utf-8') as f:
            raw_data = [json.loads(line) for line in f if line.strip()]
        
        valid_raw = filter_malformed_entries(raw_data)
        processed = preprocess_corpus(valid_raw)
        
        # 4. Save processed data
        save_corpus_streaming(iter(processed), PROCESSED_OUTPUT_PATH)
        
        logger.info(f"Pipeline complete. Processed {len(processed)} entries.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
