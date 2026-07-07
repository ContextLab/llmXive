"""
Script to verify statistical claims for Wikidata Q19873191 (A/B Testing).
Fetches metadata and summary statistics from Wikidata SPARQL and the associated paper page.
Produces a CSV report of extracted data for further audit.
"""
import csv
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Local imports from project structure
from code.src.utils.logger import get_default_logger, AuditLogger

# Configure logger
logger = get_default_logger()

WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_QID = "Q19873191"
OUTPUT_DIR = Path("data/raw")
OUTPUT_CSV = OUTPUT_DIR / "wikidata_q19873191_data.csv"
OUTPUT_JSON = OUTPUT_DIR / "wikidata_q19873191_metadata.json"

def fetch_wikidata_sparql(query: str) -> List[Dict[str, Any]]:
    """Execute a SPARQL query against the Wikidata endpoint."""
    import requests
    import urllib.parse

    params = {
        'query': query,
        'format': 'json'
    }
    headers = {
        'Accept': 'application/sparql-results+json',
        'User-Agent': 'llmXive-research-agent/1.0'
    }

    try:
        response = requests.get(WIKIDATA_SPARQL_ENDPOINT, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('results', {}).get('bindings', [])
    except Exception as e:
        logger.error(f"Failed to fetch SPARQL data: {e}")
        raise

def fetch_wikidata_page_html() -> Optional[str]:
    """Fetch the raw HTML of the Wikidata item page for potential scraping."""
    import requests
    url = f"https://www.wikidata.org/wiki/{WIKIDATA_QID}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.warning(f"Failed to fetch HTML page: {e}")
        return None

def parse_wikidata_bindings(bindings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract relevant fields from SPARQL bindings."""
    results = []
    for binding in bindings:
        record = {}
        for var, value in binding.items():
            if 'value' in value:
                # Clean up URIs if present
                val = value['value']
                if val.startswith("http"):
                    # Extract ID from URI if it's a reference
                    record[var] = val
                else:
                    record[var] = val
            if 'type' in value:
                record[f"{var}_type"] = value['type']
        results.append(record)
    return results

def extract_from_html(html_content: str) -> Dict[str, Any]:
    """
    Parse HTML content to extract additional metadata not available via SPARQL.
    Looks for specific data-attributes or table structures typical of Wikidata.
    """
    from bs4 import BeautifulSoup
    import re

    if not html_content:
        return {}

    soup = BeautifulSoup(html_content, 'html.parser')
    extracted = {}

    # Try to find the 'statements' section
    statements_div = soup.find('div', {'class': 'wikibase-statements'})
    if statements_div:
        # Look for specific P-IDs related to statistics (e.g., sample size, p-value if manually added)
        # This is a heuristic as Wikidata items for papers might not have these specific fields populated
        # We look for any table rows that might contain numerical data
        rows = statements_div.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                prop_label = cells[0].get_text(strip=True)
                val_text = cells[1].get_text(strip=True)
                extracted[prop_label] = val_text

    # Extract title and description
    title_tag = soup.find('h1', {'class': 'wikibase-entity-title'})
    if title_tag:
        extracted['title'] = title_tag.get_text(strip=True)

    desc_tag = soup.find('div', {'class': 'wikibase-entitydescription'})
    if desc_tag:
        extracted['description'] = desc_tag.get_text(strip=True)

    return extracted

def main():
    """Main entry point for the verification script."""
    logger.info(f"Starting verification for {WIKIDATA_QID}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Define SPARQL Query to get basic info about the item
    # We look for properties like: instance of, author, publication date, etc.
    # If specific statistical claims exist as properties, we would query those.
    query = f"""
    SELECT ?item ?itemLabel ?author ?publicationDate ?description
    WHERE {{
      VALUES ?item {{ wd:{WIKIDATA_QID} }}
      OPTIONAL {{ ?item wdt:P50 ?author }}
      OPTIONAL {{ ?item wdt:P577 ?publicationDate }}
      OPTIONAL {{ ?item schema:description ?description . FILTER (lang(?description) = "en") }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    """

    try:
        bindings = fetch_wikidata_sparql(query)
        parsed_data = parse_wikidata_bindings(bindings)
    except Exception as e:
        logger.error(f"SPARQL query failed: {e}")
        parsed_data = []

    # 2. Fetch HTML for additional context if needed
    html_content = fetch_wikidata_page_html()
    html_extracted = extract_from_html(html_content)

    # 3. Combine data
    final_records = []
    for row in parsed_data:
        row.update(html_extracted)
        row['source'] = 'wikidata_sparql'
        row['fetch_timestamp'] = datetime.utcnow().isoformat()
        row['wikidata_qid'] = WIKIDATA_QID
        final_records.append(row)

    # If no SPARQL data, create a minimal record from HTML
    if not final_records and html_extracted:
        final_records.append({
            'source': 'wikidata_html',
            'fetch_timestamp': datetime.utcnow().isoformat(),
            'wikidata_qid': WIKIDATA_QID,
            **html_extracted
        })

    # 4. Write CSV
    if final_records:
        fieldnames = list(final_records[0].keys())
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(final_records)
        logger.info(f"Written {len(final_records)} records to {OUTPUT_CSV}")

    # 5. Write JSON Metadata
    metadata = {
        'qid': WIKIDATA_QID,
        'fetch_time': datetime.utcnow().isoformat(),
        'sparql_count': len(parsed_data),
        'html_fields': list(html_extracted.keys()),
        'status': 'completed' if final_records else 'empty'
    }
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Written metadata to {OUTPUT_JSON}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
