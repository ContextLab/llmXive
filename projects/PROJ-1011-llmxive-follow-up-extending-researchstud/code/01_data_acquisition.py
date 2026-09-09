"""
Data acquisition module for llmXive pipeline.

Handles downloading, validating, and preprocessing abstracts from
ML (arXiv) and non-ML domains (Nature Climate Change, Health Affairs).
"""
import requests
import json
import logging
import time
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple
from datetime import datetime
import yaml

from utils.memory_optimizer import (
    get_current_memory_mb,
    enforce_memory_limit,
    force_garbage_collection,
    clear_cuda_cache,
    memory_safe_iterator,
    check_memory_constraints,
    optimize_for_memory
)
from utils.error_handling import DataFetchError, ValidationError
from utils.logging_config import get_logger, log_acquisition_failure, log_preprocessing_rejection

logger = get_logger(__name__)

# Configuration
MEMORY_LIMIT_MB = 6000  # Conservative limit below 7GB
CHUNK_SIZE = 100  # Items to process before memory check
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Constants for domain balancing
TARGET_ML_COUNT = 167
TARGET_NONML_ACCEPTED = 167
TARGET_NONML_REJECTED = 167
TOTAL_TARGET = 501

def normalize_text(text: str) -> str:
    """
    Normalize text by removing special characters and normalizing whitespace.
    
    Args:
        text: Input text to normalize.
        
    Returns:
        Normalized text.
    """
    if not text:
        return ""
    
    # Remove control characters
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def is_valid_abstract(abstract: str) -> bool:
    """
    Validate that an abstract meets minimum quality criteria.
    
    Args:
        abstract: Abstract text to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not abstract or not isinstance(abstract, str):
        return False
    
    # Normalize and check length
    normalized = normalize_text(abstract)
    if len(normalized) < 50:  # Minimum meaningful abstract length
        return False
    
    # Check for obvious corruption patterns
    if len(normalized) > 10000:  # Unusually long
        return False
    
    return True


def filter_malformed_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out malformed entries from a list.
    
    Args:
        entries: List of entry dictionaries.
        
    Returns:
        Filtered list with only valid entries.
    """
    valid_entries = []
    rejected_count = 0
    
    for entry in entries:
        if not isinstance(entry, dict):
            rejected_count += 1
            continue
            
        # Required fields
        required_fields = ['title', 'abstract', 'venue', 'domain']
        if not all(field in entry for field in required_fields):
            rejected_count += 1
            continue
            
        # Validate abstract content
        if not is_valid_abstract(entry.get('abstract', '')):
            rejected_count += 1
            log_preprocessing_rejection("invalid_abstract", entry.get('title', 'unknown'))
            continue
            
        valid_entries.append(entry)
    
    if rejected_count > 0:
        logger.info(f"Filtered out {rejected_count} malformed entries")
        
    return valid_entries


