import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import local utilities
from config import get_config
from logging_config import handle_memory_pressure, get_memory_status

# Constants
REQUIRED_COLUMNS = ['species', 'telomere_length_kb', 'lifespan', 'migration_status', 'body_mass_g']
WILD_CAUGHT_KEYWORDS = ['wild', 'wild-caught', 'field', 'natural']

def load_ingested_data(telomere_path: Path, anage_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load raw telomere and AnAge ecological data from disk.
    Raises FileNotFoundError if paths do not exist.
    """
    if not telomere_path.exists():
        raise FileNotFoundError(f"Telomere data not found at {telomere_path}")
    if not anage_path.exists():
        raise FileNotFoundError(f"AnAge data not found at {anage_path}")

    # Load telomere data (expects CSV)
    try:
        telomere_df = pd.read_csv(telomere_path)
        logging.info(f"Loaded {len(telomere_df)} rows from telomere data.")
    except Exception as e:
        raise RuntimeError(f"Failed to load telomere data: {e}")

    # Load AnAge data (expects CSV)
    try:
        anage_df = pd.read_csv(anage_path)
        logging.info(f"Loaded {len(anage_df)} rows from AnAge data.")
    except Exception as e:
        raise RuntimeError(f"Failed to load AnAge data: {e}")

    return telomere_df, anage_df

def filter_wild_caught_early_life(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataframe for wild-caught and early-life individuals.
    Logs excluded records to a separate file for audit.
    """
    if df.empty:
        logging.warning("Input dataframe is empty in filter_wild_caught_early_life.")
        return df

    # Identify wild-caught
    wild_mask = pd.Series([False] * len(df), index=df.index)
    wild_col_candidates = [c for c in df.columns if 'source' in c.lower() or 'location' in c.lower() or 'method' in c.lower()]
    
    # Heuristic: Look for columns containing 'wild' or 'caught' in values or headers
    wild_keywords = WILD_CAUGHT_KEYWORDS
    
    for col in df.columns:
        if any(kw in str(col).lower() for kw in wild_keywords):
            wild_mask |= df[col].astype(str).str.lower().apply(lambda x: any(kw in x for kw in wild_keywords))
    
    # If no specific column found, try a generic 'origin' or 'source' column if it exists
    if not wild_mask.any():
        for col in ['source', 'origin', 'collection_method', 'capture_location']:
            if col in df.columns:
                wild_mask |= df[col].astype(str).str.lower().apply(lambda x: any(kw in x for kw in wild_keywords))
                if wild_mask.any():
                    break

    # Identify early-life (if column exists)
    early_mask = pd.Series([True] * len(df), index=df.index)
    if 'life_stage' in df.columns or 'age_group' in df.columns:
        stage_col = 'life_stage' if 'life_stage' in df.columns else 'age_group'
        early_keywords = ['juvenile', 'fledgling', 'nestling', 'chick', 'young', 'early']
        early_mask = df[stage_col].astype(str).str.lower().apply(lambda x: any(kw in x for kw in early_keywords))
    else:
        # If no age info, assume all are candidates (conservative) or log warning
        logging.warning("No life stage column found. Assuming all records are potential early-life.")

    final_mask = wild_mask & early_mask
    
    filtered_df = df[final_mask].copy()
    excluded_df = df[~final_mask].copy()
    
    if not excluded_df.empty:
        excluded_path = Path('logs') / 'excluded_records.csv'
        excluded_path.parent.mkdir(parents=True, exist_ok=True)
        excluded_df.to_csv(excluded_path, index=False)
        logging.info(f"Filtered {len(excluded_df)} records to logs/excluded_records.csv.")
    
    logging.info(f"Retained {len(filtered_df)} wild-caught/early-life records.")
    return filtered_df

def convert_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all telomere units to kilobases (kb).
    Logs unconvertible records to logs/unconvertible_units.csv.
    """
    if 'telomere_length' not in df.columns or 'unit' not in df.columns:
        # If already in kb or no unit column, check if column is named telomere_length_kb
        if 'telomere_length_kb' in df.columns:
            return df.rename(columns={'telomere_length_kb': 'telomere_length_kb'})
        raise ValueError("Expected 'telomere_length' and 'unit' columns or 'telomere_length_kb' column.")

    df = df.copy()
    
    # Normalize unit column
    df['unit'] = df['unit'].astype(str).str.lower().str.strip()
    
    # Conversion factors to kb
    # 1 kb = 1000 bp
    # 1 bp = 1
    # 1 Mb = 1,000,000 bp
    # 1 Gb = 1,000,000,000 bp
    
    def to_kb(val, unit):
        try:
            val = float(val)
            if pd.isna(val):
                return np.nan
            if unit in ['kb', 'kilobase', 'kilobases']:
                return val
            elif unit in ['bp', 'base', 'bases', 'basepair', 'basepairs']:
                return val / 1000.0
            elif unit in ['mb', 'megabase', 'megabases']:
                return val * 1000.0
            elif unit in ['gb', 'gigabase', 'gigabases']:
                return val * 1_000_000.0
            else:
                return None
        except (ValueError, TypeError):
            return None

    df['telomere_length_kb'] = df.apply(lambda row: to_kb(row['telomere_length'], row['unit']), axis=1)
    
    # Identify unconvertible
    unconvertible_mask = df['telomere_length_kb'].isna()
    if unconvertible_mask.any():
        unconv_df = df[unconvertible_mask][['species', 'telomere_length', 'unit']].copy()
        unconv_path = Path('logs') / 'unconvertible_units.csv'
        unconv_path.parent.mkdir(parents=True, exist_ok=True)
        unconv_df.to_csv(unconv_path, index=False)
        logging.warning(f"Logged {len(unconv_df)} unconvertible units to logs/unconvertible_units.csv")
    
    # Drop unconvertible
    df = df.dropna(subset=['telomere_length_kb'])
    return df

def merge_data(telomere_df: pd.DataFrame, anage_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join telomere data with AnAge ecological data on species name.
    Excludes unmatched records and logs to logs/missing_data_log.csv.
    """
    # Standardize species column names for merge
    # Telomere df usually has 'species' or 'Species'
    # Anage df usually has 'species' or 'scientific_name'
    
    t_species_col = 'species' if 'species' in telomere_df.columns else None
    a_species_col = 'species' if 'species' in anage_df.columns else 'scientific_name'
    
    if not t_species_col:
        # Try to find it
        candidates = [c for c in telomere_df.columns if 'species' in c.lower()]
        if candidates:
            t_species_col = candidates[0]
        else:
            raise ValueError("Could not identify species column in telomere data.")
    
    if a_species_col not in anage_df.columns:
        candidates = [c for c in anage_df.columns if 'species' in c.lower() or 'name' in c.lower()]
        if candidates:
            a_species_col = candidates[0]
        else:
            raise ValueError("Could not identify species column in Anage data.")

    # Clean species names (strip whitespace, lower case)
    telomere_df = telomere_df.copy()
    anage_df = anage_df.copy()
    
    telomere_df[t_species_col] = telomere_df[t_species_col].astype(str).str.strip().str.lower()
    anage_df[a_species_col] = anage_df[a_species_col].astype(str).str.strip().str.lower()

    # Perform inner join
    merged = pd.merge(
        telomere_df,
        anage_df,
        left_on=t_species_col,
        right_on=a_species_col,
        how='inner'
    )

    # Log unmatched (if we did a left join first, but we did inner, so we log the difference from the left)
    # To log missing, we need to know what was in telomere but not in anage
    # Re-do a left join to identify missing
    left_merge = pd.merge(
        telomere_df,
        anage_df[[a_species_col]],
        left_on=t_species_col,
        right_on=a_species_col,
        how='left',
        indicator=True
    )
    missing = left_merge[left_merge['_merge'] == 'left_only']
    
    if not missing.empty:
        missing_path = Path('logs') / 'missing_data_log.csv'
        missing_path.parent.mkdir(parents=True, exist_ok=True)
        missing[[t_species_col]].to_csv(missing_path, index=False)
        logging.warning(f"Logged {len(missing)} species with missing AnAge data to logs/missing_data_log.csv")
    
    # Select and rename columns to match schema
    # Expected: species, telomere_length_kb, lifespan, migration_status, body_mass_g
    
    # Ensure telomere column exists
    if 'telomere_length_kb' not in merged.columns:
        # Check if it's named differently
        candidates = [c for c in merged.columns if 'telomere' in c.lower()]
        if candidates:
            merged['telomere_length_kb'] = merged[candidates[0]]
        else:
            raise ValueError("No telomere length column found in merged data.")

    # Map common AnAge columns to schema
    # lifespan: lifespan, max_lifespan, longevity
    # migration_status: migration, migration_status, migratory
    # body_mass_g: body_mass, mass, body_mass_g, weight

    def find_col(df, candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    lifespan_col = find_col(merged, ['lifespan', 'max_lifespan', 'longevity', 'longevity_years'])
    migration_col = find_col(merged, ['migration_status', 'migration', 'migratory', 'migratory_status'])
    mass_col = find_col(merged, ['body_mass_g', 'body_mass', 'mass', 'weight', 'body_mass_grams'])

    if not lifespan_col:
        logging.error("Lifespan column not found in AnAge data.")
    if not migration_col:
        logging.error("Migration status column not found in AnAge data.")
    if not mass_col:
        logging.error("Body mass column not found in AnAge data.")

    result = pd.DataFrame()
    result['species'] = merged[t_species_col]
    result['telomere_length_kb'] = merged['telomere_length_kb']
    
    if lifespan_col:
        result['lifespan'] = merged[lifespan_col]
    if migration_col:
        result['migration_status'] = merged[migration_col]
    if mass_col:
        result['body_mass_g'] = merged[mass_col]

    # Drop rows with missing required columns if they exist
    for col in REQUIRED_COLUMNS:
        if col in result.columns:
            result = result.dropna(subset=[col])

    logging.info(f"Merged data contains {len(result)} records.")
    return result

def validate_output_schema(df: pd.DataFrame, output_path: Path) -> bool:
    """
    Validates that the output dataframe meets schema requirements:
    - Contains required columns
    - 'wild-caught' filter was applied (check for source/origin keywords in metadata if available, 
      but primarily relies on the fact that filter_wild_caught_early_life was called)
    - Data types are appropriate
    """
    # Check columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        logging.error(f"Schema validation failed: Missing columns {missing_cols}")
        return False

    # Check for wild-caught filter application
    # Since we filtered before merge, we verify the source column in the original data if available
    # However, in the merged df, the source might be lost if AnAge doesn't have it.
    # We rely on the fact that the pipeline step 'filter_wild_caught_early_life' was executed.
    # To be explicit, we check if any 'wild' keyword exists in the data if a source column survived
    wild_check = False
    wild_cols = [c for c in df.columns if any(k in c.lower() for k in ['source', 'origin', 'location'])]
    if wild_cols:
        for col in wild_cols:
            if df[col].astype(str).str.lower().str.contains('wild', case=False, na=False).any():
                wild_check = True
                break
    
    # If we can't verify via column, we assume the filter logic was correct as per code flow
    # But we log a warning if we can't verify
    if not wild_check and not wild_cols:
        logging.warning("Could not explicitly verify 'wild-caught' filter in output data (no source column found).")
    
    # Validate data types
    if not pd.api.types.is_numeric_dtype(df['telomere_length_kb']):
        logging.error("telomere_length_kb is not numeric.")
        return False
    if not pd.api.types.is_numeric_dtype(df['lifespan']):
        logging.error("lifespan is not numeric.")
        return False
    if not pd.api.types.is_numeric_dtype(df['body_mass_g']):
        logging.error("body_mass_g is not numeric.")
        return False

    # Ensure no duplicates
    if df['species'].duplicated().any():
        logging.warning("Duplicate species found in merged data. Keeping first occurrence.")
        df = df.drop_duplicates(subset=['species'], keep='first')

    # Save to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Validated output saved to {output_path}")
    
    return True

def main():
    """
    Main entry point for the clean and merge pipeline.
    """
    # Configure logging
    from logging_config import init_project_logging
    init_project_logging()
    logger = logging.getLogger(__name__)

    config = get_config()
    
    # Define paths
    base_dir = Path(config.get('data_dir', 'data'))
    telomere_raw = base_dir / 'raw' / 'telomere_data.csv'
    anage_raw = base_dir / 'raw' / 'anage_data.csv'
    processed_dir = base_dir / 'processed'
    output_file = processed_dir / 'merged_data.csv'
    logs_dir = Path('logs')
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Memory pressure check
    status = get_memory_status()
    if status['usage_gb'] > 6:
        handle_memory_pressure()

    try:
        # 1. Load Data
        logger.info("Loading ingested data...")
        telomere_df, anage_df = load_ingested_data(telomere_raw, anage_raw)

        # 2. Filter Wild-Caught / Early-Life
        logger.info("Filtering for wild-caught and early-life individuals...")
        telomere_df = filter_wild_caught_early_life(telomere_df)

        # 3. Convert Units
        logger.info("Converting telomere units to kilobases...")
        telomere_df = convert_units(telomere_df)

        # 4. Merge
        logger.info("Merging telomere and ecological data...")
        merged_df = merge_data(telomere_df, anage_df)

        # 5. Validate and Save
        logger.info("Validating output schema...")
        if validate_output_schema(merged_df, output_file):
            logger.info("Pipeline completed successfully.")
        else:
            logger.error("Schema validation failed. Output not saved.")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()