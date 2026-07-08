"""
Ingestion module for downloading and parsing pre-registered study data from OSF.
Implements exponential backoff for API rate limits (429) and data extraction logic.
"""
import os
import sys
import time
import json
import hashlib
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import urljoin

# Import shared configuration
from config import (
    ensure_config_dirs,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    OUTPUTS_DIR,
    MAX_ITERATIONS,
    ALTERNATIVE_ITERATIONS,
    TIMEOUT_HOURS,
    RANDOM_SEED
)
from main import log_header, log_step, calculate_file_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(OUTPUTS_DIR, 'ingestion.log'))
    ]
)
logger = logging.getLogger(__name__)

# OSF API Configuration
OSF_API_BASE = "https://api.osf.io/v2/"
OSF_REGISTRATIONS_ENDPOINT = "registrations/"
OSF_FILES_ENDPOINT = "files/"

# Rate limiting constants
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0
BACKOFF_MULTIPLIER = 2.0

def ensure_directory_structure():
    """Ensure all required directories exist."""
    ensure_config_dirs()
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

def fetch_with_backoff(url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Optional[Dict]:
    """
    Fetch data from OSF API with exponential backoff for 429 errors.
    
    Args:
        url: The API endpoint URL
        params: Query parameters
        headers: Request headers
        
    Returns:
        JSON response data or None if failed
    """
    retries = 0
    backoff = INITIAL_BACKOFF
    
    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            
            elif response.status_code == 429:
                # Rate limit exceeded - apply backoff
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    sleep_time = int(retry_after)
                else:
                    sleep_time = backoff
                
                logger.warning(f"Rate limit (429) hit. Waiting {sleep_time}s before retry ({retries + 1}/{MAX_RETRIES})")
                time.sleep(sleep_time)
                backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)
                retries += 1
                continue
            
            elif response.status_code == 404:
                logger.error(f"Resource not found: {url}")
                return None
            
            elif response.status_code >= 500:
                # Server error - retry with backoff
                logger.warning(f"Server error ({response.status_code}). Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)
                retries += 1
                continue
            
            else:
                logger.error(f"Unexpected status code {response.status_code} from {url}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout. Retrying in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)
            retries += 1
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    logger.error(f"Max retries ({MAX_RETRIES}) exceeded for {url}")
    return None

def list_registrations(limit: int = 50, query: str = "") -> List[Dict]:
    """
    List pre-registered studies from OSF API.
    
    Args:
        limit: Maximum number of registrations to fetch
        query: Optional search query string
        
    Returns:
        List of registration metadata dictionaries
    """
    ensure_directory_structure()
    
    params = {
        'page': 1,
        'page_size': min(limit, 100),  # OSF max page size
        'filter[preprint_registered]': 'true'
    }
    
    if query:
        params['q'] = query
        
    all_registrations = []
    page = 1
    
    while len(all_registrations) < limit:
        url = urljoin(OSF_API_BASE, OSF_REGISTRATIONS_ENDPOINT)
        params['page'] = page
        
        logger.info(f"Fetching OSF registrations page {page}...")
        data = fetch_with_backoff(url, params=params)
        
        if not data or 'data' not in data:
            break
            
        registrations = data.get('data', [])
        if not registrations:
            break
            
        all_registrations.extend(registrations)
        page += 1
        
        # Check if we have enough
        if len(all_registrations) >= limit:
            break
            
        # Check if there are more pages
        links = data.get('links', {})
        if 'next' not in links:
            break
            
        # Use next link for pagination
        url = links['next']
        params = None  # Clear params as they are in the URL
        
    return all_registrations[:limit]

def get_registration_files(registration_id: str) -> List[Dict]:
    """
    Get files associated with a specific registration.
    
    Args:
        registration_id: The OSF registration ID
        
    Returns:
        List of file metadata dictionaries
    """
    url = urljoin(OSF_API_BASE, f"{OSF_REGISTRATIONS_ENDPOINT}{registration_id}/files/")
    data = fetch_with_backoff(url)
    
    if not data or 'data' not in data:
        return []
        
    return data.get('data', [])

def download_file(file_url: str, save_path: str) -> bool:
    """
    Download a file from OSF to local storage.
    
    Args:
        file_url: The direct download URL
        save_path: Local path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(file_url, stream=True, timeout=60)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"Downloaded: {save_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {file_url}: {e}")
        return False

def parse_registration_metadata(registration: Dict) -> Optional[Dict]:
    """
    Parse metadata from a registration object.
    
    Args:
        registration: Raw registration data from OSF API
        
    Returns:
        Parsed metadata dictionary or None if parsing fails
    """
    try:
        attrs = registration.get('attributes', {})
        relationships = registration.get('relationships', {})
        
        # Extract basic metadata
        osf_id = registration.get('id', '')
        title = attrs.get('title', '')
        description = attrs.get('description', '')
        
        # Extract discipline/category
        category = attrs.get('category', '')
        # Map OSF categories to our disciplines
        discipline_map = {
            'psychology': 'psychology',
            'social': 'psychology',
            'economics': 'economics',
            'business': 'economics',
            'biology': 'biology',
            'life-sciences': 'biology',
            'medicine': 'biology',
            'health-sciences': 'biology',
            'physics': 'biology',  # Broad science category
            'chemistry': 'biology',
            'computer-science': 'economics',  # Often quantitative
            'education': 'psychology',
            'political-science': 'economics',
            'sociology': 'psychology',
        }
        discipline = discipline_map.get(category.lower(), 'other')
        
        # Try to extract p-value and sample size from description or title
        # This is a heuristic; actual parsing might require reading the full manuscript
        original_p_value = None
        sample_size = None
        
        # Look for patterns in description
        import re
        desc_text = (description + " " + title).lower()
        
        # Simple p-value extraction (e.g., "p = 0.03", "p<0.05")
        p_matches = re.findall(r'p\s*[<>=]\s*0\.\d{2,}', desc_text)
        if p_matches:
            # Extract the value
            p_str = p_matches[0].split('=')[-1].split('<')[-1].split('>')[-1].strip()
            try:
                original_p_value = float(p_str)
            except ValueError:
                pass
        
        # Sample size extraction
        n_matches = re.findall(r'n\s*=\s*(\d+)', desc_text)
        if n_matches:
            try:
                sample_size = int(n_matches[0])
            except ValueError:
                pass
        
        # Check for ambiguous model indicators
        ambiguous_keywords = ['mixed', 'unclear', 'multiple models', 'robustness', 'sensitivity']
        is_ambiguous = any(kw in desc_text for kw in ambiguous_keywords)
        
        return {
            'osf_id': osf_id,
            'title': title,
            'discipline': discipline,
            'category': category,
            'original_p_value': original_p_value,
            'sample_size': sample_size,
            'description': description,
            'is_ambiguous_model': is_ambiguous,
            'missing_p_value': original_p_value is None,
            'missing_sample_size': sample_size is None,
            'raw_data': registration
        }
        
    except Exception as e:
        logger.error(f"Failed to parse metadata for registration {registration.get('id', 'unknown')}: {e}")
        return None

def ingest_studies(target_count: int = 50, force_disciplines: List[str] = None) -> Tuple[List[Dict], List[str]]:
    """
    Ingest pre-registered studies from OSF.
    
    Args:
        target_count: Number of studies to attempt to ingest
        force_disciplines: List of disciplines to prioritize for balanced sampling
        
    Returns:
        Tuple of (list of parsed study dicts, list of error messages)
    """
    ensure_directory_structure()
    
    logger.info(f"Starting ingestion of up to {target_count} studies from OSF...")
    
    # Fetch registrations
    registrations = list_registrations(limit=target_count * 2)  # Fetch extra to allow filtering
    
    if not registrations:
        logger.error("No registrations found from OSF API.")
        return [], ["No registrations found"]
    
    logger.info(f"Found {len(registrations)} potential registrations.")
    
    parsed_studies = []
    errors = []
    
    # If force_disciplines is specified, ensure balanced sampling
    if force_disciplines:
        discipline_buckets = {d: [] for d in force_disciplines}
        discipline_buckets['other'] = []
        
        for reg in registrations:
            parsed = parse_registration_metadata(reg)
            if not parsed:
                continue
                
            disc = parsed['discipline']
            if disc in discipline_buckets:
                discipline_buckets[disc].append(parsed)
            else:
                discipline_buckets['other'].append(parsed)
        
        # Select balanced subset
        studies_per_discipline = target_count // len(force_disciplines)
        remainder = target_count % len(force_disciplines)
        
        for i, disc in enumerate(force_disciplines):
            count = studies_per_discipline + (1 if i < remainder else 0)
            selected = discipline_buckets[disc][:count]
            parsed_studies.extend(selected)
            
        # Fill remaining with 'other' if needed
        if len(parsed_studies) < target_count:
            remaining = target_count - len(parsed_studies)
            other_studies = discipline_buckets['other'][:remaining]
            parsed_studies.extend(other_studies)
            
    else:
        # Standard ingestion without forced balance
        for reg in registrations:
            parsed = parse_registration_metadata(reg)
            if parsed:
                parsed_studies.append(parsed)
            
            if len(parsed_studies) >= target_count:
                break
    
    logger.info(f"Ingested {len(parsed_studies)} studies successfully.")
    
    # Log warnings for ambiguous or missing data
    for study in parsed_studies:
        if study['missing_p_value']:
            logger.warning(f"Study {study['osf_id']}: Missing p-value")
        if study['is_ambiguous_model']:
            logger.warning(f"Study {study['osf_id']}: Ambiguous model specification")
    
    return parsed_studies, errors

def save_baseline_metrics(studies: List[Dict], output_path: Optional[str] = None):
    """
    Save ingested study data to baseline_metrics.csv.
    
    Args:
        studies: List of parsed study dictionaries
        output_path: Optional custom output path
    """
    if output_path is None:
        output_path = os.path.join(DATA_PROCESSED_DIR, "baseline_metrics.csv")
    
    ensure_directory_structure()
    
    if not studies:
        logger.warning("No studies to save.")
        return
    
    # Define CSV columns
    columns = [
        'osf_id',
        'title',
        'discipline',
        'original_p_value',
        'sample_size',
        'is_ambiguous_model',
        'missing_p_value',
        'missing_sample_size'
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write(','.join(columns) + '\n')
        
        # Write data rows
        for study in studies:
            row = [
                study['osf_id'],
                '"' + study['title'].replace('"', '""') + '"',  # Escape quotes
                study['discipline'],
                str(study['original_p_value']) if study['original_p_value'] is not None else '',
                str(study['sample_size']) if study['sample_size'] is not None else '',
                str(study['is_ambiguous_model']),
                str(study['missing_p_value']),
                str(study['missing_sample_size'])
            ]
            f.write(','.join(row) + '\n')
    
    # Calculate and log hash
    file_hash = calculate_file_hash(output_path)
    logger.info(f"Saved {len(studies)} studies to {output_path}")
    logger.info(f"SHA-256 checksum: {file_hash}")

def main():
    """Main entry point for ingestion pipeline."""
    log_header("OSF Data Ingestion")
    
    # Define disciplines to ensure balanced sampling
    target_disciplines = ['psychology', 'economics', 'biology']
    target_count = 50
    
    # Ingest studies
    studies, errors = ingest_studies(
        target_count=target_count,
        force_disciplines=target_disciplines
    )
    
    if errors:
        logger.error(f"Ingestion completed with {len(errors)} errors:")
        for err in errors:
            logger.error(f"  - {err}")
    
    if not studies:
        logger.error("Ingestion failed: No studies retrieved.")
        return 1
    
    # Save results
    output_file = os.path.join(DATA_PROCESSED_DIR, "baseline_metrics.csv")
    save_baseline_metrics(studies, output_file)
    
    log_step(f"Ingestion complete: {len(studies)} studies saved to {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())