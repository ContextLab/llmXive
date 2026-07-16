"""
Data merger and deduplication logic for ball milling PSD datasets.

This module aggregates raw data from multiple sources (Materials Project, NIST, arXiv),
handles conflicting PSD measurements, and produces a single merged dataset.
"""

import hashlib
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from src.exceptions import DataIngestionError, SchemaValidationError
from src.utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants for deduplication
DEDUP_THRESHOLD = 0.95  # Jaccard similarity threshold for deduplication
PSID_COLUMNS = ['material_name', 'milling_time_hours', 'ball_milling_speed_rpm', 'material_type']
PSD_TARGETS = ['D10', 'D50', 'D90']

def _calculate_record_hash(record: Dict[str, Any]) -> str:
    """
    Calculate a deterministic hash for a record to aid in deduplication.
    Uses the primary key columns and target values.
    """
    hashable_str = ""
    for col in PSID_COLUMNS:
        val = record.get(col, "")
        if val is not None:
            hashable_str += f"{col}:{str(val)}|"
    
    # Add target values for more precise matching
    for col in PSD_TARGETS:
        val = record.get(col)
        if val is not None and not np.isnan(val):
            hashable_str += f"{col}:{val:.4f}|"
    
    return hashlib.sha256(hashable_str.encode('utf-8')).hexdigest()

def _jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def _normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a record to a standard format for merging.
    Handles type conversions and missing values.
    """
    normalized = {}
    
    # Copy core fields with type normalization
    for col in PSID_COLUMNS:
        val = record.get(col)
        if val is None:
            normalized[col] = np.nan
        elif col == 'milling_time_hours' or col == 'ball_milling_speed_rpm':
            try:
                normalized[col] = float(val)
            except (ValueError, TypeError):
                normalized[col] = np.nan
        else:
            normalized[col] = str(val).strip().lower() if isinstance(val, str) else val
    
    # Copy PSD target values
    for col in PSD_TARGETS:
        val = record.get(col)
        if val is None:
            normalized[col] = np.nan
        else:
            try:
                normalized[col] = float(val)
            except (ValueError, TypeError):
                normalized[col] = np.nan
    
    # Copy other fields as-is
    for key, val in record.items():
        if key not in normalized:
            normalized[key] = val
    
    return normalized

def _resolve_conflict(values: List[Any], source_names: List[str]) -> Tuple[Any, str]:
    """
    Resolve conflicting measurements for the same field.
    
    Strategy:
    1. If all values are identical, return that value.
    2. If values differ, prefer non-null values.
    3. If multiple non-null values exist, take the mean (for numeric) or most frequent (for categorical).
    4. Track the source of the resolved value.
    """
    # Filter out None/NaN
    valid_pairs = [(v, s) for v, s in zip(values, source_names) 
                  if v is not None and not (isinstance(v, float) and np.isnan(v))]
    
    if not valid_pairs:
        return np.nan, "unknown"
    
    # If only one valid value, return it
    if len(valid_pairs) == 1:
        return valid_pairs[0]
    
    # Check if all valid values are the same
    first_val = valid_pairs[0][0]
    all_same = all(v == first_val for v, _ in valid_pairs)
    if all_same:
        return first_val, first_val  # Source is the value itself for simplicity
    
    # For numeric values, take mean
    if isinstance(first_val, (int, float)):
        numeric_vals = [v for v, _ in valid_pairs if isinstance(v, (int, float))]
        if numeric_vals:
            mean_val = np.mean(numeric_vals)
            # Find the source closest to the mean
            closest_source = min(valid_pairs, key=lambda x: abs(x[0] - mean_val))[1]
            return mean_val, closest_source
    
    # For categorical values, take mode
    from collections import Counter
    counts = Counter([v for v, _ in valid_pairs])
    most_common = counts.most_common(1)[0][0]
    # Find a source that has this value
    for v, s in valid_pairs:
        if v == most_common:
            return most_common, s
    
    # Fallback
    return valid_pairs[0][0], valid_pairs[0][1]

def merge_datasets(raw_dataframes: Dict[str, pd.DataFrame], output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Merge multiple dataframes from different sources into a single dataset.
    
    Args:
        raw_dataframes: Dictionary mapping source names to dataframes.
        output_path: Optional path to save the merged dataset as JSON/Parquet.
    
    Returns:
        Merged and deduplicated DataFrame.
    
    Raises:
        DataIngestionError: If input dataframes are empty or malformed.
    """
    if not raw_dataframes:
        raise DataIngestionError("No dataframes provided for merging.")
    
    all_records = []
    source_map = {}  # Maps record hash to list of (source, record)
    
    logger.info(f"Merging data from {len(raw_dataframes)} sources: {list(raw_dataframes.keys())}")
    
    for source_name, df in raw_dataframes.items():
        if df is None or df.empty:
            logger.warning(f"Source '{source_name}' is empty, skipping.")
            continue
        
        if not isinstance(df, pd.DataFrame):
            raise DataIngestionError(f"Source '{source_name}' is not a DataFrame.")
        
        # Normalize and collect records
        for idx, row in df.iterrows():
            record = row.to_dict()
            record['_source'] = source_name
            normalized = _normalize_record(record)
            record_hash = _calculate_record_hash(normalized)
            
            if record_hash not in source_map:
                source_map[record_hash] = []
            source_map[record_hash].append((source_name, normalized))
    
    logger.info(f"Total unique record hashes before deduplication: {len(source_map)}")
    
    # Deduplicate and resolve conflicts
    merged_records = []
    conflict_count = 0
    
    for record_hash, source_records in source_map.items():
        if len(source_records) == 1:
            # No conflict, just use the single record
            merged_records.append(source_records[0][1])
        else:
            # Potential conflict - resolve
            conflict_count += 1
            final_record = source_records[0][1].copy()
            
            # Resolve each field that has multiple values
            for col in list(final_record.keys()):
                if col in ['_source', 'record_hash']:
                    continue
                
                values = [rec[col] for _, rec in source_records]
                sources = [src for src, _ in source_records]
                
                # Check if there's actual conflict
                unique_vals = set()
                for v in values:
                    if isinstance(v, float) and np.isnan(v):
                        continue
                    unique_vals.add(v)
                
                if len(unique_vals) <= 1:
                    # No real conflict
                    continue
                
                # Resolve conflict
                resolved_val, resolved_source = _resolve_conflict(values, sources)
                final_record[col] = resolved_val
                final_record[f'{col}_source'] = resolved_source if isinstance(resolved_source, str) else 'resolved'
            
            final_record['_source'] = 'merged'
            final_record['_conflict_resolved'] = True
            merged_records.append(final_record)
    
    logger.info(f"Merged {len(merged_records)} records, resolved {conflict_count} conflicts")
    
    # Create final DataFrame
    merged_df = pd.DataFrame(merged_records)
    
    # Add metadata
    merged_df['_merge_timestamp'] = pd.Timestamp.now()
    merged_df['_source_count'] = merged_df['_source'].apply(lambda x: 1 if x != 'merged' else len(raw_dataframes))
    
    # Save if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as Parquet (preferred) and JSON (backup)
        parquet_path = output_path.with_suffix('.parquet')
        json_path = output_path.with_suffix('.json')
        
        merged_df.to_parquet(parquet_path, index=False)
        merged_df.to_json(json_path, orient='records', lines=False, indent=2)
        
        logger.info(f"Merged dataset saved to {parquet_path} and {json_path}")
    
    return merged_df

