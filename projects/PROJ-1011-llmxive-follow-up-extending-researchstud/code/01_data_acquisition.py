"""
Data Acquisition Module for llmXive Research Studio.
Handles downloading, validation, and preprocessing of research abstracts.
"""

import requests
import json
import logging
import time
import re
import unicodedata
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple
from datetime import datetime

# Import project utilities
# Note: Importing from utils.logging_config to ensure logging is configured correctly
# and to avoid circular imports, we configure the logger here using the helper.
from utils.logging_config import get_logger, log_acquisition_failure
from utils.error_handling import DataFetchError, validate_data_response
from utils.config import set_seed

# Constants
ARXIV_API_BASE = "http://export.arxiv.org/api/query"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
DEFAULT_ENCODING = 'utf-8'

# Logger instance
logger = get_logger(__name__)

def load_data_sources_config(config_path: str = "data-sources.yaml") -> Dict[str, Any]:
    """Load data source configuration from YAML file."""
    import yaml
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, 'r', encoding=DEFAULT_ENCODING) as f:
        config = yaml.safe_load(f)
    
    if not config or 'sources' not in config:
        raise ValueError("Invalid configuration: missing 'sources' key")
    
    return config

def normalize_text(text: str) -> str:
    """Normalize text by removing non-ASCII characters and extra whitespace."""
    if not text:
        return ""
    
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Remove non-ASCII characters but keep basic punctuation
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def is_valid_abstract(abstract: str) -> bool:
    """Check if an abstract is valid (non-empty and reasonable length)."""
    if not abstract or not isinstance(abstract, str):
        return False
    
    normalized = normalize_text(abstract)
    if len(normalized) < 50:  # Minimum length check
        return False
    
    if len(normalized) > 50000:  # Maximum length check
        return False
    
    return True

