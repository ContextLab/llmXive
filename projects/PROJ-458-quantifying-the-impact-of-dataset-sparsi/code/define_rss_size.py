"""
Define RSS_SIZE by performing a quick resource check.

This script estimates the memory required to hold a large dataset of material entries
and determines a safe Representative Stratified Sample (RSS) size that fits within
typical CI/runner constraints (approx 7GB RAM available, targeting <2GB usage for safety).

It writes the final integer value to data/metadata/rss_config.json.
"""
import os
import sys
import json
import math
from pathlib import Path

# Add parent directory to path to allow imports from utils if needed, 
# though this script is self-contained for calculation.
project_root = Path(__file__).parent.parent
metadata_dir = project_root / "data" / "metadata"

# Ensure metadata directory exists
metadata_dir.mkdir(parents=True, exist_ok=True)

def estimate_row_size_bytes():
    """
    Estimate the memory footprint of a single row in the processed dataset.
    
    Based on the data model:
    - material_id: str (~10-20 bytes)
    - composition: str (~20-50 bytes)
    - formation_energy: float64 (8 bytes)
    - dft_computed: bool (1 byte)
    - Descriptors (from matminer ElementalPropertyFeatureExtractor):
      Typically ~100-200 float64 features depending on the exact extractor settings.
      Let's assume a conservative average of 150 features.
      150 * 8 bytes = 1200 bytes.
    - Overhead for Python object/pandas index: ~100 bytes per row.
    
    Total estimated per row: ~1.5 KB.
    """
    # Conservative estimate: 1.5 KB per row
    return 1536 

def calculate_rss_size():
    """
    Calculate the RSS size based on memory constraints.
    
    Assumptions:
    - Available RAM for this process: ~4 GB (safe limit for a 7GB total system)
    - Target utilization: 50% of available RAM for the dataframe to allow for overhead
    - Overhead factor: 2.0x (pandas memory usage can be higher than raw data size)
    
    Target Data Size = 2.0 GB = 2 * 1024^3 bytes
    Row Size = 1.5 KB
    Max Rows = Target / Row Size
    """
    target_memory_gb = 2.0
    target_memory_bytes = target_memory_gb * (1024 ** 3)
    row_size_bytes = estimate_row_size_bytes()
    
    max_rows = int(target_memory_bytes / row_size_bytes)
    
    # Round down to a clean number (e.g., nearest 1000)
    rss_size = (max_rows // 1000) * 1000
    
    return rss_size

def main():
    """Main execution function."""
    print("Starting RSS Size calculation...")
    
    rss_size = calculate_rss_size()
    
    # Define output path
    output_path = metadata_dir / "rss_config.json"
    
    # Prepare data
    config_data = {
        "rss_size": rss_size,
        "reason": f"Estimated for ~{rss_size} rows to fit within 2GB memory target. "
                  f"Row size estimate: {estimate_row_size_bytes()} bytes."
    }
    
    # Write to file
    with open(output_path, "w") as f:
        json.dump(config_data, f, indent=2)
    
    print(f"RSS Size determined: {rss_size}")
    print(f"Configuration written to: {output_path}")
    
    # Verification
    if output_path.exists():
        with open(output_path, "r") as f:
            loaded = json.load(f)
        assert isinstance(loaded["rss_size"], int), "rss_size must be an integer"
        assert loaded["rss_size"] > 0, "rss_size must be positive"
        print("Verification passed: rss_config.json contains valid integer.")
    else:
        raise FileNotFoundError(f"Failed to create {output_path}")

if __name__ == "__main__":
    main()