def run_merge_pipeline(
    materials_project_df: Optional[pd.DataFrame] = None,
    nist_df: Optional[pd.DataFrame] = None,
    arxiv_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run the complete merge pipeline with all available data sources.
    
    Args:
        materials_project_df: DataFrame from Materials Project ingestion.
        nist_df: DataFrame from NIST ingestion.
        arxiv_df: DataFrame from arXiv ingestion.
        output_path: Path to save the merged dataset.
    
    Returns:
        Merged DataFrame.
    """
    raw_dataframes = {}
    
    if materials_project_df is not None and not materials_project_df.empty:
        raw_dataframes['materials_project'] = materials_project_df
    
    if nist_df is not None and not nist_df.empty:
        raw_dataframes['nist'] = nist_df
    
    if arxiv_df is not None and not arxiv_df.empty:
        raw_dataframes['arxiv'] = arxiv_df
    
    if not raw_dataframes:
        raise DataIngestionError("No valid data sources provided for merging.")
    
    return merge_datasets(raw_dataframes, output_path)

if __name__ == "__main__":
    # Example usage for testing
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Create sample data for testing
    sample_mp = pd.DataFrame({
        'material_name': ['SiO2', 'Al2O3'],
        'milling_time_hours': [2.0, 4.0],
        'ball_milling_speed_rpm': [500, 600],
        'material_type': ['ceramic', 'ceramic'],
        'D10': [10.5, 12.0],
        'D50': [25.0, 30.0],
        'D90': [45.0, 55.0]
    })
    
    sample_nist = pd.DataFrame({
        'material_name': ['SiO2', 'Fe2O3'],
        'milling_time_hours': [2.5, 3.0],
        'ball_milling_speed_rpm': [520, 550],
        'material_type': ['ceramic', 'metal'],
        'D10': [11.0, 8.0],
        'D50': [26.0, 20.0],
        'D90': [46.0, 35.0]
    })
    
    sample_arxiv = pd.DataFrame({
        'material_name': ['Al2O3', 'Cu'],
        'milling_time_hours': [4.0, 1.5],
        'ball_milling_speed_rpm': [600, 400],
        'material_type': ['ceramic', 'metal'],
        'D10': [12.0, 5.0],
        'D50': [30.0, 15.0],
        'D90': [55.0, 25.0]
    })
    
    output_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    merged = run_merge_pipeline(
        materials_project_df=sample_mp,
        nist_df=sample_nist,
        arxiv_df=sample_arxiv,
        output_path=output_dir / "merged_ball_milling_data"
    )
    
    print(f"Merged dataset shape: {merged.shape}")
    print(f"Columns: {list(merged.columns)}")
    print(merged.head())
