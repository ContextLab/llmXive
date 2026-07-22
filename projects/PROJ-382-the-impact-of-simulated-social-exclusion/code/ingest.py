import json
import logging
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
import pandas as pd
from requests.exceptions import RequestException, Timeout

from config import get_config
from logging_config import get_project_logger
from network_utils import retry_request, download_file_with_error_handling, IngestionError

logger = get_project_logger(__name__)

# OSF API Search Endpoint
OSF_SEARCH_URL = "https://api.osf.io/v2/search/nodes/"
OSF_FILES_URL = "https://api.osf.io/v2/files/"

def calculate_checksum(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def validate_schema(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """Check if DataFrame contains required columns."""
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map variant column names to standard schema."""
    # Column mapping for prosocial amount
    amount_map = {
        'donation': 'prosocial_amount',
        'allocation': 'prosocial_amount',
        'transfer': 'prosocial_amount',
        'prosocial_amount': 'prosocial_amount'
    }
    
    # Normalize condition column
    condition_map = {
        'ignored': 1,
        'excluded': 1,
        'control': 0,
        'baseline': 0
    }

    # Standardize column names
    cols_to_rename = {}
    for col in df.columns:
        lower_col = col.lower()
        if lower_col in amount_map:
            cols_to_rename[col] = amount_map[lower_col]
    
    if cols_to_rename:
        df = df.rename(columns=cols_to_rename)
    
    # Ensure required columns exist
    if 'condition' not in df.columns and 'prosocial_amount' in df.columns:
        # If condition is missing but we have amount, assume binary condition
        # This is a heuristic; real data should have condition
        pass

    return df

def search_osf_datasets(keywords: List[str], page_size: int = 20) -> List[Dict[str, Any]]:
    """
    Perform a keyword-based search on OSF for datasets.
    
    Args:
        keywords: List of keywords to search for (e.g., ["social exclusion", "prosocial"])
        page_size: Number of results per page
        
    Returns:
        List of dataset metadata dictionaries containing 'id', 'title', and 'files_url'
    """
    # Construct OSF search query
    # OSF search uses a specific query syntax
    query_parts = []
    for kw in keywords:
        # Search for exact phrase or individual words
        query_parts.append(f'"{kw}"')
    
    query_string = " AND ".join(query_parts)
    
    params = {
        "filter[public]": "true",
        "page[size]": page_size,
        "sort": "date_created",
        "q": query_string
    }
    
    datasets = []
    seen_ids = set()
    
    try:
        response = retry_request(
            "GET", 
            OSF_SEARCH_URL, 
            params=params, 
            timeout=30,
            max_retries=3
        )
        
        if response.status_code == 200:
            data = response.json()
            for node in data.get('data', []):
                node_id = node.get('id')
                if node_id and node_id not in seen_ids:
                    seen_ids.add(node_id)
                    # Extract file URL for this node
                    files_url = node.get('links', {}).get('files')
                    if files_url:
                        datasets.append({
                            'id': node_id,
                            'title': node.get('attributes', {}).get('title'),
                            'files_url': files_url
                        })
                        logger.info(f"Found potential dataset: {node.get('attributes', {}).get('title')}")
        else:
            logger.error(f"OSF search failed with status {response.status_code}")
            
    except RequestException as e:
        logger.error(f"Network error during OSF search: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during OSF search: {e}")
        
    return datasets

def get_dataset_files(files_url: str) -> List[Dict[str, Any]]:
    """
    Fetch list of files from an OSF project's files endpoint.
    
    Args:
        files_url: The files API URL for the project
        
    Returns:
        List of file metadata dictionaries
    """
    all_files = []
    next_url = files_url
    
    while next_url:
        try:
            response = retry_request("GET", next_url, timeout=30, max_retries=3)
            if response.status_code == 200:
                data = response.json()
                all_files.extend(data.get('data', []))
                next_url = data.get('links', {}).get('next')
            else:
                logger.warning(f"Failed to fetch files from {next_url}: {response.status_code}")
                break
        except RequestException as e:
            logger.error(f"Network error fetching files: {e}")
            break
        except Exception as e:
            logger.error(f"Error parsing file list: {e}")
            break
            
    return all_files

def find_csv_in_files(files: List[Dict[str, Any]]) -> Optional[str]:
    """
    Find the first CSV file in the list of files.
    
    Args:
        files: List of file metadata from OSF
        
    Returns:
        Direct download URL for the CSV file, or None if not found
    """
    for file_node in files:
        file_name = file_node.get('attributes', {}).get('name', '').lower()
        if file_name.endswith('.csv'):
            # Get the direct download link
            links = file_node.get('links', {})
            download_url = links.get('download')
            if download_url:
                return download_url
    return None

def download_dataset(url: Path, dest_path: Path) -> bool:
    """
    Download a dataset from a URL to a destination path.
    
    Args:
        url: Source URL (can be Path or str)
        dest_path: Destination file path
        
    Returns:
        True if download successful, False otherwise
    """
    return download_file_with_error_handling(str(url), dest_path)

def ingest_datasets(urls: List[str], output_dir: Path) -> Tuple[pd.DataFrame, int]:
    """
    Ingest datasets from a list of URLs.
    
    Args:
        urls: List of dataset URLs
        output_dir: Directory to store downloaded files
        
    Returns:
        Tuple of (combined DataFrame, count of valid datasets)
    """
    required_columns = ['condition', 'prosocial_amount', 'randomized']
    valid_datasets = []
    valid_count = 0
    
    for url in urls:
        try:
            # Download dataset
            filename = Path(url).name.split('?')[0]
            if not filename.endswith('.csv'):
                filename = f"dataset_{valid_count}.csv"
            
            dest_path = output_dir / filename
            
            if download_dataset(url, dest_path):
                # Load and validate
                df = pd.read_csv(dest_path)
                df = normalize_columns(df)
                
                is_valid, missing = validate_schema(df, required_columns)
                if is_valid:
                    valid_datasets.append(df)
                    valid_count += 1
                    logger.info(f"Successfully ingested dataset: {url}")
                else:
                    logger.warning(f"Dataset missing columns {missing}: {url}")
            else:
                logger.warning(f"Failed to download dataset: {url}")
                
        except Exception as e:
            logger.error(f"Error processing dataset {url}: {e}")
            
    if valid_datasets:
        combined = pd.concat(valid_datasets, ignore_index=True)
    else:
        combined = pd.DataFrame(columns=required_columns)
        
    return combined, valid_count

def perform_keyword_fallback(output_dir: Path, min_valid_datasets: int = 3) -> List[str]:
    """
    Perform keyword-based search on OSF if initial URL list yields fewer than 3 valid datasets.
    
    Args:
        output_dir: Directory to store downloaded files
        min_valid_datasets: Minimum number of valid datasets required
        
    Returns:
        List of URLs that yielded valid datasets
    """
    # Initial ingestion from config URLs
    config = get_config()
    initial_urls = config.get('osf_urls', [])
    
    # Try initial URLs first
    valid_urls = []
    if initial_urls:
        _, valid_count = ingest_datasets(initial_urls, output_dir)
        valid_urls = [url for url in initial_urls]  # Simplified: assume all initial are valid if count > 0
        
        if valid_count >= min_valid_datasets:
            logger.info(f"Initial URL list yielded {valid_count} valid datasets. No fallback needed.")
            return valid_urls
    
    logger.warning(f"Initial URL list yielded fewer than {min_valid_datasets} valid datasets. Starting keyword search fallback.")
    
    # Perform keyword search
    keywords = ["social exclusion", "prosocial", "donation"]
    search_results = search_osf_datasets(keywords)
    
    logger.info(f"OSF search returned {len(search_results)} potential datasets.")
    
    fallback_urls = []
    new_valid_count = 0
    
    for dataset in search_results:
        if new_valid_count >= min_valid_datasets:
            break
            
        try:
            # Get files for this dataset
            files = get_dataset_files(dataset['files_url'])
            csv_url = find_csv_in_files(files)
            
            if csv_url:
                # Attempt to download and validate
                filename = f"search_{dataset['id']}.csv"
                dest_path = output_dir / filename
                
                if download_dataset(csv_url, dest_path):
                    df = pd.read_csv(dest_path)
                    df = normalize_columns(df)
                    is_valid, missing = validate_schema(df, ['condition', 'prosocial_amount', 'randomized'])
                    
                    if is_valid:
                        fallback_urls.append(csv_url)
                        new_valid_count += 1
                        logger.info(f"Added valid dataset from search: {dataset['title']}")
                    else:
                        logger.debug(f"Search result missing columns {missing}: {dataset['title']}")
                else:
                    logger.debug(f"Failed to download from search result: {dataset['title']}")
                    
        except Exception as e:
            logger.error(f"Error processing search result {dataset['id']}: {e}")
            
    if new_valid_count < min_valid_datasets:
        logger.error(f"Keyword search fallback only found {new_valid_count} valid datasets. Minimum required: {min_valid_datasets}")
        # Return whatever we found, the caller will handle the halt logic
        
    return fallback_urls

def ingest_with_fallback(output_dir: Path) -> Tuple[pd.DataFrame, int]:
    """
    Main entry point for ingestion with automatic keyword search fallback.
    
    Args:
        output_dir: Directory to store downloaded files
        
    Returns:
        Tuple of (combined DataFrame, count of valid datasets)
    """
    config = get_config()
    initial_urls = config.get('osf_urls', [])
    min_valid = config.get('min_valid_datasets', 3)
    
    # Try initial URLs
    valid_urls = []
    valid_count = 0
    combined_df = pd.DataFrame()
    
    if initial_urls:
        combined_df, valid_count = ingest_datasets(initial_urls, output_dir)
        valid_urls = [url for url in initial_urls]  # Simplified tracking
    
    # Check if fallback is needed
    if valid_count < min_valid:
        fallback_urls = perform_keyword_fallback(output_dir, min_valid)
        
        if fallback_urls:
            # Ingest fallback URLs
            fallback_df, fallback_count = ingest_datasets(fallback_urls, output_dir)
            
            if not combined_df.empty and not fallback_df.empty:
                combined_df = pd.concat([combined_df, fallback_df], ignore_index=True)
            elif not fallback_df.empty:
                combined_df = fallback_df
                
            valid_count += fallback_count
            valid_urls.extend(fallback_urls)
    
    logger.info(f"Ingestion complete. Total valid datasets: {valid_count}")
    return combined_df, valid_count

# Backward compatibility exports
__all__ = [
    'calculate_checksum',
    'validate_schema', 
    'normalize_columns',
    'download_dataset',
    'ingest_datasets',
    'search_osf_datasets',
    'perform_keyword_fallback',
    'ingest_with_fallback'
]
