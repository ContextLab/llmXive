import json
import os
import sys
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from sibling modules as per API surface
from utils.osf_client import fetch_with_backoff, get_study_metadata, OSFClientError
from utils.data_hygiene import ensure_directory

class ExtractionError(Exception):
    """Custom exception for extraction failures."""
    pass

def extract_planned_metrics(text: str) -> Dict[str, Any]:
    """
    Extract planned power, target_n, and effect_size_assumption from text.
    Uses regex hybrid approach as implemented in T013.
    """
    if not text:
        return {}

    result = {}

    # Pattern for planned power (e.g., "power=0.80", "80% power", "target power: 0.9")
    power_patterns = [
        r'power\s*[=:]\s*(0\.\d+|\d+)',
        r'target\s+power\s*[=:]\s*(0\.\d+|\d+)',
        r'\b(\d{1,2})\s*%\s+power',
    ]
    for pattern in power_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1)
            if '%' in text[max(0, match.start()-10):match.end()]:
                result['planned_power'] = float(val) / 100.0
            else:
                result['planned_power'] = float(val)
            break

    # Pattern for target N (e.g., "N=50", "sample size: 100", "n = 30")
    n_patterns = [
        r'[Nn]\s*[=:]\s*(\d+)',
        r'sample\s+size\s*[=:]\s*(\d+)',
        r'target\s+sample\s+size\s*[=:]\s*(\d+)',
        r'n\s*[=:]\s*(\d+)',
    ]
    for pattern in n_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['target_n'] = int(match.group(1))
            break

    # Pattern for effect size (e.g., "d=0.5", "effect size: 0.3", "r = 0.4")
    effect_patterns = [
        r'd\s*[=:]\s*([0-9.]+)',
        r'effect\s+size\s*[=:]\s*([0-9.]+)',
        r'r\s*[=:]\s*([0-9.]+)',
        r'f\s*[=:]\s*([0-9.]+)',
    ]
    for pattern in effect_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['effect_size_assumption'] = float(match.group(1))
            break

    return result

def fetch_study_pre_registration_data(osf_id: str) -> Dict[str, Any]:
    """
    Fetch study metadata and pre-registration content from OSF.
    Prioritizes 'Primary Pre-registration' if multiple exist.
    """
    try:
        metadata = get_study_metadata(osf_id)
        if not metadata:
            raise ExtractionError(f"Metadata not found for OSF ID: {osf_id}")

        # Extract pre-registrations
        pre_registrations = metadata.get('pre_registrations', [])
        if not pre_registrations:
            # Fallback to linked registrations if pre_registrations key missing
            pre_registrations = metadata.get('registrations', [])

        if not pre_registrations:
            return {
                'osf_id': osf_id,
                'missing_planned_data': True,
                'reason': 'No pre-registrations found',
                'primary_content': None,
                'primary_source': None
            }

        # Prioritize "Primary Pre-registration"
        primary = None
        for reg in pre_registrations:
            title = reg.get('title', '').lower()
            if 'primary' in title or 'main' in title:
                primary = reg
                break

        # If no primary found, take the first one (or the most recent if date available)
        if not primary:
            # Sort by date if available, else take first
            pre_registrations.sort(key=lambda x: x.get('created', ''), reverse=True)
            primary = pre_registrations[0]

        # Fetch the content of the primary pre-registration
        # Assuming the content is in a specific field or linked file
        # For OSF, content might be in 'data' or linked via 'files'
        content_text = None
        source_info = f"Registration: {primary.get('title', 'Unknown')}"

        # Attempt to extract text from the registration's data blob
        # OSF API often returns content in 'data.attributes.description' or similar
        if 'data' in primary:
            data_blob = primary['data']
            if isinstance(data_blob, dict):
                # Try common fields
                for field in ['description', 'content', 'text', 'body']:
                    if field in data_blob:
                        content_text = data_blob[field]
                        break
            elif isinstance(data_blob, str):
                content_text = data_blob

        # If content is still None, try to fetch via linked file ID if present
        if not content_text and 'files' in primary:
            # Placeholder for file fetching logic (T017/T018 will handle detailed file retrieval)
            # For now, we flag that content could not be extracted inline
            pass

        if not content_text:
            return {
                'osf_id': osf_id,
                'missing_planned_data': True,
                'reason': 'Pre-registration content not accessible or empty',
                'primary_source': source_info,
                'primary_content': None
            }

        return {
            'osf_id': osf_id,
            'missing_planned_data': False,
            'primary_content': content_text,
            'primary_source': source_info,
            'raw_registration': primary
        }

    except OSFClientError as e:
        raise ExtractionError(f"OSF Client error for {osf_id}: {str(e)}")
    except Exception as e:
        raise ExtractionError(f"Unexpected error fetching {osf_id}: {str(e)}")

def extract_batch(osf_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Process a batch of OSF IDs, extracting planned metrics and handling missing data.
    Returns a list of processed records.
    """
    results = []
    for osf_id in osf_ids:
        try:
            data = fetch_study_pre_registration_data(osf_id)
            if not data.get('missing_planned_data') and data.get('primary_content'):
                metrics = extract_planned_metrics(data['primary_content'])
                data.update(metrics)
            results.append(data)
        except ExtractionError as e:
            results.append({
                'osf_id': osf_id,
                'missing_planned_data': True,
                'reason': str(e),
                'primary_content': None
            })
    return results

def main():
    """
    Main entry point for the extraction task.
    Reads OSF IDs from a config or argument, processes them, and writes to data/derived.
    """
    if len(sys.argv) < 2:
        print("Usage: python extraction.py <osf_id1> [osf_id2 ...]")
        sys.exit(1)

    osf_ids = sys.argv[1:]
    output_dir = Path("data/derived")
    ensure_directory(output_dir)
    output_file = output_dir / "study_records_raw.json"

    print(f"Processing {len(osf_ids)} studies...")
    records = extract_batch(osf_ids)

    # Validate and log missing data stats
    missing_count = sum(1 for r in records if r.get('missing_planned_data'))
    print(f"Extraction complete. {missing_count}/{len(records)} records have missing planned data.")

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, default=str)

    print(f"Output written to {output_file}")

if __name__ == "__main__":
    main()
