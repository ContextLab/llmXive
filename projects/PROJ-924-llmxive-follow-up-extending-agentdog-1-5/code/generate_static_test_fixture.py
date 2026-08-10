"""
T012c: Generate static test fixture from real data (AdvBench/HF4).

This script fetches real data from AdvBench and HF4 using the existing
data_loader functions, merges them, adds deterministic timestamps,
and saves the result to data/test_static_logs.json.

The output file contains records with: log_id, text, label, timestamp.
"""
import json
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone

# Import from existing project modules
from data_loader import fetch_advbench, fetch_hf4, generate_deterministic_timestamp
from config import get_path, set_seed
from utils import save_json_file

# Ensure reproducibility
set_seed(42)

def generate_log_id(record_index: int, source: str) -> str:
    """Generate a deterministic UUID based on index and source."""
    seed_str = f"{source}-{record_index}"
    # Use UUID5 with a namespace for determinism
    namespace = uuid.NAMESPACE_DNS
    return str(uuid.uuid5(namespace, seed_str))

def prepare_record(
    text: str, 
    label: str, 
    source: str, 
    index: int, 
    existing_timestamp: Any = None
) -> Dict[str, Any]:
    """Prepare a single record with all required fields."""
    log_id = generate_log_id(index, source)
    
    # Generate timestamp if not provided or invalid
    if existing_timestamp is None:
        # Use the deterministic timestamp generator from data_loader
        timestamp_str = generate_deterministic_timestamp(log_id)
    else:
        # If timestamp exists, use it; otherwise generate
        timestamp_str = str(existing_timestamp)
    
    return {
        "log_id": log_id,
        "text": text,
        "label": label,
        "timestamp": timestamp_str
    }

def fetch_and_prepare_advbench() -> List[Dict[str, Any]]:
    """Fetch AdvBench data and prepare records."""
    try:
        data = fetch_advbench()
    except Exception as e:
        print(f"Error fetching AdvBench: {e}", file=sys.stderr)
        raise
    
    records = []
    for i, item in enumerate(data):
        # AdvBench typically has 'prompt' or 'text' field and is malicious
        text = item.get('prompt') or item.get('text') or item.get('input', '')
        if not text:
            continue
        
        # AdvBench contains attack prompts, label them as 'malicious'
        record = prepare_record(
            text=text,
            label='malicious',
            source='advbench',
            index=i,
            existing_timestamp=item.get('timestamp')
        )
        records.append(record)
    
    return records

def fetch_and_prepare_hf4() -> List[Dict[str, Any]]:
    """Fetch HF4 data and prepare records."""
    try:
        data = fetch_hf4()
    except Exception as e:
        print(f"Error fetching HF4: {e}", file=sys.stderr)
        raise
    
    records = []
    for i, item in enumerate(data):
        text = item.get('text') or item.get('prompt') or item.get('input', '')
        if not text:
            continue
        
        # HF4 contains benign logs, label them as 'benign'
        record = prepare_record(
            text=text,
            label='benign',
            source='hf4',
            index=i,
            existing_timestamp=item.get('timestamp')
        )
        records.append(record)
    
    return records

def generate_static_fixture():
    """Main function to generate the static test fixture."""
    print("Fetching AdvBench data...")
    advbench_records = fetch_and_prepare_advbench()
    print(f"  Retrieved {len(advbench_records)} records from AdvBench")
    
    print("Fetching HF4 data...")
    hf4_records = fetch_and_prepare_hf4()
    print(f"  Retrieved {len(hf4_records)} records from HF4")
    
    # Combine all records
    all_records = advbench_records + hf4_records
    print(f"Total records: {len(all_records)}")
    
    # Validate required fields
    required_fields = {'log_id', 'text', 'label', 'timestamp'}
    for i, record in enumerate(all_records):
        missing = required_fields - set(record.keys())
        if missing:
            raise ValueError(f"Record {i} missing fields: {missing}")
    
    # Get output path
    output_path = get_path('data/test_static_logs.json')
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    print(f"Saving to {output_path}...")
    save_json_file(all_records, output_path)
    
    print(f"Successfully generated static test fixture with {len(all_records)} records")
    return all_records

def main():
    """Entry point for the script."""
    try:
        generate_static_fixture()
    except Exception as e:
        print(f"Failed to generate static test fixture: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
