import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set

# Add project root to path if needed for imports, though this script is standalone
# relative to the project structure.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PAIRED_DIR = PROJECT_ROOT / "data" / "paired"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_PAIRED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_geo_search_results() -> Dict[str, Any]:
    """Load GEO search results for Arabidopsis and Solanum."""
    results = {}
    geo_files = [
        DATA_RAW_DIR / "geo_arabidopsis_search.json",
        DATA_RAW_DIR / "geo_solanum_search.json"
    ]
    
    for file_path in geo_files:
        if not file_path.exists():
            logger.warning(f"Geo search file not found: {file_path}")
            continue
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Extract series IDs and potentially sample IDs if available in search results
            # Typically search results return series IDs (GSE...). We need to assume
            # we might need to fetch metadata, but for this task we assume the search
            # results might contain sample info or we extract what we can.
            # Based on T002/T003, these files contain IDs.
            # We will treat the content as a list of series objects or IDs.
            if isinstance(data, list):
                results[file_path.stem] = data
            elif isinstance(data, dict) and 'results' in data:
                results[file_path.stem] = data['results']
            else:
                results[file_path.stem] = data
    
    return results

def load_mw_search_results() -> Dict[str, Any]:
    """Load Metabolomics Workbench search results."""
    file_path = DATA_RAW_DIR / "mw_search.json"
    if not file_path.exists():
        logger.warning(f"MW search file not found: {file_path}")
        return {}
    
    with open(file_path, 'r') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

def extract_geo_biosample_ids(geo_data: List[Any]) -> Set[str]:
    """
    Extract biosample IDs from GEO search results.
    Note: GEO search results often only give Series (GSE). 
    In a real scenario, we would need to fetch GSE metadata to get GSM (samples).
    However, T002/T003 output is 'IDs'. If they are GSE IDs, we cannot get sample IDs
    without a download step (T023).
    
    CRITICAL: The task requires comparing biosample identifiers. 
    If the search files only contain GSE IDs, we must acknowledge that sample-level
    pairing is impossible without downloading the series metadata.
    
    Strategy:
    1. Check if the loaded data contains sample-level info (GSM).
    2. If only GSE, we assume the 'search results' might have included a 'samples' field
       or we must simulate the fetch if the API allows, OR we report that we cannot
       proceed without T023 (Download).
    
    Given the constraint "Real data only" and "No fabrication", and that T023 is not done:
    We will attempt to parse the existing JSON. If it lacks sample IDs, we will log
    that sample-level pairing requires T023, but we will try to extract any available
    identifiers. If the JSON structure from T002/T003 is just a list of GSE strings,
    we cannot match samples.
    
    However, looking at the task T007 description: "comparing biosample identifiers from GEO and Metabolomics metadata".
    If the metadata isn't downloaded yet, we can't do this. 
    
    Assumption: The search results JSON from T002/T003 might contain a 'samples' list or similar
    if the search tool was extended, OR we are expected to fail gracefully if data is missing.
    
    Let's assume the search results contain a structure like:
    [{"accession": "GSE123", "samples": ["GSM1", "GSM2"]}, ...]
    OR we just have GSEs and we must report 0 samples.
    
    We will implement a robust extractor that looks for 'samples', 'gsm', or 'biosample' keys.
    """
    ids = set()
    for item in geo_data:
        if isinstance(item, str):
            # Just a GSE ID, no sample info
            continue
        if isinstance(item, dict):
            # Check common keys for samples
            if 'samples' in item:
                ids.update(item['samples'])
            elif 'gsm' in item:
                if isinstance(item['gsm'], list):
                    ids.update(item['gsm'])
                else:
                    ids.add(item['gsm'])
            elif 'biosample' in item:
                if isinstance(item['biosample'], list):
                    ids.update(item['biosample'])
                else:
                    ids.add(item['biosample'])
            # Fallback: if the item itself is a sample ID (unlikely for GSE search)
            if 'accession' in item:
                acc = item['accession']
                if acc.startswith('GSM'):
                    ids.add(acc)
    return ids

def extract_mw_biosample_ids(mw_data: List[Any]) -> Set[str]:
    """
    Extract biosample IDs from Metabolomics Workbench results.
    MW experiments usually have a 'samples' or 'biosamples' field.
    """
    ids = set()
    for item in mw_data:
        if isinstance(item, str):
            continue
        if isinstance(item, dict):
            # Check for sample lists
            if 'samples' in item:
                ids.update(item['samples'])
            elif 'biosamples' in item:
                ids.update(item['biosamples'])
            elif 'sample_ids' in item:
                ids.update(item['sample_ids'])
            # MW often uses 'study' or 'experiment' with nested samples
            if 'study' in item and isinstance(item['study'], dict):
                if 'samples' in item['study']:
                    ids.update(item['study']['samples'])
    return ids

