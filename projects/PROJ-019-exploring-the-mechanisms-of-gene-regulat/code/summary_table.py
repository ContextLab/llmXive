import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# Import from existing API surface
from code.config import DATA_PROCESSED_DIR
from code.validate import get_top_motifs_summary

logger = logging.getLogger(__name__)

def load_enrichment_csv(csv_path: Path) -> pd.DataFrame:
    """
    Load the enrichment matrix from CSV.
    Expected columns: motif_id, cell_type, p_value, q_value
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Enrichment matrix not found at {csv_path}")
    
    df = pd.read_csv(csv_path)
    required_cols = {'motif_id', 'cell_type', 'p_value', 'q_value'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Enrichment matrix missing columns: {missing}")
    
    return df

def load_validation_json(json_path: Path) -> Dict[str, Any]:
    """
    Load the validation report JSON.
    Expected structure:
    {
        "overlap_pct": float,
        "top_motifs": [{"motif_id": str, "q_value": float, "overlap_pct": float}, ...],
        "silhouette_score": float
    }
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Validation report not found at {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Validate structure
    if 'top_motifs' not in data:
        raise ValueError("Validation report missing 'top_motifs' key")
    
    return data

def generate_summary_table(enrichment_csv: Path, validation_json: Path, output_path: Path) -> pd.DataFrame:
    """
    Generate the final summary table.
    
    Reads from:
    - enrichment_csv: data/processed/enrichment_matrix.csv
    - validation_json: data/processed/validation_report.json
    
    Outputs:
    - summary_table.csv with columns: motif_id, p_value_raw, q_value_adj, chip_overlap_pct
    
    Logic:
    1. Load enrichment matrix
    2. Load validation report (contains top_motifs with overlap_pct)
    3. Filter enrichment to top motifs (q < 0.05) as per T032a
    4. Merge with overlap data from validation report
    5. Output final table
    """
    # Load data
    enrichment_df = load_enrichment_csv(enrichment_csv)
    validation_data = load_validation_json(validation_json)
    
    # Get top motifs summary (already filtered by q < 0.05 in T032a)
    top_motifs = validation_data['top_motifs']
    
    if not top_motifs:
        logger.warning("No top motifs found in validation report. Creating empty summary table.")
        summary_df = pd.DataFrame(columns=['motif_id', 'p_value_raw', 'q_value_adj', 'chip_overlap_pct'])
        summary_df.to_csv(output_path, index=False)
        return summary_df
    
    # Create a lookup dict for overlap percentages by motif_id
    overlap_lookup = {motif['motif_id']: motif['overlap_pct'] for motif in top_motifs}
    
    # Filter enrichment to only top motifs
    top_motif_ids = set(overlap_lookup.keys())
    filtered_df = enrichment_df[enrichment_df['motif_id'].isin(top_motif_ids)].copy()
    
    if filtered_df.empty:
        logger.warning("No matching motifs found between enrichment and validation. Creating empty summary table.")
        summary_df = pd.DataFrame(columns=['motif_id', 'p_value_raw', 'q_value_adj', 'chip_overlap_pct'])
        summary_df.to_csv(output_path, index=False)
        return summary_df
    
    # Add overlap percentage column
    # For each motif, get the overlap_pct from the validation report
    # If a motif appears in multiple cell types, we take the max overlap or average?
    # Based on task description, we assume one row per motif_id in summary
    # So we need to aggregate if there are duplicates
    
    # First, map overlap_pct to each row
    filtered_df['chip_overlap_pct'] = filtered_df['motif_id'].map(overlap_lookup)
    
    # Rename columns to match output specification
    summary_df = filtered_df[['motif_id', 'p_value', 'q_value', 'chip_overlap_pct']].copy()
    summary_df.columns = ['motif_id', 'p_value_raw', 'q_value_adj', 'chip_overlap_pct']
    
    # If there are duplicate motif_ids (from different cell types), we need to aggregate
    # The task doesn't specify aggregation method, so we'll take the row with the lowest q_value
    summary_df = summary_df.sort_values('q_value_adj').drop_duplicates('motif_id', keep='first')
    
    # Round values as per specification
    summary_df['p_value_raw'] = summary_df['p_value_raw'].round(6)  # Standard p-value precision
    summary_df['q_value_adj'] = summary_df['q_value_adj'].round(4)  # 4 decimal places as per T032
    summary_df['chip_overlap_pct'] = summary_df['chip_overlap_pct'].round(2)  # 2 decimal places as per T032
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    summary_df.to_csv(output_path, index=False)
    
    logger.info(f"Summary table generated with {len(summary_df)} motifs at {output_path}")
    
    return summary_df

def main():
    """
    Main entry point for generating the summary table.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths
    enrichment_csv = DATA_PROCESSED_DIR / 'enrichment_matrix.csv'
    validation_json = DATA_PROCESSED_DIR / 'validation_report.json'
    output_path = DATA_PROCESSED_DIR / 'summary_table.csv'
    
    # Check if input files exist
    if not enrichment_csv.exists():
        logger.error(f"Enrichment matrix not found at {enrichment_csv}")
        logger.error("Please run the enrichment pipeline first (T024)")
        sys.exit(1)
    
    if not validation_json.exists():
        logger.error(f"Validation report not found at {validation_json}")
        logger.error("Please run the validation pipeline first (T032)")
        sys.exit(1)
    
    try:
        generate_summary_table(enrichment_csv, validation_json, output_path)
        logger.info("Summary table generation completed successfully")
    except Exception as e:
        logger.error(f"Error generating summary table: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
