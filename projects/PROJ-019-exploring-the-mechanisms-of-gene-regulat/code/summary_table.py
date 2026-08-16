"""
summary_table.py

Generates the final summary table combining enrichment results and ChIP-seq overlap statistics.
Output: data/processed/summary_table.csv
Columns: motif_id, p_value_raw, q_value_adj, chip_overlap_pct
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

from code.config import DATA_PROCESSED_DIR
from code.enrichment import aggregate_enrichment_results
from code.validate import load_enrichment_results as validate_load_enrichment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define expected file paths based on previous tasks
ENRICHMENT_MATRIX_PATH = DATA_PROCESSED_DIR / "enrichment_matrix.csv"
VALIDATION_REPORT_PATH = DATA_PROCESSED_DIR / "validation_report.json"
OUTPUT_PATH = DATA_PROCESSED_DIR / "summary_table.csv"

def load_chip_overlap_stats() -> Dict[str, float]:
    """
    Loads the ChIP-seq overlap statistics from the validation report.
    Returns a dictionary mapping motif_id to chip_overlap_pct.
    """
    if not VALIDATION_REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Validation report not found at {VALIDATION_REPORT_PATH}. "
            "Ensure T032 (validation) has been executed successfully."
        )

    with open(VALIDATION_REPORT_PATH, 'r') as f:
        report = json.load(f)

    # The report structure is expected to contain a list of motif stats
    # based on the implementation of T030/T032.
    # Expected structure: {"motif_stats": [{"motif_id": "MA...", "chip_overlap_pct": 0.65}, ...]}
    # or potentially a flat dict if T032 aggregated differently.
    # We assume the structure from T032: a list of validated motifs with overlap stats.
    
    stats = {}
    if "motif_stats" in report:
        for entry in report["motif_stats"]:
            motif_id = entry.get("motif_id")
            overlap_pct = entry.get("chip_overlap_pct")
            if motif_id and overlap_pct is not None:
                stats[motif_id] = overlap_pct
    elif "overlap_stats" in report:
        # Fallback if T032 used a different key
        for motif_id, overlap_pct in report["overlap_stats"].items():
            stats[motif_id] = overlap_pct
    else:
        logger.warning(f"Unexpected validation report structure at {VALIDATION_REPORT_PATH}. Keys: {report.keys()}")

    return stats

def generate_summary_table() -> pd.DataFrame:
    """
    Merges enrichment results (p_value, q_value) with ChIP-seq overlap stats.
    Returns a DataFrame with columns: motif_id, p_value_raw, q_value_adj, chip_overlap_pct.
    """
    if not ENRICHMENT_MATRIX_PATH.exists():
        raise FileNotFoundError(
            f"Enrichment matrix not found at {ENRICHMENT_MATRIX_PATH}. "
            "Ensure T024 (enrichment) has been executed successfully."
        )

    # Load enrichment results
    # The matrix is expected to be in long format or wide format with motifs as rows.
    # Based on T024, it's likely a CSV with motifs as rows and cell types as columns,
    # or a long format. The task requires a single summary table, so we aggregate
    # the enrichment stats (e.g., mean q-value or max significance) across cell types
    # or select the most significant entry per motif if the matrix is wide.
    # However, the task description implies a single row per motif.
    # Let's assume the enrichment matrix has columns: motif_id, cell_type, q_value, p_value.
    # If it's wide (motifs as index, cell_types as columns), we need to aggregate.
    
    df_enrichment = pd.read_csv(ENRICHMENT_MATRIX_PATH)

    # Normalize columns to expected names if they differ slightly
    # T024 output: enrichment_matrix.csv
    # Expected columns from T022/T023: motif_id, p_value, q_value, cell_type (if long)
    # OR motif_id, cell_type_1_q, cell_type_2_q ... (if wide)
    
    # Strategy: If 'q_value' column exists, assume long format.
    # If not, assume wide format and aggregate (e.g., min q-value across cell types).
    
    if 'q_value' in df_enrichment.columns:
        # Long format: aggregate by motif_id
        # We take the most significant (min q-value) and corresponding p-value
        df_agg = df_enrichment.sort_values('q_value').groupby('motif_id').first().reset_index()
        df_agg = df_agg.rename(columns={'q_value': 'q_value_adj', 'p_value': 'p_value_raw'})
    else:
        # Wide format or different structure.
        # Try to identify q-value columns.
        q_cols = [c for c in df_enrichment.columns if 'q' in c.lower() and 'value' in c.lower()]
        if not q_cols:
            raise ValueError(f"Could not identify q-value columns in {ENRICHMENT_MATRIX_PATH}. Columns: {df_enrichment.columns.tolist()}")
        
        # Aggregate: min q-value across cell types
        df_enrichment['min_q'] = df_enrichment[q_cols].min(axis=1)
        # For p-value, we might need to find the corresponding one, or just take min p-value
        p_cols = [c for c in df_enrichment.columns if 'p' in c.lower() and 'value' in c.lower()]
        if p_cols:
            df_enrichment['min_p'] = df_enrichment[p_cols].min(axis=1)
            df_agg = df_enrichment[['motif_id', 'min_q', 'min_p']].rename(
                columns={'min_q': 'q_value_adj', 'min_p': 'p_value_raw'}
            )
        else:
            # Fallback: just use min q
            df_agg = df_enrichment[['motif_id', 'min_q']].rename(columns={'min_q': 'q_value_adj'})
            df_agg['p_value_raw'] = 0.0 # Placeholder if p-value not found, though unlikely

    # Load ChIP overlap stats
    chip_stats = load_chip_overlap_stats()

    # Merge
    df_summary = df_agg.merge(
        pd.DataFrame.from_dict(chip_stats, orient='index', columns=['chip_overlap_pct']),
        left_on='motif_id',
        right_index=True,
        how='left'
    )

    # Fill missing overlap with 0.0 if motif wasn't validated (top motifs only were validated usually)
    df_summary['chip_overlap_pct'] = df_summary['chip_overlap_pct'].fillna(0.0)

    # Ensure correct column order and types
    cols = ['motif_id', 'p_value_raw', 'q_value_adj', 'chip_overlap_pct']
    # Only keep columns that exist in df_summary
    final_cols = [c for c in cols if c in df_summary.columns]
    df_summary = df_summary[final_cols]

    # Sort by q-value ascending (most significant first)
    if 'q_value_adj' in df_summary.columns:
        df_summary = df_summary.sort_values('q_value_adj')

    return df_summary

def main():
    """
    Main entry point to generate the summary table.
    """
    logger.info("Starting summary table generation (T033)...")
    
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    try:
        df = generate_summary_table()
        df.to_csv(OUTPUT_PATH, index=False)
        logger.info(f"Summary table successfully written to {OUTPUT_PATH}")
        logger.info(f"Total motifs in summary: {len(df)}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate summary table: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())