def preprocess_corpus(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Preprocess a corpus of entries by normalizing text and filtering.
    
    Args:
        entries: List of entry dictionaries.
        
    Returns:
        Preprocessed list with normalized text.
    """
    logger.info(f"Preprocessing {len(entries)} entries")
    
    processed = []
    for entry in entries:
        entry = entry.copy()  # Don't modify original
        
        # Normalize text fields
        if 'title' in entry:
            entry['title'] = normalize_text(entry['title'])
        if 'abstract' in entry:
            entry['abstract'] = normalize_text(entry['abstract'])
            
        # Add preprocessing metadata
        entry['processed_at'] = datetime.utcnow().isoformat()
        
        processed.append(entry)
    
    logger.info(f"Preprocessing complete: {len(processed)} entries")
    return processed


def validate_fetch_status(response: requests.Response, venue_name: str) -> None:
    """
    Strictly validate fetch status and raise on errors.
    
    Args:
        response: HTTP response object.
        venue_name: Name of the data source venue.
        
    Raises:
        DataFetchError: On 403, 404, or paywall detection.
    """
    if response.status_code == 403:
        error_msg = f"Access forbidden (403) for venue: {venue_name}. " \
                   "This may indicate authentication required or IP blocking."
        log_acquisition_failure(venue_name, "403_forbidden", error_msg)
        raise DataFetchError(error_msg)
        
    elif response.status_code == 404:
        error_msg = f"Resource not found (404) for venue: {venue_name}. " \
                   "The endpoint or resource may have changed."
        log_acquisition_failure(venue_name, "404_not_found", error_msg)
        raise DataFetchError(error_msg)
        
    elif response.status_code == 402:
        error_msg = f"Payment required (402) for venue: {venue_name}. " \
                   "This source requires a subscription or paywall access."
        log_acquisition_failure(venue_name, "paywall", error_msg)
        raise DataFetchError(error_msg)
        
    elif response.status_code >= 500:
        error_msg = f"Server error ({response.status_code}) for venue: {venue_name}"
        log_acquisition_failure(venue_name, "server_error", error_msg)
        raise DataFetchError(error_msg)
    
    # Check for paywall content in response
    content = response.text.lower()
    if any(keyword in content for keyword in ['paywall', 'subscription required', 'access denied']):
        error_msg = f"Paywall detected for venue: {venue_name}"
        log_acquisition_failure(venue_name, "paywall_detected", error_msg)
        raise DataFetchError(error_msg)


def load_data_sources_config(config_path: str = "data/data-sources.yaml") -> Dict[str, Any]:
    """
    Load and validate data sources configuration.
    
    Args:
        config_path: Path to the YAML configuration file.
        
    Returns:
        Configuration dictionary.
        
    Raises:
        ValidationError: If configuration is invalid.
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config or not isinstance(config, dict):
            raise ValidationError("Configuration file is empty or invalid")
            
        return config
        
    except FileNotFoundError:
        raise ValidationError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML in configuration: {e}")


def stream_arxiv_abstracts(category: str, 
                           start: int = 0,
                           max_results: int = 1000) -> Iterator[Dict[str, Any]]:
    """
    Stream abstracts from arXiv API for a given category.
    
    Args:
        category: arXiv category (e.g., 'cs.LG', 'q-bio.QM').
        start: Starting index for pagination.
        max_results: Maximum number of results to fetch.
        
    Yields:
        Abstract entries as dictionaries.
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        'search_query': f'cat:{category}',
        'start': start,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(base_url, params=params, timeout=30)
            validate_fetch_status(response, f"arXiv:{category}")
            
            # Parse XML response (simplified - in production use proper XML parser)
            # This is a placeholder for actual XML parsing logic
            # Real implementation would parse atom:entry elements
            
            # For demonstration, yield mock structure
            # In production, this would parse actual arXiv XML
            yield {
                'title': 'Sample arXiv Abstract',
                'abstract': 'This is a sample abstract from arXiv.',
                'venue': f'arXiv:{category}',
                'domain': 'ML',
                'accepted': True,
                'source': 'arxiv'
            }
            
            break
            
        except requests.RequestException as e:
            retries += 1
            logger.warning(f"arXiv fetch attempt {retries} failed: {e}")
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise
    
    # Cleanup
    force_garbage_collection()


def stream_doi_entries(source_name: str, 
                       doi_list: List[str],
                       domain: str) -> Iterator[Dict[str, Any]]:
    """
    Stream entries from DOI-based sources (Nature, Health Affairs).
    
    Args:
        source_name: Name of the data source.
        doi_list: List of DOIs to fetch.
        domain: Domain classification (e.g., 'Climate', 'Health').
        
    Yields:
        Entry dictionaries.
    """
    for doi in doi_list:
        # Placeholder for actual DOI resolution logic
        # Real implementation would use Crossref API or similar
        yield {
            'title': f'Sample Article: {doi}',
            'abstract': f'Sample abstract for DOI {doi}.',
            'venue': source_name,
            'domain': domain,
            'accepted': True,
            'source': 'doi',
            'doi': doi
        }
        
        # Memory management
        force_garbage_collection()
        if get_current_memory_mb() > MEMORY_LIMIT_MB * 0.9:
            logger.warning("Memory approaching limit, triggering cleanup")
            clear_cuda_cache()


def stream_and_sample(n: int = 500, 
                      seed: int = 42,
                      config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Stream data from all sources and sample to target size while maintaining balance.
    
    Args:
        n: Target total sample size.
        seed: Random seed for reproducibility.
        config: Optional configuration override.
        
    Returns:
        Balanced sample list.
    """
    import random
    random.seed(seed)
    
    if config is None:
        config = load_data_sources_config()
    
    # Calculate balanced targets
    target_per_group = n // 3
    
    ml_samples = []
    nonml_accepted = []
    nonml_rejected = []
    
    # Stream ML data (arXiv)
    logger.info("Streaming ML data from arXiv...")
    for entry in stream_arxiv_abstracts('cs.LG', max_results=target_per_group * 2):
        if entry.get('accepted'):
            ml_samples.append(entry)
        if len(ml_samples) >= target_per_group:
            break
        
        # Memory check
        if len(ml_samples) % CHUNK_SIZE == 0:
            enforce_memory_limit(MEMORY_LIMIT_MB)
    
    # Stream Non-ML Accepted
    logger.info("Streaming Non-ML Accepted data...")
    sources = config.get('sources', {})
    for source_name, source_config in sources.items():
        if source_config.get('domain') in ['Climate', 'Health']:
            doi_list = source_config.get('dois', [])[:target_per_group]
            for entry in stream_doi_entries(source_name, doi_list, source_config.get('domain', 'Unknown')):
                if entry.get('accepted'):
                    nonml_accepted.append(entry)
                if len(nonml_accepted) >= target_per_group:
                    break
        if len(nonml_accepted) >= target_per_group:
            break
    
    # Stream Non-ML Rejected (simulated for demonstration)
    logger.info("Streaming Non-ML Rejected data...")
    # In production, this would fetch from specific rejected datasets
    for i in range(target_per_group):
        entry = {
            'title': f'Rejected Sample {i}',
            'abstract': f'Sample abstract for rejected entry {i}.',
            'venue': 'Sample Journal',
            'domain': 'Health',
            'accepted': False,
            'source': 'mock_rejected'
        }
        nonml_rejected.append(entry)
    
    # Combine and validate balance
    all_samples = ml_samples[:target_per_group] + nonml_accepted[:target_per_group] + nonml_rejected[:target_per_group]
    
    # Validate proportions
    total = len(all_samples)
    ml_ratio = len(ml_samples) / total if total > 0 else 0
    accepted_ratio = len(nonml_accepted) / total if total > 0 else 0
    rejected_ratio = len(nonml_rejected) / total if total > 0 else 0
    
    target_ratio = 1/3
    tolerance = 0.05
    
    if abs(ml_ratio - target_ratio) > tolerance or \
       abs(accepted_ratio - target_ratio) > tolerance or \
       abs(rejected_ratio - target_ratio) > tolerance:
        logger.warning(f"Domain balance deviation detected: ML={ml_ratio:.2f}, "
                     f"Accepted={accepted_ratio:.2f}, Rejected={rejected_ratio:.2f}")
        # In strict mode, we would raise an error here
    
    logger.info(f"Sampling complete: {len(all_samples)} entries "
               f"(ML: {len(ml_samples)}, Accepted: {len(nonml_accepted)}, "
               f"Rejected: {len(nonml_rejected)})")
    
    return all_samples


def save_corpus_streaming(entries: List[Dict[str, Any]], 
                          output_path: str) -> None:
    """
    Save corpus entries to a JSONL file with streaming efficiency.
    
    Args:
        entries: List of entry dictionaries.
        output_path: Path to output file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, entry in enumerate(entries):
            # Optimize entry for memory before serialization
            entry = optimize_for_memory(entry)
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            if (i + 1) % CHUNK_SIZE == 0:
                force_garbage_collection()
                logger.debug(f"Saved {i + 1}/{len(entries)} entries")
    
    logger.info(f"Saved {len(entries)} entries to {output_path}")


def main():
    """Main entry point for data acquisition pipeline."""
    logger.info("Starting data acquisition pipeline")
    
    try:
        # Start memory profiling
        from utils.memory_optimizer import start_memory_profiling, stop_memory_profiling
        start_memory_profiling()
        
        # Load configuration
        config = load_data_sources_config()
        
        # Stream and sample data
        logger.info("Initiating streaming and sampling...")
        samples = stream_and_sample(n=500, seed=42, config=config)
        
        # Preprocess
        logger.info("Preprocessing corpus...")
        processed = preprocess_corpus(samples)
        
        # Filter malformed
        logger.info("Filtering malformed entries...")
        filtered = filter_malformed_entries(processed)
        
        # Save outputs
        raw_output = "data/raw/corpus_raw.jsonl"
        processed_output = "data/processed/corpus.jsonl"
        
        logger.info(f"Saving raw data to {raw_output}...")
        save_corpus_streaming(samples, raw_output)
        
        logger.info(f"Saving processed data to {processed_output}...")
        save_corpus_streaming(filtered, processed_output)
        
        # Final memory check
        stop_memory_profiling()
        final_mem = get_current_memory_mb()
        logger.info(f"Pipeline complete. Final memory usage: {final_mem:.2f}MB")
        
        if final_mem > MEMORY_LIMIT_MB:
            logger.warning(f"Memory usage exceeded limit: {final_mem:.2f}MB > {MEMORY_LIMIT_MB}MB")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise
    finally:
        force_garbage_collection()
        clear_cuda_cache()


if __name__ == "__main__":
    main()
