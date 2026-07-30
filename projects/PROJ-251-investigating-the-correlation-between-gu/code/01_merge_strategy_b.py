import os
import sys
import logging
from pathlib import Path
import pandas as pd
import psutil
from typing import Tuple, Optional

# Ensure the parent directory is in the path for imports if running as script
# but relying on the project structure where utils is a package or in path
# The existing API surface shows imports from utils, so we assume standard path setup.

logger = logging.getLogger(__name__)

class InsufficientSampleSizeError(Exception):
    """Raised when memory constraints or sample size limits are violated."""
    pass

def estimate_memory_footprint(df: pd.DataFrame) -> float:
    """
    Estimates the memory footprint of a DataFrame in MB.
    """
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def merge_otu_serology(
    otu_path: str,
    serology_path: str,
    output_path: str,
    min_sample_size: int = 50,
    max_memory_gb: float = 6.0
) -> Tuple[int, int]:
    """
    Merges microbiome OTU table and serology metadata.
    
    Logic:
    1. Memory Check: Estimate footprint. If > max_memory_gb * 1024 MB, raise InsufficientSampleSizeError.
    2. Merge: Join on 'subject_id'.
    3. Filter: Drop rows where 'titer_baseline' or 'titer_post' is null.
    4. Validate: If N < min_sample_size, raise InsufficientSampleSizeError.
    5. Output: Write to output_path.
    
    Returns:
        Tuple of (excluded_count, final_count)
    """
    otu_path = Path(otu_path)
    serology_path = Path(serology_path)
    output_path = Path(output_path)
    
    if not otu_path.exists():
        raise FileNotFoundError(f"OTU table not found at {otu_path}")
    if not serology_path.exists():
        raise FileNotFoundError(f"Serology metadata not found at {serology_path}")

    # 1. Memory Check
    # We load a small sample first to estimate size if file is huge, 
    # but for strict adherence to "fail loudly" on memory, we assume 
    # the full load estimate is the safe guard. 
    # A more robust way for massive files is to check file size on disk first.
    try:
        # Check file sizes on disk to avoid loading if obviously too big
        otu_size_mb = otu_path.stat().st_size / (1024 * 1024)
        sero_size_mb = serology_path.stat().st_size / (1024 * 1024)
        estimated_total_mb = otu_size_mb + sero_size_mb * 2 # Heuristic for join expansion
        
        if estimated_total_mb > (max_memory_gb * 1024):
            raise InsufficientSampleSizeError(
                f"Memory constraints prevent loading full dataset. "
                f"Estimated size {estimated_total_mb:.2f} MB > {max_memory_gb * 1024:.2f} MB. "
                f"Pipeline cannot proceed."
            )

        # Load Data
        logger.info(f"Loading OTU table from {otu_path}...")
        otu_df = pd.read_csv(otu_path)
        
        logger.info(f"Loading serology metadata from {serology_path}...")
        sero_df = pd.read_csv(serology_path)
        
        # Refine memory estimate after load
        actual_memory_mb = estimate_memory_footprint(otu_df) + estimate_memory_footprint(sero_df)
        if actual_memory_mb > (max_memory_gb * 1024):
             raise InsufficientSampleSizeError(
                f"Memory constraints prevent loading full dataset. "
                f"Actual memory usage {actual_memory_mb:.2f} MB > {max_memory_gb * 1024:.2f} MB. "
                f"Pipeline cannot proceed."
            )

    except InsufficientSampleSizeError:
        raise
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

    # 2. Merge
    logger.info("Merging datasets on 'subject_id'...")
    if 'subject_id' not in otu_df.columns:
        raise ValueError(f"OTU table missing 'subject_id' column. Columns: {otu_df.columns.tolist()}")
    if 'subject_id' not in sero_df.columns:
        raise ValueError(f"Serology table missing 'subject_id' column. Columns: {sero_df.columns.tolist()}")
        
    merged_df = pd.merge(otu_df, sero_df, on='subject_id', how='inner')
    initial_count = len(merged_df)
    logger.info(f"Merged dataset size: {initial_count} rows.")

    # 3. Filter Null Titers
    logger.info("Filtering subjects with missing titer_baseline or titer_post...")
    before_filter = len(merged_df)
    merged_df = merged_df.dropna(subset=['titer_baseline', 'titer_post'])
    after_filter = len(merged_df)
    excluded_count = before_filter - after_filter
    
    logger.info(f"Excluded {excluded_count} subjects due to missing titer data.")
    
    if excluded_count > 0:
        logger.warning(f"Significant number of subjects ({excluded_count}) excluded due to missing titers.")

    # 4. Final Validation
    final_count = len(merged_df)
    logger.info(f"Final dataset size: {final_count} rows.")
    
    if final_count < min_sample_size:
        raise InsufficientSampleSizeError(
            f"Insufficient sample size (N={final_count} < {min_sample_size}) in final dataset."
        )

    # 5. Output
    logger.info(f"Writing final dataset to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully wrote merged and filtered dataset to {output_path}")
    return excluded_count, final_count

def main():
    """
    Entry point for the merge script.
    Reads config for paths or uses defaults based on task description.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Default paths as per task description
    otu_path = "data/raw/otutable.csv"
    serology_path = "data/raw/serology.csv"
    output_path = "data/processed/cleared_with_diversity.csv"
    
    # Check if config exists to override defaults (optional, but good practice)
    # For now, we use the hardcoded paths from the task description as the primary source
    # since config.py might not have specific path overrides for these raw/processed names.
    
    try:
        excluded, final = merge_otu_serology(
            otu_path=otu_path,
            serology_path=serology_path,
            output_path=output_path,
            min_sample_size=50,
            max_memory_gb=6.0
        )
        logger.info(f"Merge completed. Excluded: {excluded}, Final N: {final}")
    except InsufficientSampleSizeError as e:
        logger.critical(str(e))
        sys.exit(1)
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
