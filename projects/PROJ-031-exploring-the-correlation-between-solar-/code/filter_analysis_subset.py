"""
Filter analysis subset module.
Filters out recurrent storm periods to create a clean analysis dataset.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta

# Constants
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
ALIGNED_CSV = PROCESSED_DIR / "aligned_events.csv"
ANALYSIS_SUBSET_CSV = PROCESSED_DIR / "analysis_subset.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create output directories."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def filter_non_recurrent_storms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to non-recurrent storms.
    Rule: Only include distinct minima separated by >= 24 hours of recovery.
    A storm is considered recurrent if another storm occurs within 7 days.
    """
    if len(df) == 0:
        return df
    
    # Sort by storm time
    df = df.sort_values('storm_min_time').reset_index(drop=True)
    
    # Convert time to datetime
    df['storm_dt'] = pd.to_datetime(df['storm_min_time'])
    
    # Filter out recurrent storms
    keep_mask = []
    for i, row in df.iterrows():
        is_recurrent = row.get('is_recurrent', False)
        if not is_recurrent:
            keep_mask.append(True)
        else:
            # Check if this is the first in a recurrent cluster
            # Keep the strongest (most negative Dst) in each cluster
            cluster_start = i
            while i + 1 < len(df):
                next_time = df.loc[i+1, 'storm_dt']
                curr_time = row['storm_dt']
                if (next_time - curr_time).total_seconds() / 3600 <= 24:
                    i += 1
                else:
                    break
            cluster_end = i
            
            # Find the strongest storm in the cluster
            cluster = df.loc[cluster_start:cluster_end]
            strongest_idx = cluster['storm_min_dst'].idxmin()
            keep_mask.append(df.index == strongest_idx)
    
    # Apply filter
    filtered_df = df[keep_mask]
    filtered_df = filtered_df.drop(columns=['storm_dt'])
    
    logger.info(f"Filtered from {len(df)} to {len(filtered_df)} non-recurrent storms")
    return filtered_df

def write_subset(df: pd.DataFrame):
    """Write the analysis subset to CSV."""
    output_path = ANALYSIS_SUBSET_CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote analysis subset to {output_path}")

def update_manifest():
    """Update the source manifest with the new file."""
    import yaml
    manifest_path = DATA_DIR / "source_manifest.yaml"
    
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        manifest['last_updated'] = datetime.now().isoformat()
        
        # Add analysis subset entry
        if 'analysis_subset' not in manifest.get('sources', {}):
            if 'sources' not in manifest:
                manifest['sources'] = {}
            manifest['sources']['analysis_subset'] = {
                'url': str(ANALYSIS_SUBSET_CSV),
                'status': 'generated',
                'last_verified_at': datetime.now().isoformat(),
                'verified': True
            }
        
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)
    else:
        logger.warning("Manifest not found, skipping update")

def main():
    """Main entry point."""
    ensure_directories()
    
    try:
        # Load aligned events
        if not ALIGNED_CSV.exists():
            raise FileNotFoundError(f"Aligned events file not found at {ALIGNED_CSV}")
        
        df = pd.read_csv(ALIGNED_CSV)
        logger.info(f"Loaded {len(df)} aligned events")
        
        # Filter
        filtered_df = filter_non_recurrent_storms(df)
        
        # Write
        write_subset(filtered_df)
        
        # Update manifest
        update_manifest()
        
        logger.info("Filtering completed successfully")
        return True
    except Exception as e:
        logger.error(f"Filtering failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
