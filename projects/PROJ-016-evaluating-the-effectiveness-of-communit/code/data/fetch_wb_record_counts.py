"""
Task T008b: Count World Bank Rows
Streams the World Bank dataset for the CBNRM proxy (EG.GOV.POLI.ZS) and GDP/Pop data
for years 2000–2020. Counts rows as they arrive to establish total_wb_available.
Saves the count to data/processed/counts_wb.json.
"""
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import get_logger
from config import get_config

logger = get_logger(__name__)
CONFIG = get_config()

# World Bank API endpoints
WB_API_BASE = "https://api.worldbank.org/v2"
WB_STREAM_BASE = "https://api.worldbank.org/v2/country/all/indicator"

# Indicators to fetch
CBNRM_PROXY_INDICATOR = "EG.GOV.POLI.ZS"
GDP_INDICATOR = "NY.GDP.PCAP.CD"
POP_INDICATOR = "SP.POP.TOTL"

# Years of interest
START_YEAR = CONFIG.get("DATA_YEARS_START", 2000)
END_YEAR = CONFIG.get("DATA_YEARS_END", 2020)

def fetch_world_bank_indicator_count(
    indicator: str,
    start_year: int,
    end_year: int,
    max_pages: int = 1000
) -> int:
    """
    Fetches the count of rows for a specific World Bank indicator for a given year range.
    Uses pagination to count all available rows without loading full data into memory.
    
    Args:
        indicator: The World Bank indicator code (e.g., 'EG.GOV.POLI.ZS')
        start_year: Start year for the data range
        end_year: End year for the data range
        max_pages: Maximum number of pages to fetch (safety limit)
    
    Returns:
        int: Total count of rows for the indicator in the specified year range
    """
    total_count = 0
    page = 1
    per_page = 5000  # Max allowed by World Bank API
    
    # Construct query parameters
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": per_page,
        "page": page,
        "source": "2",  # World Development Indicators
        "format": "json"
    }
    
    url = f"{WB_API_BASE}/country/all/indicator/{indicator}"
    
    logger.info(f"Fetching count for indicator {indicator} from {start_year} to {end_year}")
    
    while page <= max_pages:
        params["page"] = page
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list) or len(data) < 2:
                logger.error(f"Unexpected response format for page {page}")
                break
            
            # First element is metadata, second is the data list
            metadata = data[0]
            page_data = data[1]
            
            page_count = len(page_data)
            total_count += page_count
            
            logger.debug(f"Page {page}: fetched {page_count} rows, total so far: {total_count}")
            
            # Check if we've reached the last page
            if metadata.get("page", 1) >= metadata.get("pages", 1):
                break
            
            page += 1
            
            # Small delay to respect API rate limits
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed on page {page}: {e}")
            # Retry logic could be added here, but for counting we fail loud
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error on page {page}: {e}")
            raise
    
    logger.info(f"Total rows fetched for {indicator}: {total_count}")
    return total_count

def count_world_bank_rows() -> Dict[str, Any]:
    """
    Counts rows for CBNRM proxy, GDP, and Population indicators.
    
    Returns:
        Dict containing counts for each indicator and total
    """
    try:
        cbnrm_count = fetch_world_bank_indicator_count(
            CBNRM_PROXY_INDICATOR, START_YEAR, END_YEAR
        )
        
        gdp_count = fetch_world_bank_indicator_count(
            GDP_INDICATOR, START_YEAR, END_YEAR
        )
        
        pop_count = fetch_world_bank_indicator_count(
            POP_INDICATOR, START_YEAR, END_YEAR
        )
        
        # The task asks for total_wb_available which should represent
        # the total rows available across all relevant indicators
        # We'll use the count of the primary indicator (CBNRM) as the main metric
        # since it's the limiting factor for the analysis
        total_wb_available = cbnrm_count
        
        return {
            "cbnrm_proxy_count": cbnrm_count,
            "gdp_count": gdp_count,
            "population_count": pop_count,
            "total_wb_available": total_wb_available,
            "year_range": f"{START_YEAR}-{END_YEAR}",
            "indicators": {
                "cbnrm_proxy": CBNRM_PROXY_INDICATOR,
                "gdp": GDP_INDICATOR,
                "population": POP_INDICATOR
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to count World Bank rows: {e}")
        raise

def save_outputs(counts: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the row counts to a JSON file.
    
    Args:
        counts: Dictionary containing the row counts
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(counts, f, indent=2)
    
    logger.info(f"Saved row counts to {output_path}")

def main() -> None:
    """Main entry point for T008b."""
    try:
        # Determine output path
        project_root = Path(__file__).parent.parent.parent
        output_path = project_root / "data" / "processed" / "counts_wb.json"
        
        # Count rows
        counts = count_world_bank_rows()
        
        # Save results
        save_outputs(counts, output_path)
        
        logger.info("T008b completed successfully")
        print(f"Total World Bank rows available: {counts['total_wb_available']}")
        
    except Exception as e:
        logger.error(f"T008b failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
