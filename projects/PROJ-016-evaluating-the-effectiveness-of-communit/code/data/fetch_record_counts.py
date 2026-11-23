"""
Fetch record counts from FAO STAT and World Bank APIs.
Implements streaming/counting logic to avoid loading full datasets into memory.
"""
import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

# Add parent directory to path for imports if running as script
if 'code' not in sys.path[0]:
    code_path = Path(__file__).resolve().parent
    sys.path.insert(0, str(code_path.parent))

from logging_config import get_logger
from config import get_config

logger = get_logger(__name__)

def get_fao_stream_url(indicator_code: str) -> str:
    """
    Construct the FAO STAT API URL for streaming/CSV export.
    FAO STAT API endpoint for data retrieval.
    """
    config = get_config()
    # FAO STAT API base URL for data extraction
    base_url = "https://www.fao.org/faostat/api"
    # Using the CSV export endpoint which supports streaming
    # Indicator: AG.LND.FRST.ZS (Forest Area Change)
    url = f"{base_url}/v1/en/data/export/CSV/{indicator_code}"
    return url

def fetch_fao_records_count(indicator_code: str, timeout: int = 30) -> int:
    """
    Stream the FAO STAT dataset for the given indicator and count rows.
    Does NOT load the full dataset into memory.
    
    Args:
        indicator_code: The FAO indicator code (e.g., 'AG.LND.FRST.ZS')
        timeout: Request timeout in seconds
        
    Returns:
        int: Total number of data rows (excluding header)
        
    Raises:
        RuntimeError: If the API fetch fails after retries
    """
    url = get_fao_stream_url(indicator_code)
    logger.info(f"Fetching FAO stream URL for {indicator_code}: {url}")
    
    # Retry logic with exponential backoff (max 3 attempts)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Use stream=True to handle large files without loading all into memory
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            row_count = 0
            # Iterate line by line to count rows
            for line in response.iter_lines(decode_unicode=True):
                if line and not line.startswith('"Item Code"'):  # Skip header
                    row_count += 1
            
            logger.info(f"Successfully counted {row_count} rows for indicator {indicator_code}")
            return row_count
            
        except requests.exceptions.RequestException as e:
            attempt_num = attempt + 1
            if attempt_num < max_retries:
                wait_time = 2 ** attempt_num
                logger.warning(f"Attempt {attempt_num}/{max_retries} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed for {indicator_code}: {e}")
                raise RuntimeError(f"Failed to fetch FAO data after {max_retries} attempts: {e}")
    
    return 0

def save_outputs(counts: Dict[str, int], output_dir: Path) -> None:
    """
    Save the counts to JSON files in the processed data directory.
    
    Args:
        counts: Dictionary mapping source name to count
        output_dir: Directory to save the JSON files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if 'fao' in counts:
        fao_path = output_dir / "counts_fao.json"
        with open(fao_path, 'w') as f:
            json.dump({"total_fao_available": counts['fao']}, f, indent=2)
        logger.info(f"Saved FAO count to {fao_path}")
    
    if 'wb' in counts:
        wb_path = output_dir / "counts_wb.json"
        with open(wb_path, 'w') as f:
            json.dump({"total_wb_available": counts['wb']}, f, indent=2)
        logger.info(f"Saved World Bank count to {wb_path}")

def main() -> int:
    """
    Main entry point for fetching FAO record counts.
    T008a: Count FAO Rows for 'Forest Area Change' (AG.LND.FRST.ZS)
    """
    config = get_config()
    indicator_code = config.get('FAO_INDICATOR', 'AG.LND.FRST.ZS')
    
    # Output directory from config or default
    output_dir = Path(config.get('DATA_PROCESSED_DIR', 'data/processed'))
    
    logger.info(f"Starting T008a: Counting FAO rows for {indicator_code}")
    
    try:
        # Fetch and count FAO rows
        fao_count = fetch_fao_records_count(indicator_code)
        
        if fao_count == 0:
            logger.error(f"No rows found for indicator {indicator_code} or API failure.")
            return 1
        
        # Save the count
        save_outputs({'fao': fao_count}, output_dir)
        
        logger.info(f"T008a completed successfully. FAO count: {fao_count}")
        return 0
        
    except Exception as e:
        logger.error(f"T008a failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
