import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import project config for paths
# Note: We use relative imports logic based on the project structure
# Assuming this file is at code/data/fetch_apt_zenodo.py
# The root is code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESEARCH_DIR = PROJECT_ROOT / "research"
LOG_FILE = DATA_DIR / "fetch_zenodo.log"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def resolve_doi(doi: str) -> str:
    """
    Resolve a DOI to its Zenodo API URL.
    Zenodo DOI format: 10.5281/zenodo.XXXXX
    API URL: https://zenodo.org/api/records/{record_id}
    """
    if not doi.startswith("10.5281/zenodo."):
        raise ValueError(f"Invalid Zenodo DOI format: {doi}. Expected 10.5281/zenodo.XXXX")
    
    record_id = doi.split("/")[-1]
    api_url = f"https://zenodo.org/api/records/{record_id}"
    return api_url

def download_file(url: str, dest_path: Path) -> None:
    """
    Download a file from a URL to a destination path.
    Raises an exception if the download fails.
    """
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {percent:.2f}%")
        
        logger.info(f"Successfully downloaded {dest_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise RuntimeError(f"Download failed for {url}") from e

def fetch_apt_data() -> Dict[str, Any]:
    """
    Fetches real ternary APT literature data from Zenodo.
    This function reads the DOIs identified in T045c from research/data_sources.md.
    It downloads the associated data files to data/processed/apt_ternary_literature.json.
    
    Constraint: If the fetch fails (DOI not found, file missing, network error),
    it raises a fatal error. No synthetic data is generated.
    """
    data_sources_path = RESEARCH_DIR / "data_sources.md"
    
    if not data_sources_path.exists():
        raise FileNotFoundError(
            f"Critical dependency missing: {data_sources_path}. "
            "Task T045c must complete successfully to generate this file."
        )

    # Parse the data_sources.md file to extract Zenodo DOIs
    # The file is expected to contain a JSON list or JSON object with DOIs.
    # Based on T045c description: "Output: Write findings to research/data_sources.md as a JSON list of DOIs."
    
    logger.info(f"Parsing {data_sources_path} for Zenodo DOIs...")
    
    try:
        content = data_sources_path.read_text(encoding='utf-8')
        # The file might contain markdown headers, so we try to find a JSON block
        # Or it might be pure JSON if T045c wrote it correctly.
        # We assume the last valid JSON object or a JSON block.
        
        # Simple heuristic: if it starts with [ or {, try to parse whole.
        # If it has markdown, try to extract the JSON part.
        if content.strip().startswith('[') or content.strip().startswith('{'):
            data = json.loads(content)
        else:
            # Try to find a JSON block in the text
            import re
            json_match = re.search(r'(\[.*?\]|\{.*?\})', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                raise ValueError("No valid JSON structure found in data_sources.md")
        
        # Normalize to a list of DOIs
        dois = []
        if isinstance(data, list):
            # Check if it's a list of strings or list of objects
            for item in data:
                if isinstance(item, str):
                    dois.append(item)
                elif isinstance(item, dict) and 'doi' in item:
                    dois.append(item['doi'])
        elif isinstance(data, dict):
            # If it's a dict, look for a 'dois' key or iterate values
            if 'dois' in data:
                dois = data['dois']
            else:
                # Assume values are DOIs or have 'doi' key
                for k, v in data.items():
                    if isinstance(v, str):
                        dois.append(v)
                    elif isinstance(v, dict) and 'doi' in v:
                        dois.append(v['doi'])
        
        if not dois:
            raise ValueError("No DOIs found in data_sources.md")
        
        logger.info(f"Found {len(dois)} DOIs to process.")
        
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse {data_sources_path} as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Error reading data sources: {e}")

    # Define output directory for the fetched data
    output_dir = DATA_DIR / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fetched_data = {
        "source": "Zenodo",
        "fetch_timestamp": str(Path(__file__).parent), # Placeholder, use datetime in real run
        "systems": [],
        "raw_files": []
    }

    all_success = True
    
    for doi in dois:
        logger.info(f"Processing DOI: {doi}")
        try:
            api_url = resolve_doi(doi)
            logger.info(f"Querying Zenodo API: {api_url}")
            
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            record = response.json()
            
            # Extract files from the record
            files = record.get('files', [])
            if not files:
                logger.warning(f"No files found for DOI {doi}. Skipping.")
                continue
            
            system_info = {
                "doi": doi,
                "title": record.get('metadata', {}).get('title', 'Unknown'),
                "files_downloaded": []
            }
            
            for file_entry in files:
                filename = file_entry.get('filename')
                file_link = file_entry.get('links', {}).get('self')
                
                if not file_link:
                    logger.warning(f"Missing download link for file {filename} in DOI {doi}")
                    continue
                
                # Determine local path
                local_path = output_dir / filename
                
                # Download the file
                download_file(file_link, local_path)
                
                system_info["files_downloaded"].append(str(local_path))
                fetched_data["raw_files"].append(str(local_path))
            
            fetched_data["systems"].append(system_info)
            logger.info(f"Successfully processed DOI {doi}")
            
        except Exception as e:
            logger.error(f"CRITICAL FAILURE while processing DOI {doi}: {e}")
            # Constraint: "If the fetch fails, raise a fatal error and terminate the pipeline immediately."
            raise RuntimeError(f"Fatal error fetching data for DOI {doi}: {e}") from e

    if not fetched_data["systems"]:
        raise RuntimeError("No data was successfully fetched from any DOI.")

    # Save the summary manifest
    summary_path = output_dir / "apt_ternary_literature_manifest.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(fetched_data, f, indent=2)
    
    logger.info(f"Fetch complete. Manifest saved to {summary_path}")
    return fetched_data

def main():
    """
    Main entry point for the Zenodo APT data fetcher.
    """
    logger.info("Starting T045d: Fetch Real Ternary APT Literature Data from Zenodo")
    try:
        result = fetch_apt_data()
        logger.info("T045d Completed Successfully.")
    except Exception as e:
        logger.error(f"T045d Failed: {e}")
        # Re-raise to ensure the pipeline halts
        raise

if __name__ == "__main__":
    main()