import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import yaml

# Import custom exception as per project API surface
from utils.exceptions import DataQualityError
from utils.logging_utils import setup_logging, get_logger

# Constants
VALIDATION_LOG_PATH = Path("data/logs/source_validation.log")
RESEARCH_MD_PATH = Path("specs/001-predict-root-architecture/research.md")
TIMEOUT_SECONDS = 30

def parse_research_md_sources(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses the research.md file to extract verified data sources.
    Expected format in research.md:
    - Zenodo: [ID]
    - Dryad: [ID]
    - SoilGrids: [URL or Dataset ID]
    - HuggingFace: [Dataset ID]
    
    Returns a list of dicts with 'source_type', 'id', and 'url'.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Research file not found: {file_path}")
    
    sources = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Parse Zenodo
        if line.lower().startswith("zenodo"):
            # Extract ID, e.g., "Zenodo: 1234567"
            parts = line.split(":", 1)
            if len(parts) == 2:
                source_id = parts[1].strip()
                sources.append({
                    "source_type": "Zenodo",
                    "id": source_id,
                    "url": f"https://zenodo.org/api/records/{source_id}"
                })
        
        # Parse Dryad
        elif line.lower().startswith("dryad"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                source_id = parts[1].strip()
                # Dryad URL structure
                sources.append({
                    "source_type": "Dryad",
                    "id": source_id,
                    "url": f"https://datadryad.org/stash/dataset/{source_id}"
                })
        
        # Parse SoilGrids (API endpoint or HF dataset)
        elif "soilgrids" in line.lower():
            # Check if it's a HF dataset ID or URL
            if line.startswith("http"):
                sources.append({
                    "source_type": "SoilGrids",
                    "id": line,
                    "url": line
                })
            else:
                # Assume HF dataset ID format if not a URL
                # e.g., "SoilGrids: isric/soilgrids"
                parts = line.split(":", 1)
                if len(parts) == 2:
                    dataset_id = parts[1].strip()
                    sources.append({
                        "source_type": "SoilGrids",
                        "id": dataset_id,
                        "url": f"https://huggingface.co/datasets/{dataset_id}"
                    })
        
        # Parse HuggingFace
        elif line.lower().startswith("huggingface") or "hf" in line.lower():
            if "://" in line:
                url = line.split(":", 1)[1].strip()
                sources.append({
                    "source_type": "HuggingFace",
                    "id": url.split("/")[-1],
                    "url": url
                })
            else:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    dataset_id = parts[1].strip()
                    sources.append({
                        "source_type": "HuggingFace",
                        "id": dataset_id,
                        "url": f"https://huggingface.co/datasets/{dataset_id}"
                    })
    
    return sources

def verify_source(source: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """
    Verifies the accessibility of a single data source.
    Returns a dict with status, response_time, and error_message (if any).
    """
    result = {
        "source_type": source["source_type"],
        "id": source["id"],
        "url": source["url"],
        "status": "unknown",
        "response_time_ms": None,
        "error_message": None
    }
    
    try:
        start_time = time.time()
        response = requests.head(source["url"], timeout=TIMEOUT_SECONDS, allow_redirects=True)
        end_time = time.time()
        
        result["response_time_ms"] = round((end_time - start_time) * 1000, 2)
        
        # Handle specific status codes
        if response.status_code == 200:
            result["status"] = "accessible"
        elif response.status_code == 301 or response.status_code == 302:
            # Redirect is usually fine if it resolves
            result["status"] = "accessible (redirect)"
        elif response.status_code == 404:
            result["status"] = "not_found"
            result["error_message"] = f"HTTP 404: Resource not found"
        elif response.status_code == 403:
            result["status"] = "forbidden"
            result["error_message"] = f"HTTP 403: Access forbidden"
        elif response.status_code >= 500:
            result["status"] = "server_error"
            result["error_message"] = f"HTTP {response.status_code}: Server error"
        else:
            result["status"] = f"unexpected_{response.status_code}"
            result["error_message"] = f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error_message"] = f"Request timed out after {TIMEOUT_SECONDS}s"
    except requests.exceptions.ConnectionError as e:
        result["status"] = "connection_error"
        result["error_message"] = f"Connection failed: {str(e)}"
    except requests.exceptions.RequestException as e:
        result["status"] = "request_failed"
        result["error_message"] = f"Request failed: {str(e)}"
    
    logger.info(f"Verified {source['source_type']} ({source['id']}): {result['status']} in {result['response_time_ms']}ms")
    return result

def main():
    """
    Main entry point for Data Discovery & Source Validation (T000).
    1. Reads research.md.
    2. Verifies all listed sources.
    3. Logs results to data/logs/source_validation.log.
    4. Raises DataQualityError if any source is unreachable.
    """
    # Setup logging
    setup_logging()
    logger = get_logger("source_validation")
    
    logger.info("Starting Data Discovery & Source Validation (T000)...")
    
    # Ensure log directory exists
    VALIDATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Add file handler for the specific log file
    file_handler = logging.FileHandler(VALIDATION_LOG_PATH, mode='w')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    try:
        # Step 1: Parse sources from research.md
        if not RESEARCH_MD_PATH.exists():
            raise FileNotFoundError(f"Research file {RESEARCH_MD_PATH} not found. "
                                    "Ensure T035 has completed successfully.")
        
        logger.info(f"Parsing sources from {RESEARCH_MD_PATH}...")
        sources = parse_research_md_sources(RESEARCH_MD_PATH)
        
        if not sources:
            logger.warning("No data sources found in research.md.")
            logger.info("Validation complete (no sources to verify).")
            return
        
        logger.info(f"Found {len(sources)} data sources to verify.")
        
        # Step 2: Verify each source
        all_accessible = True
        validation_results = []
        
        for source in sources:
            result = verify_source(source, logger)
            validation_results.append(result)
            if result["status"] != "accessible" and result["status"] != "accessible (redirect)":
                all_accessible = False
        
        # Step 3: Write summary to log
        logger.info("-" * 50)
        logger.info("SUMMARY:")
        for res in validation_results:
            status_str = f"[{res['status'].upper()}]"
            logger.info(f"{status_str} {res['source_type']}: {res['id']} ({res['url']})")
            if res['error_message']:
                logger.error(f"  Error: {res['error_message']}")
        
        # Step 4: Hard fail if any source is unreachable
        if not all_accessible:
            failed_sources = [r for r in validation_results if r["status"] not in ["accessible", "accessible (redirect)"]]
            error_msg = f"Data source validation failed for {len(failed_sources)} source(s). " \
                        "See data/logs/source_validation.log for details."
            logger.error(error_msg)
            raise DataQualityError(error_msg)
        
        logger.info("All data sources are accessible. Validation successful.")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except DataQualityError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {str(e)}")
        raise DataQualityError(f"Unexpected error during source validation: {str(e)}")
    finally:
        # Remove file handler to avoid locking issues
        logger.removeHandler(file_handler)
        file_handler.close()

if __name__ == "__main__":
    main()
