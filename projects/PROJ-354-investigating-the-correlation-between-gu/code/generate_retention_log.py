"""
Task T016: Generate cohort retention log.

This script loads the preprocessed cohort data (after filtering and ILR transformation)
and generates a JSON report containing retention counts and rates as required by SC-001.

It assumes the following artifacts exist from previous tasks (T013, T014, T015, T015.5):
- data/processed/zero_replaced_counts.parquet
- data/processed/ilr_coordinates.parquet
- data/processed/cohort_with_age_groups.parquet

The script calculates:
1. Initial cohort size (from raw download if available, or inferred from the first processed file).
2. Size after antibiotic filtering (T013).
3. Size after missingness filtering (T013).
4. Final cohort size (after all preprocessing).
5. Retention rate (Final / Initial).

Since T013 logs exclusion counts, we reconstruct the counts by comparing the sizes
of the intermediate files if the raw file is not kept, or by reading the exclusion log
if it was written. For this implementation, we assume the pipeline writes a temporary
log or we infer from the file sizes of the processed steps.

To be robust, this script will:
1. Check for the existence of `data/processed/cohort_with_age_groups.parquet` (Final).
2. Check for `data/processed/ilr_coordinates.parquet` (Pre-final, same size).
3. Check for `data/processed/zero_replaced_counts.parquet` (Post-zero-replace, pre-filter? 
   Actually T013 says "filter cohort... exclude recent antibiotic users". T014 is zero-replace.
   Wait, the order in tasks.md:
   T013: Filter cohort (exclude antibiotics, missingness).
   T014: Zero-replaced counts.
   T015: ILR.
   
   So: Raw -> Filtered (T013) -> Zero-Replaced (T014) -> ILR (T015).
   
   We need the "Initial" count. This usually comes from the raw download (T012).
   If T012 saved a raw file, we use it. If not, we might need to estimate or assume
   the user has a `data/raw/` file.
   
   Let's assume the raw data is available at `data/raw/microbiome_raw.parquet` or similar
   based on T012. If not, we will attempt to load the first available file and mark
   initial as unknown or infer from context.
   
   However, the most reliable way to get the "Initial" count for a retention log
   is to read the raw file count.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_directories
from utils.logging import get_logger, init_logging

# Initialize logging
init_logging()
logger = get_logger(__name__)

def load_parquet_count(file_path: Path) -> int:
    """Load a parquet file and return the row count."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return 0
    try:
        # Use chunked reading to avoid memory issues if file is huge, 
        # though we just need the count.
        # For parquet, we can often just read metadata or a small sample.
        # But pandas read_parquet is standard.
        df = pd.read_parquet(file_path)
        return len(df)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        raise