def filter_malformed_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out malformed entries from the corpus."""
    valid_entries = []
    malformed_count = 0
    
    for entry in entries:
        if not isinstance(entry, dict):
            malformed_count += 1
            continue
        
        # Check required fields
        if 'title' not in entry or 'abstract' not in entry:
            malformed_count += 1
            continue
        
        # Validate abstract content
        if not is_valid_abstract(entry.get('abstract', '')):
            malformed_count += 1
            continue
        
        valid_entries.append(entry)
    
    if malformed_count > 0:
        logger.warning(f"Filtered out {malformed_count} malformed entries")
    
    return valid_entries

def validate_fetch_status(response: requests.Response, source_name: str) -> None:
    """
    Strict validation of fetch status. Raises DataFetchError on failure.
    Fails loudly on 403, 404, or paywall detection.
    """
    # Check HTTP status
    if response.status_code == 403:
        msg = f"Access forbidden (403) for source '{source_name}'. API key may be missing or invalid."
        logger.error(msg)
        raise DataFetchError(msg)
    
    if response.status_code == 404:
        msg = f"Resource not found (404) for source '{source_name}'. Check the URL configuration."
        logger.error(msg)
        raise DataFetchError(msg)
    
    if response.status_code >= 500:
        msg = f"Server error ({response.status_code}) for source '{source_name}'. Please try again later."
        logger.error(msg)
        raise DataFetchError(msg)
    
    # Check for paywall indicators in content
    content_lower = response.text.lower()
    paywall_indicators = [
        "access denied", "login required", "paywall", 
        "subscription required", "premium content", "sign in"
    ]
    
    for indicator in paywall_indicators:
        if indicator in content_lower:
            msg = f"Paywall detected for source '{source_name}'. Content is not publicly accessible."
            logger.error(msg)
            raise DataFetchError(msg)
    
    # Check content type
    content_type = response.headers.get('content-type', '').lower()
    if 'text/html' in content_type and source_name not in ['arxiv', 'general']:
        # Some APIs return HTML on error
        if response.status_code == 200:
            # Double check if it looks like an error page
            if 'error' in content_lower or 'not found' in content_lower:
                msg = f"Unexpected HTML response for source '{source_name}'. Possible error page."
                logger.error(msg)
                raise DataFetchError(msg)

def stream_arxiv_abstracts(category: str, max_results: int = 1000, start: int = 0) -> Iterator[Dict[str, Any]]:
    """
    Stream abstracts from arXiv API for a specific category.
    Handles pagination and rate limiting.
    """
    params = {
        'search_query': f'cat:{category}',
        'start': start,
        'max_results': 50,  # arXiv max per request
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    count = 0
    retries = 0
    
    while count < max_results:
        try:
            response = requests.get(ARXIV_API_BASE, params=params, timeout=30)
            
            # Validate response
            validate_fetch_status(response, f"arXiv:{category}")
            
            # Parse XML response (arXiv uses Atom feed)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            entries = root.findall('atom:entry', namespaces)
            
            if not entries:
                logger.info(f"No more entries found for category {category}")
                break
            
            for entry in entries:
                if count >= max_results:
                    return
                
                # Extract fields
                title = entry.find('atom:title', namespaces)
                abstract = entry.find('atom:summary', namespaces)
                published = entry.find('atom:published', namespaces)
                authors = entry.findall('atom:author/atom:name', namespaces)
                categories = entry.findall('atom:category', namespaces)
                
                if title is None or abstract is None:
                    continue
                
                # Clean text
                title_text = normalize_text(title.text) if title.text else ""
                abstract_text = normalize_text(abstract.text) if abstract.text else ""
                
                # Extract categories
                category_list = [cat.get('term') for cat in categories if cat.get('term')]
                
                record = {
                    'id': entry.find('atom:id', namespaces).text if entry.find('atom:id', namespaces) else "",
                    'title': title_text,
                    'abstract': abstract_text,
                    'published': published.text if published is not None else "",
                    'authors': [a.text for a in authors if a.text],
                    'categories': category_list,
                    'source': f"arXiv:{category}",
                    'acceptance_status': 'accepted',  # arXiv is preprint, but we treat as accepted for this pipeline
                    'domain': 'ML' if 'cs.LG' in category_list or 'stat.ML' in category_list else 'Other'
                }
                
                yield record
                count += 1
            
            # Update start for next page
            start += 50
            params['start'] = start
            
            # Rate limiting
            time.sleep(3)
            
        except requests.exceptions.RequestException as e:
            retries += 1
            if retries >= MAX_RETRIES:
                msg = f"Failed to fetch from arXiv after {MAX_RETRIES} retries: {str(e)}"
                log_acquisition_failure(msg, f"arXiv:{category}")
                raise DataFetchError(msg)
            logger.warning(f"Request failed, retrying ({retries}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
        except ET.ParseError as e:
            msg = f"Failed to parse arXiv response: {str(e)}"
            log_acquisition_failure(msg, f"arXiv:{category}")
            raise DataFetchError(msg)

def stream_doi_entries(source_config: Dict[str, Any], max_results: int = 100) -> Iterator[Dict[str, Any]]:
    """
    Stream entries from DOI-based sources (e.g., Nature, Health Affairs).
    This is a placeholder for actual API integration which would vary by publisher.
    For this implementation, we simulate the structure based on the config.
    """
    source_name = source_config.get('name', 'unknown')
    base_url = source_config.get('url', '')
    
    if not base_url:
        msg = f"No URL configured for source '{source_name}'"
        log_acquisition_failure(msg, source_name)
        raise DataFetchError(msg)
    
    # Note: In a real implementation, this would make API calls to the specific publisher.
    # Since many academic publishers require authentication or have complex APIs,
    # we implement the structure here but note that actual data fetching depends on
    # specific API keys and endpoints configured in data-sources.yaml.
    
    # For this task, we assume the data is already fetched or we have a mock endpoint
    # that returns structured data. In production, this would be replaced with real API logic.
    
    # Example structure for a DOI lookup (would need real API integration)
    # This is a skeleton to show the intended flow
    
    count = 0
    # In a real scenario, we would paginate through results
    # For now, we yield an empty iterator to indicate no data available without proper API setup
    # This prevents fabrication while maintaining the code structure
    logger.info(f"Stream configured for {source_name} but requires API authentication to fetch data.")
    
    # If a test endpoint is provided in config, try to use it
    test_endpoint = source_config.get('test_endpoint')
    if test_endpoint:
        try:
            response = requests.get(test_endpoint, timeout=10)
            validate_fetch_status(response, source_name)
            data = response.json()
            
            for item in data.get('results', [])[:max_results]:
                if count >= max_results:
                    break
                
                record = {
                    'id': item.get('doi', item.get('id', '')),
                    'title': item.get('title', ''),
                    'abstract': item.get('abstract', ''),
                    'published': item.get('published', ''),
                    'authors': item.get('authors', []),
                    'categories': item.get('categories', []),
                    'source': source_name,
                    'acceptance_status': item.get('status', 'accepted'),
                    'domain': item.get('domain', 'Other')
                }
                
                if is_valid_abstract(record['abstract']):
                    yield record
                    count += 1
        except Exception as e:
            logger.warning(f"Could not fetch from test endpoint for {source_name}: {e}")
            # Fail loudly as per requirements if real data cannot be fetched
            # Do not fall back to synthetic data
            raise DataFetchError(f"Failed to fetch data from {source_name}: {str(e)}")

def stream_and_sample(
    config: Dict[str, Any],
    target_ml: int = 50,
    target_non_ml_accepted: int = 50,
    target_non_ml_rejected: int = 50,
    seed: int = 42
) -> Iterator[Dict[str, Any]]:
    """
    Stream data from multiple sources and sample to achieve balance.
    Stops when targets are met or sources are exhausted.
    """
    set_seed(seed)
    
    ml_count = 0
    non_ml_accepted_count = 0
    non_ml_rejected_count = 0
    
    sources = config.get('sources', {})
    
    # Process ML sources (arXiv)
    if 'ml_sources' in sources:
        for source_name, source_config in sources['ml_sources'].items():
            category = source_config.get('category', 'cs.LG')
            for record in stream_arxiv_abstracts(category, max_results=target_ml * 2):
                if ml_count >= target_ml:
                    break
                yield record
                ml_count += 1
            
            if ml_count >= target_ml:
                break
    
    # Process Non-ML Accepted sources
    if 'non_ml_accepted_sources' in sources:
        for source_name, source_config in sources['non_ml_accepted_sources'].items():
            for record in stream_doi_entries(source_config, max_results=target_non_ml_accepted * 2):
                if non_ml_accepted_count >= target_non_ml_accepted:
                    break
                yield record
                non_ml_accepted_count += 1
            
            if non_ml_accepted_count >= target_non_ml_accepted:
                break
    
    # Process Non-ML Rejected sources (if available)
    if 'non_ml_rejected_sources' in sources:
        for source_name, source_config in sources['non_ml_rejected_sources'].items():
            for record in stream_doi_entries(source_config, max_results=target_non_ml_rejected * 2):
                if non_ml_rejected_count >= target_non_ml_rejected:
                    break
                yield record
                non_ml_rejected_count += 1
            
            if non_ml_rejected_count >= target_non_ml_rejected:
                break
    
    # Check balance
    total = ml_count + non_ml_accepted_count + non_ml_rejected_count
    if total > 0:
        logger.info(f"Sampled {ml_count} ML, {non_ml_accepted_count} Non-ML Accepted, {non_ml_rejected_count} Non-ML Rejected")
        
        # Validate balance (within 10% of target)
        target = max(target_ml, target_non_ml_accepted, target_non_ml_rejected)
        tolerance = target * 0.1
        
        if (abs(ml_count - target) > tolerance or 
            abs(non_ml_accepted_count - target) > tolerance or 
            abs(non_ml_rejected_count - target) > tolerance):
            logger.warning("Sample balance deviates from target. Consider adjusting sources.")

def extract_until(
    source: Iterator[Dict[str, Any]],
    target: int = 50,
    unique_field: str = 'abstract',
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Extract records until a target number of unique problem statements are found.
    Uses cryptographic hash for uniqueness detection.
    """
    import hashlib
    set_seed(seed)
    
    seen_hashes = set()
    result = []
    ml_count = 0
    non_ml_rejected_count = 0
    
    for record in source:
        # Calculate hash of the unique field
        content = record.get(unique_field, '')
        if not content:
            continue
        
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        if content_hash in seen_hashes:
            continue
        
        seen_hashes.add(content_hash)
        result.append(record)
        
        # Track counts for balance check
        domain = record.get('domain', '')
        status = record.get('acceptance_status', '')
        
        if 'ML' in domain or 'cs.LG' in str(record.get('categories', [])):
            ml_count += 1
        elif status == 'rejected':
            non_ml_rejected_count += 1
        
        # Check if we have enough unique non-ML statements
        non_ml_count = len(result) - ml_count - non_ml_rejected_count
        if non_ml_count >= target:
            # Validate balance
            target_ml = target
            target_rejected = target
            
            # Allow 10% deviation
            if ml_count < target_ml * 0.9 or non_ml_rejected_count < target_rejected * 0.9:
                raise BalanceError(
                    f"Balance check failed: ML={ml_count}, Rejected={non_ml_rejected_count}, "
                    f"Non-ML Unique={non_ml_count}. Expected ~{target} in each category."
                )
            break
    
    if len(result) < target:
        logger.warning(f"Could not reach target of {target} unique statements. Got {len(result)}.")
    
    return result

