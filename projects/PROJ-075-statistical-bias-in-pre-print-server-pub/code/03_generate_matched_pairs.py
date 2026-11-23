import os
import sys
import csv
import logging
from datetime import datetime
from pathlib import Path

# Ensure code directory is in path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.pdf_parser import is_valid_p_value_range

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/processing.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def load_csv(input_path: str) -> list[dict]:
    """
    Load the intermediate extracted stats CSV.
    Expected columns: preprint_id, journal_id, preprint_p_values, preprint_effect_sizes, 
                      journal_p_values, journal_effect_sizes, primary_method, exclusion_reason
    """
    data = []
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    logger.info(f"Loaded {len(data)} rows from {input_path}")
    return data

def load_exclusions(exclusion_log_path: str) -> set[str]:
    """
    Load exclusion log to identify pairs that were filtered out previously.
    We return a set of 'preprint_id,journal_id' keys to cross-reference.
    """
    exclusions = set()
    if not os.path.exists(exclusion_log_path):
        logger.warning(f"Exclusion log not found at {exclusion_log_path}. Proceeding without exclusions.")
        return exclusions

    with open(exclusion_log_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Create a unique key for the pair
            key = f"{row['preprint_id']},{row['journal_id']}"
            exclusions.add(key)
    
    logger.info(f"Loaded {len(exclusions)} excluded pairs from {exclusion_log_path}")
    return exclusions

def is_missing_data(p_values_str: str, effect_sizes_str: str) -> bool:
    """
    Check if a string representation of p-values or effect sizes is effectively empty or missing.
    Returns True if missing, False if present.
    """
    if not p_values_str or p_values_str.strip() == '':
        return True
    if not effect_sizes_str or effect_sizes_str.strip() == '':
        return True
    
    # Check if the string contains only delimiters or whitespace
    parts_p = [x.strip() for x in p_values_str.split(';') if x.strip()]
    parts_es = [x.strip() for x in effect_sizes_str.split(';') if x.strip()]
    
    return len(parts_p) == 0 or len(parts_es) == 0

def flag_missing_fields(row: dict) -> dict:
    """
    Add flags to the row indicating which specific fields are missing or invalid.
    Returns the modified row.
    """
    flags = []
    
    # Check Preprint Data
    if is_missing_data(row.get('preprint_p_values', ''), row.get('preprint_effect_sizes', '')):
        flags.append('missing_preprint_stats')
    else:
        # Validate p-values if present
        p_vals = row.get('preprint_p_values', '').split(';')
        for pv in p_vals:
            pv = pv.strip()
            if pv and not is_valid_p_value_range(pv):
                flags.append('invalid_preprint_p_value')
                break

    # Check Journal Data
    if is_missing_data(row.get('journal_p_values', ''), row.get('journal_effect_sizes', '')):
        flags.append('missing_journal_stats')
    else:
        # Validate p-values if present
        p_vals = row.get('journal_p_values', '').split(';')
        for pv in p_vals:
            pv = pv.strip()
            if pv and not is_valid_p_value_range(pv):
                flags.append('invalid_journal_p_value')
                break

    # Check Exclusion Status (from exclusion_reason column if it exists)
    if row.get('exclusion_reason') and row['exclusion_reason'].strip() != '':
        flags.append('excluded_by_filter')

    row['data_quality_flags'] = ';'.join(flags) if flags else 'none'
    return row

def main():
    """
    Main entry point for generating the final matched_pairs.csv.
    
    1. Loads intermediate extraction results.
    2. Loads exclusion logs to ensure consistency.
    3. Flags rows with missing data.
    4. Writes the final `data/processed/matched_pairs.csv`.
    """
    logger.info("Starting matched pairs generation (T017)...")
    
    # Define paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / 'data' / 'raw' / 'extracted_stats.csv'
    exclusion_path = base_dir / 'data' / 'raw' / 'exclusion_log.csv'
    output_path = base_dir / 'data' / 'processed' / 'matched_pairs.csv'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        rows = load_csv(str(input_path))
    except FileNotFoundError as e:
        logger.critical(f"Cannot proceed: {e}")
        sys.exit(1)
    
    exclusions = load_exclusions(str(exclusion_path))
    
    # Process rows
    processed_rows = []
    stats = {'total': len(rows), 'flagged': 0, 'clean': 0}
    
    for row in rows:
        # Re-verify exclusion status based on exclusion_reason column in the row itself
        # The row might have been filtered in 01_fetch_and_match but still present if the pipeline is incremental
        # We trust the `exclusion_reason` column in the input CSV as the source of truth for this step
        if row.get('exclusion_reason') and row['exclusion_reason'].strip() != '':
            # This row was filtered out in previous steps, mark it but keep for audit or skip?
            # Task T017 says "Generate ... containing MatchedPaperPair entities ... flagging pairs with missing data"
            # Usually, excluded pairs are not part of the final "matched" dataset for analysis, 
            # but we keep them with a flag to show the pipeline history.
            pass 

        # Flag missing/invalid data
        processed_row = flag_missing_fields(row)
        processed_rows.append(processed_row)
        
        if processed_row['data_quality_flags'] != 'none':
            stats['flagged'] += 1
        else:
            stats['clean'] += 1

    # Write output
    fieldnames = list(processed_rows[0].keys()) if processed_rows else []
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)
    
    logger.info(f"Successfully wrote {len(processed_rows)} rows to {output_path}")
    logger.info(f"Stats: {stats}")
    
    print(f"Generated {output_path}")

if __name__ == '__main__':
    main()