def get_retention_stats() -> Dict[str, Any]:
    """
    Calculate retention statistics based on the pipeline outputs.
    
    Expected flow:
    1. Raw Data (T012) -> `data/raw/microbiome_raw.parquet` (or similar)
    2. Filtered Data (T013) -> `data/processed/filtered_counts.parquet` (implied intermediate)
       OR T013 might output directly to the zero-replace input.
       The tasks say:
       T013: "Output: data/processed/zero_replaced_counts.parquet" (Wait, T014 says that).
       Let's re-read T013: "Implement code/preprocess.py to filter cohort...". It doesn't explicitly
       name an output file, but T014 says "Output: data/processed/zero_replaced_counts.parquet".
       T015 says "Output: data/processed/ilr_coordinates.parquet".
       
       Assumption:
       - Raw: data/raw/microbiome_data.parquet (from T012)
       - Filtered: data/processed/filtered_cohort.parquet (Intermediate from T013, not explicitly named in T013 description but needed for flow)
       - Zero-Replaced: data/processed/zero_replaced_counts.parquet (T014)
       - ILR: data/processed/ilr_coordinates.parquet (T015)
       - Final: data/processed/cohort_with_age_groups.parquet (T015.5)
       
       If intermediate files are not saved, we might only have Raw and Final.
       We will try to load the most granular files available.
    """
    # Define paths based on project conventions
    raw_path = get_path("data/raw/microbiome_data.parquet")
    # If raw is not there, try other common names from T012
    if not raw_path.exists():
        raw_path = get_path("data/raw/microbiome_raw.parquet")
    
    # Intermediate/Filtered (if saved by T013)
    filtered_path = get_path("data/processed/filtered_cohort.parquet")
    
    # Zero Replaced (T014)
    zero_replace_path = get_path("data/processed/zero_replaced_counts.parquet")
    
    # ILR (T015)
    ilr_path = get_path("data/processed/ilr_coordinates.parquet")
    
    # Final (T015.5)
    final_path = get_path("data/processed/cohort_with_age_groups.parquet")

    stats = {
        "raw_count": 0,
        "filtered_count": 0,
        "zero_replaced_count": 0,
        "ilr_count": 0,
        "final_count": 0,
        "retention_rate": 0.0,
        "exclusions": {
            "antibiotic_users": 0,
            "missing_data": 0,
            "other": 0
        }
    }

    # 1. Get Raw Count
    if raw_path.exists():
        stats["raw_count"] = load_parquet_count(raw_path)
        logger.info(f"Raw cohort count: {stats['raw_count']}")
    else:
        logger.warning("Raw data file not found. Cannot calculate exact retention rate from raw.")
        # Fallback: Assume raw count is the final count + estimated exclusions? 
        # No, we must fail loudly or mark as unknown.
        stats["raw_count"] = None

    # 2. Get Filtered Count (if available)
    if filtered_path.exists():
        stats["filtered_count"] = load_parquet_count(filtered_path)
        logger.info(f"Filtered cohort count: {stats['filtered_count']}")
    
    # 3. Get Zero Replaced Count
    if zero_replace_path.exists():
        stats["zero_replaced_count"] = load_parquet_count(zero_replace_path)
        logger.info(f"Zero-replaced cohort count: {stats['zero_replaced_count']}")
    
    # 4. Get ILR Count
    if ilr_path.exists():
        stats["ilr_count"] = load_parquet_count(ilr_path)
        logger.info(f"ILR transformed cohort count: {stats['ilr_count']}")
    
    # 5. Get Final Count
    if final_path.exists():
        stats["final_count"] = load_parquet_count(final_path)
        logger.info(f"Final cohort count (with age groups): {stats['final_count']}")
    else:
        # If final is missing, we might use ILR as the final for the report if T015.5 failed
        if stats["ilr_count"] > 0:
            stats["final_count"] = stats["ilr_count"]
            logger.warning("Final cohort file missing, using ILR count as proxy.")
        else:
            logger.error("No processed cohort data found. Cannot generate retention log.")
            return stats

    # Calculate Retention Rate
    if stats["raw_count"] and stats["raw_count"] > 0:
        stats["retention_rate"] = stats["final_count"] / stats["raw_count"]
    else:
        stats["retention_rate"] = 0.0

    # Estimate exclusions if intermediate files are missing
    if stats["raw_count"] and stats["final_count"] > 0:
        total_excluded = stats["raw_count"] - stats["final_count"]
        # We don't know the split between antibiotic vs missing without the intermediate file.
        # We will log this as "unspecified" or try to infer if we have the filtered file.
        if stats["filtered_count"] > 0:
            # We have the filtered step
            stats["exclusions"]["antibiotic_users"] = stats["raw_count"] - stats["filtered_count"]
            stats["exclusions"]["missing_data"] = stats["filtered_count"] - stats["final_count"]
        else:
            # Cannot split, just record total
            stats["exclusions"]["other"] = total_excluded

    return stats

def main():
    """Main entry point for T016."""
    logger.info("Starting T016: Generating Cohort Retention Log")
    
    # Ensure output directory exists
    output_dir = get_path("results/validation")
    ensure_directories([output_dir])
    
    output_file = output_dir / "cohort_retention_log.json"
    
    try:
        stats = get_retention_stats()
        
        # Add metadata
        report = {
            "task_id": "T016",
            "spec_reference": "SC-001",
            "generated_at": pd.Timestamp.now().isoformat(),
            "retention_statistics": stats
        }
        
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Retention log generated successfully: {output_file}")
        print(f"Success: {output_file} created with {stats['final_count']} participants (Rate: {stats['retention_rate']:.2%})")
        
    except Exception as e:
        logger.error(f"Failed to generate retention log: {e}")
        raise

if __name__ == "__main__":
    main()