class BalanceError(Exception):
    """Raised when the extracted sample is not balanced according to requirements."""
    pass

def preprocess_corpus(corpus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Preprocess the corpus: normalize text, filter malformed entries."""
    return filter_malformed_entries(corpus)

def save_corpus_streaming(records: Iterator[Dict[str, Any]], output_path: str) -> int:
    """
    Save records to a JSONL file in streaming fashion.
    Returns the number of records written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    with open(output_path, 'w', encoding=DEFAULT_ENCODING) as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            count += 1
            
            # Log progress every 100 records
            if count % 100 == 0:
                logger.info(f"Wrote {count} records to {output_path}")
    
    logger.info(f"Successfully wrote {count} records to {output_path}")
    return count

def main():
    """Main entry point for data acquisition pipeline."""
    logger.info("Starting data acquisition pipeline...")
    
    try:
        # Load configuration
        config = load_data_sources_config()
        
        # Create output directory
        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "corpus_raw.jsonl"
        
        # Stream and sample data
        logger.info("Fetching and sampling data...")
        records = stream_and_sample(
            config,
            target_ml=50,
            target_non_ml_accepted=50,
            target_non_ml_rejected=50,
            seed=42
        )
        
        # Preprocess and save
        logger.info("Preprocessing and saving corpus...")
        count = save_corpus_streaming(records, str(output_file))
        
        logger.info(f"Pipeline completed. Total records: {count}")
        
        # Verify output exists
        if not output_file.exists():
            raise RuntimeError(f"Output file not created: {output_file}")
        
        return count
        
    except DataFetchError as e:
        logger.error(f"Data fetch failed: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in pipeline: {e}")
        raise

if __name__ == "__main__":
    main()