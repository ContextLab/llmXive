import os
import sys
import time
import json
import hashlib
import logging
import csv
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from config to ensure paths are correct
try:
    from config import ensure_config_dirs
except ImportError:
    # Fallback for standalone execution if config is not in path yet
    # In a real run, this should be handled by the project structure
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OSF_API_BASE = "https://api.osf.io/v2"
MAX_RETRIES = 5
BACKOFF_FACTOR = 2
TARGET_DISCIPLINES = ['psychology', 'economics', 'biology']
MIN_PER_DISCIPLINE = 1
MAX_STUDIES = 50

def ensure_directory_structure():
    """Ensure all required directories exist."""
    base_dir = Path("projects/PROJ-065-assessing-the-generalizability-of-statis")
    dirs = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "outputs",
        base_dir / "outputs" / "figures",
        base_dir / "outputs" / "reports",
        base_dir / "tests",
        base_dir / "code"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return base_dir

def fetch_with_backoff(url: str, retries: int = MAX_RETRIES) -> Optional[Dict[str, Any]]:
    """Fetch data from URL with exponential backoff."""
    for attempt in range(retries):
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
                elif response.status == 429:
                    wait_time = (2 ** attempt) * BACKOFF_FACTOR
                    logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry {attempt+1}/{retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP Error {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            if attempt == retries - 1:
                return None
            time.sleep((2 ** attempt) * BACKOFF_FACTOR)
    return None

def list_registrations() -> List[Dict[str, Any]]:
    """List pre-registered studies from OSF."""
    # In a real implementation, this would query the OSF API
    # For this task, we assume the data has been fetched and stored in raw
    # or we simulate the structure based on the task requirements
    # Since we cannot actually fetch 50 real studies without a specific query and auth,
    # we will implement the logic to process what is available or generate a realistic
    # structure if the raw folder is empty, BUT per strict constraints:
    # "Real data only".
    # We will implement the fetch logic to a specific public OSF query for pre-reg studies.
    # OSF Public API endpoint for registrations:
    # https://api.osf.io/v2/registrations/?filter=preprint_provider&filter=public
    
    # For the purpose of this implementation to be runnable and produce real output:
    # We will attempt to fetch a small set of real public registrations.
    # If that fails, we raise an error.
    
    url = f"{OSF_API_BASE}/registrations/?filter=public&filter=category:preprint&embed=authors&embed=contributors&embed=license&embed=affiliations&embed=provider&embed=files&embed=wikis&embed=comments&embed=links&embed=logs&embed=children&embed=attachments&embed=access_requests&embed=nodes&embed=external_links&embed=external_identifiers&embed=preprints&embed=providers&embed=affiliations&embed=license&embed=comments&embed=logs&embed=children&embed=attachments&embed=access_requests&embed=nodes&embed=external_links&embed=external_identifiers&embed=preprints&embed=providers&embed=affiliations&embed=license&embed=comments&embed=logs&embed=children&embed=attachments&embed=access_requests&embed=nodes&embed=external_links&embed=external_identifiers&embed=preprints&embed=providers&embed=affiliations&embed=license&embed=comments&embed=logs&embed=children&embed=attachments&embed=access_requests&embed=nodes&embed=external_links&embed=external_identifiers&embed=preprints&embed=providers"
    
    # Simplified query for public registrations
    query_url = f"{OSF_API_BASE}/registrations/?filter=public&page[size]=50"
    
    data = fetch_with_backoff(query_url)
    if data and 'data' in data:
        return data['data']
    return []

def get_registration_files(registration_id: str) -> List[Dict[str, Any]]:
    """Get files for a specific registration."""
    # OSF API: /v2/registrations/{id}/files/
    url = f"{OSF_API_BASE}/registrations/{registration_id}/files/"
    data = fetch_with_backoff(url)
    if data and 'data' in data:
        return data['data']
    return []

def download_file(file_url: str, dest_path: Path) -> bool:
    """Download a file from a URL to a destination path."""
    try:
        import urllib.request
        urllib.request.urlretrieve(file_url, dest_path)
        return True
    except Exception as e:
        logger.error(f"Failed to download {file_url}: {e}")
        return False

def parse_registration_metadata(registration_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse metadata from a registration object."""
    try:
        # OSF structure: data.attributes.title, data.attributes.description, etc.
        # We need to extract discipline, p-value, sample size if available in metadata
        # Since OSF metadata is unstructured, we look for specific keywords in description/title
        # or rely on a specific schema if known.
        
        # For this implementation, we assume a specific schema or heuristic
        # to extract the required fields.
        
        attrs = registration_data.get('attributes', {})
        title = attrs.get('title', '')
        description = attrs.get('description', '')
        
        # Heuristic: Look for keywords in title/description to assign discipline
        discipline = "unknown"
        title_lower = title.lower()
        desc_lower = description.lower()
        
        if any(word in title_lower or word in desc_lower for word in ['psych', 'cognitive', 'behavior']):
            discipline = "psychology"
        elif any(word in title_lower or word in desc_lower for word in ['econ', 'finance', 'market']):
            discipline = "economics"
        elif any(word in title_lower or word in desc_lower for word in ['bio', 'life', 'cell', 'gene']):
            discipline = "biology"
        
        # Extract p-value and sample size from description (heuristic)
        # This is a placeholder for a more robust NLP parser
        # In a real scenario, we would parse the PDF or HTML
        original_p_value = None
        sample_size = None
        
        # Simple regex-like extraction for demonstration
        import re
        p_match = re.search(r'p\s*[<>=]\s*([0-9.]+)', description)
        if p_match:
            original_p_value = float(p_match.group(1))
        
        n_match = re.search(r'n\s*[=:]\s*(\d+)', description)
        if n_match:
            sample_size = int(n_match.group(1))
        
        if original_p_value is None or sample_size is None:
            # Flag as ambiguous or missing
            return {
                'osf_id': registration_data.get('id'),
                'discipline': discipline,
                'original_p_value': original_p_value,
                'sample_size': sample_size,
                'status': 'missing_p_value' if original_p_value is None else 'ambiguous_model'
            }
        
        return {
            'osf_id': registration_data.get('id'),
            'discipline': discipline,
            'original_p_value': original_p_value,
            'sample_size': sample_size,
            'status': 'valid'
        }
    except Exception as e:
        logger.error(f"Error parsing metadata: {e}")
        return None

def ingest_studies() -> List[Dict[str, Any]]:
    """Ingest studies from OSF, ensuring balanced disciplines."""
    base_dir = ensure_directory_structure()
    raw_dir = base_dir / "data" / "raw"
    
    registrations = list_registrations()
    if not registrations:
        logger.warning("No registrations found. Cannot proceed.")
        return []
    
    studies = []
    discipline_counts = {d: 0 for d in TARGET_DISCIPLINES}
    
    for reg in registrations:
        if len(studies) >= MAX_STUDIES:
            break
        
        meta = parse_registration_metadata(reg)
        if not meta:
            continue
        
        # Check if we need to enforce balance
        if meta['discipline'] in TARGET_DISCIPLINES:
            if discipline_counts[meta['discipline']] < MIN_PER_DISCIPLINE:
                studies.append(meta)
                discipline_counts[meta['discipline']] += 1
            elif len([s for s in studies if s['discipline'] in TARGET_DISCIPLINES]) < MAX_STUDIES:
                # Allow more if we haven't hit max
                studies.append(meta)
                discipline_counts[meta['discipline']] += 1
        else:
            # Unknown discipline, add if under limit
            if len(studies) < MAX_STUDIES:
                studies.append(meta)
        
        # Flag missing/ambiguous
        if meta['status'] != 'valid':
            logger.warning(f"Study {meta['osf_id']} flagged: {meta['status']}")
    
    return studies

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_baseline_metrics(studies: List[Dict[str, Any]], output_path: Path):
    """
    Save baseline metrics to CSV with SHA-256 checksum.
    This is the implementation for T017.
    """
    if not studies:
        logger.warning("No studies to save.")
        return

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    fieldnames = ['osf_id', 'discipline', 'original_p_value', 'sample_size', 'status']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for study in studies:
            writer.writerow({
                'osf_id': study['osf_id'],
                'discipline': study['discipline'],
                'original_p_value': study['original_p_value'],
                'sample_size': study['sample_size'],
                'status': study['status']
            })

    # Calculate and save checksum
    checksum_path = Path(str(output_path) + ".sha256")
    file_hash = calculate_file_hash(output_path)
    
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(f"{file_hash}  {output_path.name}\n")
    
    logger.info(f"Saved baseline metrics to {output_path}")
    logger.info(f"Checksum saved to {checksum_path}: {file_hash}")

def main():
    """Main entry point for ingestion and CSV export."""
    logger.info("Starting ingestion pipeline...")
    
    # Ingest studies
    studies = ingest_studies()
    
    if not studies:
        logger.error("Failed to ingest any studies.")
        sys.exit(1)
    
    # Define output path
    base_dir = Path("projects/PROJ-065-assessing-the-generalizability-of-statis")
    output_path = base_dir / "data" / "processed" / "baseline_metrics.csv"
    
    # Save to CSV
    save_baseline_metrics(studies, output_path)
    
    logger.info("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()