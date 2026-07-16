"""
Script to generate a static test fixture for User Story 1 (US-01) testing.
This script fetches real data from AdvBench and HF4 datasets, selects a representative
subset, and saves it to data/test_static_logs.json.

Requirements:
- Real data only: Uses fetch_advbench and fetch_hf4 from data_loader.
- No synthetic fallbacks: If data fetch fails, the script raises an exception.
- Output: data/test_static_logs.json containing a list of log records.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import from sibling module (must exist per API surface)
from data_loader import fetch_advbench, fetch_hf4
from config import get_output_path, ensure_directories

def generate_static_fixture(output_path: str, sample_size: int = 100) -> None:
    """
    Generate a static test fixture from real AdvBench and HF4 data.

    Args:
        output_path: Path to the output JSON file.
        sample_size: Number of samples to extract from each dataset.
    """
    # Ensure output directory exists
    ensure_directories(output_path)

    print(f"Fetching real data for static fixture generation...")
    
    # Fetch real data - these functions must raise on failure (no synthetic fallback)
    try:
        advbench_data = fetch_advbench()
        print(f"Successfully fetched AdvBench data: {len(advbench_data)} records")
    except Exception as e:
        print(f"ERROR: Failed to fetch AdvBench data: {e}")
        raise

    try:
        hf4_data = fetch_hf4()
        print(f"Successfully fetched HF4 data: {len(hf4_data)} records")
    except Exception as e:
        print(f"ERROR: Failed to fetch HF4 data: {e}")
        raise

    # Select representative samples
    # Take first N samples from each dataset (real data, not synthetic)
    advbench_sample = advbench_data[:sample_size]
    hf4_sample = hf4_data[:sample_size]

    # Format logs with metadata
    static_logs = []

    for i, record in enumerate(advbench_sample):
        log_entry = {
            "log_id": f"advbench_{i:04d}",
            "text": record.get("text", record.get("prompt", "")),
            "source": "advbench",
            "label": "benign" if "attack" not in record.get("prompt", "").lower() else "attack"
        }
        static_logs.append(log_entry)

    for i, record in enumerate(hf4_sample):
        log_entry = {
            "log_id": f"hf4_{i:04d}",
            "text": record.get("text", record.get("prompt", "")),
            "source": "hf4",
            "label": "benign" if "attack" not in record.get("prompt", "").lower() else "attack"
        }
        static_logs.append(log_entry)

    # Write to output file
    output_file = Path(output_path)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(static_logs, f, indent=2, ensure_ascii=False)

    print(f"Generated static test fixture: {output_path}")
    print(f"Total records: {len(static_logs)}")
    print(f"  - AdvBench: {len(advbench_sample)}")
    print(f"  - HF4: {len(hf4_sample)}")

if __name__ == "__main__":
    # Default output path from project config
    output_path = get_output_path("test_static_logs.json")
    generate_static_fixture(output_path)
