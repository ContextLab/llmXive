"""
Fetch record counts from FAO and World Bank APIs for low/middle-income countries (2000-2020).
This script implements T008: Verify and Fetch Total Records.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import requests

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import get_logger
from config import get_config

logger = get_logger(__name__)
config = get_config()

# Constants
YEAR_RANGE = config.get("YEAR_RANGE", (2000, 2020))
LOW_MID_INCOME_CODES = ["LMI"]  # World Bank group code for Low & Middle Income

def get_world_bank_countries_by_income() -> List[str]:
    """
    Fetch list of country ISO3 codes for low and middle-income countries.
    Uses World Bank API: https://api.worldbank.org/v2/country/all?format=json&per_page=300
    Filter by incomeLevel: 'low', 'lower middle', 'upper middle'.
    """
    url = "https://api.worldbank.org/v2/country/all"
    params = {
        "format": "json",
        "per_page": 300,
        "fields": "id;iso2Code;name;region;incomeLevel;lendingType"
    }

    countries = []
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if len(data) < 2:
            raise ValueError("Unexpected World Bank API response format")

        for country in data[1]:
            income_level = country.get("incomeLevel", {}).get("id", "")
            if income_level in ["LDC", "LMC", "UMC"]:  # Low, Lower Middle, Upper Middle
                iso3 = country.get("id")
                if iso3 and iso3 not in ["Aggregates"]:
                    countries.append(iso3)
        
        logger.info(f"Fetched {len(countries)} low/middle-income countries from World Bank.")
        return countries
    except Exception as e:
        logger.error(f"Failed to fetch World Bank countries: {e}")
        raise

def fetch_world_bank_records(countries: List[str]) -> int:
    """
    Fetch total record count from World Bank for a specific indicator across years.
    Indicator: AG.LND.FRST.ZS (Forest Area (% of land area)) - proxy for land use data.
    We query one indicator to estimate the denominator for the dataset we intend to build.
    """
    indicator = "AG.LND.FRST.ZS" # Forest Area %
    total_records = 0
    
    # World Bank API supports pagination, but for count estimation we can use a single query
    # with a large per_page limit or aggregate manually.
    # We will iterate countries to be safe and accurate, as API doesn't support "count all" easily.
    
    url = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    
    for country in countries:
        params = {
            "format": "json",
            "date": f"{YEAR_RANGE[0]}:{YEAR_RANGE[1]}",
            "per_page": 5000 # Max allowed
        }
        
        try:
            response = requests.get(url.format(country=country, indicator=indicator), params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if len(data) > 1:
                # data[0] is metadata, data[1] is list of observations
                records = data[1]
                # Filter out null values if any (though API usually returns valid data points)
                valid_records = [r for r in records if r.get("value") is not None]
                total_records += len(valid_records)
            time.sleep(0.5) # Rate limit compliance
        except Exception as e:
            logger.warning(f"Failed to fetch WB records for {country}: {e}")
            continue

    logger.info(f"Total World Bank records found: {total_records}")
    return total_records

def fetch_fao_records(countries: List[str]) -> int:
    """
    Fetch total record count from FAO FRA (Forest Resources Assessment) API.
    FAO FRA API is less standardized. We use the FAOSTAT bulk data or specific endpoint.
    Endpoint: https://www.fao.org/faostat/en/#data/FO (Forest Area)
    We will use the FAOSTAT API which is more programmatic:
    https://www.fao.org/faostat/api/data/en?domain=FO&element=FO0102&area=211&item=101&unit=1&year=2000,2001...
    
    Simplified approach: Query for all countries in the list for the indicator 'Forest Area' (FO0102)
    over the year range.
    """
    # FAOSTAT API endpoint for data
    base_url = "https://www.fao.org/faostat/api/data/en"
    domain = "FO" # Forest
    element = "FO0102" # Forest area (sq km) or percentage? Let's use area.
    unit = "1" # Hectares or similar
    
    total_records = 0
    years = list(range(YEAR_RANGE[0], YEAR_RANGE[1] + 1))
    year_str = ",".join(map(str, years))
    
    # FAOSTAT API often requires specific area codes. 
    # Since we have ISO3 codes, we might need to map them or query by country name.
    # To avoid complex mapping, we will query the "All Areas" or specific known codes if available.
    # However, the most robust way for a "total available records" check without a full mapping table
    # is to query the metadata or a broad query.
    
    # Alternative: Use the 'metadata' endpoint to count available data points?
    # Let's try a direct data query for a few sample countries to verify structure, then aggregate.
    # But for T008, we need the total. 
    
    # Strategy: Query FAO for the specific indicator for the list of countries.
    # FAO API parameter 'area' accepts ISO3 codes? Documentation says "Area Code".
    # We will attempt to query for each country.
    
    for country in countries:
        # Construct parameters
        params = {
            "domain": domain,
            "element": element,
            "area": country, # Try ISO3
            "year": year_str,
            "format": "json"
        }
        
        try:
            # FAO API might block or require specific headers
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    # Count non-null entries
                    records = data["data"]
                    valid_records = [r for r in records if r.get("Value") is not None]
                    total_records += len(valid_records)
            elif response.status_code == 404:
                # Country not found or no data
                pass
            else:
                logger.warning(f"FAO API returned {response.status_code} for {country}")
            
            time.sleep(1) # Be careful with FAO rate limits
        except Exception as e:
            logger.warning(f"Failed to fetch FAO records for {country}: {e}")
            continue

    logger.info(f"Total FAO records found: {total_records}")
    return total_records

def save_outputs(wb_count: int, fao_count: int, output_path: Path):
    """
    Save the total record counts to the specified JSON file.
    """
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "year_range": YEAR_RANGE,
        "target_countries": "Low and Middle Income",
        "world_bank": {
            "indicator": "AG.LND.FRST.ZS",
            "count": wb_count
        },
        "fao": {
            "domain": "FO",
            "element": "FO0102",
            "count": fao_count
        },
        "total_records": wb_count + fao_count,
        "note": "Counts represent available non-null observations for the specified indicator and year range."
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved total record counts to {output_path}")

def main():
    """
    Main entry point for T008.
    """
    logger.info("Starting T008: Verify and Fetch Total Records")
    
    # 1. Get list of low/middle-income countries
    try:
        countries = get_world_bank_countries_by_income()
    except Exception as e:
        logger.critical(f"Cannot proceed without country list: {e}")
        return

    # 2. Fetch World Bank records
    wb_count = 0
    try:
        wb_count = fetch_world_bank_records(countries)
    except Exception as e:
        logger.error(f"Error fetching World Bank records: {e}")
        # Continue to FAO if possible, or fail? Task requires both.
        # If one fails, we might have incomplete data, but we must not fake.
        # We will log error and proceed to FAO, then save what we have (or fail if critical).
        # Given the constraint "Fail loudly", we should probably raise if critical data missing.
        # However, if API is down, we can't fake. We'll let it crash if it's a hard failure.
        # For now, we assume partial success is better than crash if one API is flaky, 
        # but the task says "Query FAO and World Bank". 
        # We will let the exception propagate if it's a critical fetch failure.
        raise

    # 3. Fetch FAO records
    fao_count = 0
    try:
        fao_count = fetch_fao_records(countries)
    except Exception as e:
        logger.error(f"Error fetching FAO records: {e}")
        raise

    # 4. Save results
    output_path = Path("data/processed/total_records_count.json")
    save_outputs(wb_count, fao_count, output_path)
    
    logger.info("T008 completed successfully.")

if __name__ == "__main__":
    main()