def run_pairing_feasibility():
    """
    Main function to verify sample-level pairing feasibility.
    1. Load GEO and MW search results.
    2. Extract biosample IDs.
    3. Compare to find matches.
    4. Calculate pairing rate.
    5. Write reports.
    """
    logger.info("Starting pairing feasibility analysis (T007)...")
    
    geo_data = load_geo_search_results()
    mw_data = load_mw_search_results()
    
    if not geo_data and not mw_data:
        logger.error("No search results found. Cannot proceed with pairing.")
        # Create empty report
        report = {
            "status": "failed",
            "reason": "No search results found in data/raw",
            "geo_samples": 0,
            "mw_samples": 0,
            "matched_samples": 0,
            "pairing_rate": 0.0
        }
        with open(DATA_PAIRED_DIR / "pairing_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        return

    # Flatten geo data if it's a dict of lists
    all_geo_items = []
    for k, v in geo_data.items():
        if isinstance(v, list):
            all_geo_items.extend(v)
        else:
            all_geo_items.append(v)
    
    # Extract IDs
    geo_ids = extract_geo_biosample_ids(all_geo_items)
    mw_ids = extract_mw_biosample_ids(mw_data)
    
    logger.info(f"Found {len(geo_ids)} potential GEO sample IDs.")
    logger.info(f"Found {len(mw_ids)} potential MW sample IDs.")
    
    # If no IDs found in search results (common if search only returns GSE/Study IDs),
    # we cannot match samples. We must report this.
    if len(geo_ids) == 0 or len(mw_ids) == 0:
        logger.warning("No sample-level IDs found in search results. Pairing requires T023 (download).")
        report = {
            "status": "incomplete",
            "reason": "Search results do not contain sample-level IDs (GSM/Biosample). Download (T023) required.",
            "geo_samples": len(geo_ids),
            "mw_samples": len(mw_ids),
            "matched_samples": 0,
            "pairing_rate": 0.0,
            "details": []
        }
        log_details = {
            "timestamp": "T007",
            "geo_source": list(geo_data.keys()),
            "mw_source": "mw_search.json",
            "error": "Sample IDs not present in search results"
        }
    else:
        # Perform matching
        # Note: In real scenarios, GEO and MW might use different ID formats.
        # We assume a direct string match for this feasibility check.
        matched = geo_ids.intersection(mw_ids)
        matched_list = list(matched)
        
        # Calculate rate based on the smaller set or total union?
        # Task says ">=95% match". Usually implies: (Matched / Total Required) or (Matched / Total Available).
        # We'll calculate: Matched / min(GEO, MW) to see overlap efficiency, 
        # and Matched / (GEO + MW) for overall coverage.
        # The constraint is ">=95% match". Let's assume we need 95% of GEO samples to have MW data.
        total_geo = len(geo_ids)
        total_mw = len(mw_ids)
        total_matched = len(matched)
        
        if total_geo > 0:
            pairing_rate = total_matched / total_geo
        else:
            pairing_rate = 0.0
        
        report = {
            "status": "success" if pairing_rate >= 0.95 else "insufficient",
            "geo_samples": total_geo,
            "mw_samples": total_mw,
            "matched_samples": total_matched,
            "pairing_rate": pairing_rate,
            "threshold": 0.95,
            "matched_ids": matched_list[:50]  # Limit log size
        }
        
        log_details = {
            "timestamp": "T007",
            "geo_count": total_geo,
            "mw_count": total_mw,
            "matched_count": total_matched,
            "rate": pairing_rate,
            "details": [
                {"geo_id": g, "mw_id": g} for g in matched_list[:100]
            ]
        }

    # Write pairing report
    report_path = DATA_PAIRED_DIR / "pairing_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Pairing report written to {report_path}")
    
    # Write log details
    log_path = LOGS_DIR / "data_pairing.json"
    # Append to existing log if it exists? Or overwrite? 
    # Task says "log details to ...". Overwriting for now as it's a specific run log.
    # But usually logs are append. Let's overwrite with the full state of this run.
    with open(log_path, 'w') as f:
        json.dump(log_details, f, indent=2)
    logger.info(f"Pairing details logged to {log_path}")

    if pairing_rate < 0.95:
        logger.warning(f"Pairing rate {pairing_rate:.2%} is below 95% threshold.")
    else:
        logger.info(f"Pairing rate {pairing_rate:.2%} meets 95% threshold.")

if __name__ == "__main__":
    run_pairing_feasibility()
