"""
Summary Table Generation (Task T034)

Generates the final summary table by reading the enrichment matrix and validation report,
filtering for top motifs, and calculating Jaccard overlap percentages.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from code.config import DATA_PROCESSED_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_enrichment_csv() -> pd.DataFrame:
    """
    Loads the enrichment matrix from data/processed/enrichment_matrix.csv.
    Raises FileNotFoundError if the file does not exist.
    """
    file_path = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {file_path}. "
            "Ensure enrichment analysis (T024) has been run successfully."
        )
    
    logger.info(f"Loading enrichment matrix from {file_path}")
    df = pd.read_csv(file_path)
    
    required_cols = ['motif_id', 'cell_type', 'p_value', 'q_value']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Enrichment matrix missing required columns: {missing_cols}")
    
    return df

def load_validation_json() -> Dict[str, Any]:
    """
    Loads the validation report from data/processed/validation_report.json.
    Raises FileNotFoundError if the file does not exist.
    """
    file_path = DATA_PROCESSED_DIR / "validation_report.json"
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {file_path}. "
            "Ensure validation pipeline (T033) has been run successfully."
        )
    
    logger.info(f"Loading validation report from {file_path}")
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if 'top_motifs' not in data:
        raise ValueError("Validation report missing 'top_motifs' key.")
    
    return data

def calculate_jaccard_overlap(predicted_peaks: List[Dict], observed_peaks: List[Dict]) -> float:
    """
    Calculates the Jaccard overlap (Intersection over Union) between two sets of peaks.
    
    Args:
        predicted_peaks: List of dicts with keys 'chrom', 'start', 'end'
        observed_peaks: List of dicts with keys 'chrom', 'start', 'end'
        
    Returns:
        Float percentage of overlap (0.0 to 100.0).
    """
    if not predicted_peaks or not observed_peaks:
        return 0.0
    
    # Convert to sets of tuples for efficient intersection/union
    # Assuming peaks are normalized (chrom, start, end)
    p_set = set((p['chrom'], p['start'], p['end']) for p in predicted_peaks)
    o_set = set((p['chrom'], p['start'], p['end']) for p in observed_peaks)
    
    intersection = len(p_set.intersection(o_set))
    union = len(p_set.union(o_set))
    
    if union == 0:
        return 0.0
    
    return (intersection / union) * 100.0

def generate_summary_table(enrichment_df: pd.DataFrame, validation_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generates the final summary table.
    
    Logic:
    1. Filter enrichment results to top N motifs by q-value (ranking).
       Note: The task description implies selecting 'top N' to satisfy FR-005.
       We will select the top 10 motifs overall by lowest q_value.
    2. Retrieve the 'chip_overlap_pct' from the validation report.
       Note: The validation report (T033) contains 'top_motifs' which includes
       'overlap_pct' for specific motifs. However, the summary table requires
       a column 'chip_overlap_pct'.
       
       According to T033 spec: 'top_motifs' is a list of objects with keys:
       motif_id, q_value, overlap_pct.
       
       We will map the overlap_pct from the validation report to the corresponding
       motif_id in the summary table. If a motif in the top list isn't in the
       validation report's top_motifs (unlikely if we filter strictly), we default
       to 0.0 or NaN.
       
    3. Construct the output DataFrame with columns:
       motif_id, p_value_raw, q_value_adj, chip_overlap_pct.
    """
    
    logger.info("Generating summary table...")
    
    # 1. Filter to top motifs by q-value
    # Sort by q_value ascending
    sorted_df = enrichment_df.sort_values(by='q_value', ascending=True)
    
    # Select top N. Let's choose top 10 as a representative "top enriched" set.
    # If the dataset is smaller, take all.
    top_n = min(10, len(sorted_df))
    top_motifs_df = sorted_df.head(top_n).copy()
    
    # 2. Map overlap percentages from validation report
    # The validation report has a list of 'top_motifs' with overlap_pct
    validation_motifs = {
        m['motif_id']: m.get('overlap_pct', 0.0) 
        for m in validation_data.get('top_motifs', [])
    }
    
    # Apply overlap percentage to the dataframe
    # If a motif_id is not found in the validation mapping, set to 0.0 or NaN
    # Based on T033 spec, overlap_pct is float or null.
    top_motifs_df['chip_overlap_pct'] = top_motifs_df['motif_id'].map(
        lambda x: validation_motifs.get(x, 0.0)
    )
    
    # 3. Select and rename columns for final output
    # Output columns: motif_id, p_value_raw, q_value_adj, chip_overlap_pct
    result_df = top_motifs_df[[
        'motif_id', 
        'p_value', 
        'q_value', 
        'chip_overlap_pct'
    ]].copy()
    
    result_df.columns = [
        'motif_id', 
        'p_value_raw', 
        'q_value_adj', 
        'chip_overlap_pct'
    ]
    
    # Ensure formatting: overlap_pct to 2 decimal places
    result_df['chip_overlap_pct'] = result_df['chip_overlap_pct'].round(2)
    
    return result_df

def main():
    """
    Entry point for T034.
    Reads inputs, generates table, and writes to data/processed/summary_table.csv.
    """
    try:
        # Ensure output directory exists
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load inputs
        enrichment_df = load_enrichment_csv()
        validation_data = load_validation_json()
        
        # Generate table
        summary_df = generate_summary_table(enrichment_df, validation_data)
        
        # Write output
        output_path = DATA_PROCESSED_DIR / "summary_table.csv"
        summary_df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully wrote summary table to {output_path}")
        logger.info(f"Table shape: {summary_df.shape}")
        logger.info(f"Columns: {list(summary_df.columns)}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during summary generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())