"""
Script to verify Wikidata item Q19873191 (Statistical Significance in A/B Testing).
Fetches metadata via SPARQL and the main page HTML to extract publication details.
Outputs a CSV with validation results and a JSON summary.
"""
import csv
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import project logger
from code.src.utils.logger import get_default_logger, AuditLogger

# Configure logging for this script
logger = get_default_logger("verify_wikidata_q19873191")

WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_ITEM_URL = "https://www.wikidata.org/wiki/Q19873191"
OUTPUT_DIR = Path("data")
OUTPUT_CSV = OUTPUT_DIR / "wikidata_q19873191_validation.csv"
OUTPUT_JSON = OUTPUT_DIR / "wikidata_q19873191_summary.json"

# SPARQL query to fetch properties for Q19873191
SPARQL_QUERY = """
SELECT ?item ?itemLabel ?publishedIn ?publishedDate ?doi ?authorLabel ?description
WHERE {
  VALUES ?item { wd:Q19873191 }
  OPTIONAL { ?item wdt:P1433 ?publishedIn . }
  OPTIONAL { ?item wdt:P577 ?publishedDate . }
  OPTIONAL { ?item wdt:P356 ?doi . }
  OPTIONAL { ?item wdt:P50 ?author . }
  OPTIONAL { ?item wdt:P170 ?author . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
LIMIT 100
"""

def fetch_wikidata_sparql(query: str) -> List[Dict[str, Any]]:
    """Fetch data from Wikidata SPARQL endpoint."""
    import requests
    params = {
        'query': query,
        'format': 'json'
    }
    headers = {
        'Accept': 'application/sparql-results+json',
        'User-Agent': 'llmXive-Research-Agent/1.0'
    }
    
    try:
        response = requests.get(WIKIDATA_SPARQL_ENDPOINT, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('results', {}).get('bindings', [])
    except requests.exceptions.RequestException as e:
        logger.error(f"SPARQL request failed: {e}")
        return []

def fetch_wikidata_page_html(url: str) -> Optional[str]:
    """Fetch the raw HTML of the Wikidata page."""
    import requests
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"HTML fetch failed: {e}")
        return None

def parse_wikidata_bindings(bindings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse SPARQL bindings into a list of dictionaries."""
    results = []
    for binding in bindings:
        record = {}
        for key, value in binding.items():
            if key in ['item', 'publishedIn', 'author']:
                record[key] = value.get('value', '').split('/')[-1]
            elif key in ['itemLabel', 'authorLabel', 'description']:
                record[key] = value.get('value', '')
            elif 'Date' in key or 'doi' in key:
                record[key] = value.get('value', '')
        if record:
            results.append(record)
    return results

def extract_from_html(html_content: str) -> Dict[str, Any]:
    """Extract basic metadata from HTML if needed (fallback)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    title = soup.find('h1', {'id': 'firstHeading'})
    title_text = title.get_text() if title else "Unknown"
    
    # Look for description meta tag
    desc_meta = soup.find('meta', attrs={'name': 'description'})
    description = desc_meta.get('content', '') if desc_meta else ""
    
    return {
        "title": title_text,
        "description": description,
        "url": WIKIDATA_ITEM_URL
    }

def main():
    """Main execution function."""
    logger.info(f"Starting verification for {WIKIDATA_ITEM_URL}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch via SPARQL
    bindings = fetch_wikidata_sparql(SPARQL_QUERY)
    parsed_data = parse_wikidata_bindings(bindings)
    
    # 2. Fetch HTML for additional context
    html_content = fetch_wikidata_page_html(WIKIDATA_ITEM_URL)
    html_meta = extract_from_html(html_content) if html_content else {}

    # 3. Combine data
    combined_records = []
    if parsed_data:
        for record in parsed_data:
            record.update({
                "source": "sparql",
                "verified_at": datetime.utcnow().isoformat(),
                "html_title": html_meta.get("title"),
                "html_description": html_meta.get("description")
            })
            combined_records.append(record)
    else:
        # Fallback if SPARQL returns nothing but HTML exists
        combined_records.append({
            "source": "html_fallback",
            "verified_at": datetime.utcnow().isoformat(),
            "html_title": html_meta.get("title"),
            "html_description": html_meta.get("description"),
            "error": "SPARQL returned no bindings"
        })

    # 4. Write CSV
    if combined_records:
        fieldnames = list(combined_records[0].keys())
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(combined_records)
        logger.info(f"CSV written to {OUTPUT_CSV}")
    else:
        logger.error("No data retrieved to write CSV.")

    # 5. Write JSON Summary
    summary = {
        "item_id": "Q19873191",
        "item_url": WIKIDATA_ITEM_URL,
        "retrieved_at": datetime.utcnow().isoformat(),
        "record_count": len(combined_records),
        "data": combined_records,
        "status": "completed" if combined_records else "failed"
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"JSON summary written to {OUTPUT_JSON}")

    return 0

if __name__ == "__main__":
    sys.exit(main())