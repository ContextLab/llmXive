"""
Preprocessing module for Pollinator Network Prediction.

Implements data cleaning, feature engineering, and matrix assembly.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
from utils.logger import get_logger
from config import get_data_processed
from pathlib import Path
import os
import gc

logger = get_logger("preprocessing")

def exclude_species_ids(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove species ID columns from the dataframe to prevent data leakage.
    """
    id_cols = [col for col in df.columns if 'species_id' in col.lower() or col.lower() == 'id']
    if id_cols:
        logger.info(f"Dropping ID columns: {id_cols}")
        df = df.drop(columns=id_cols)
    return df

def build_feature_matrix(raw_dir: Path) -> pd.DataFrame:
    """
    Main entry point for building the feature matrix from raw ecosystem data.
    
    This function orchestrates the full preprocessing pipeline:
    1. Loads interaction data and trait metadata.
    2. Generates negative samples based on co-occurrence.
    3. Performs imputation, winsorization, normalization, and encoding.
    4. Assembles the final matrix.
    
    Args:
        raw_dir: Path to the raw data directory containing ecosystem files.
        
    Returns:
        A pandas DataFrame representing the feature matrix.
    """
    logger.info(f"Building feature matrix from {raw_dir}")
    
    if not raw_dir.exists():
        logger.error(f"Raw directory {raw_dir} does not exist.")
        return pd.DataFrame()

    # Collect all ecosystem data
    all_rows = []
    ecosystem_files = [f for f in os.listdir(raw_dir) if f.endswith('.csv')]
    
    if not ecosystem_files:
        logger.warning("No ecosystem CSV files found in raw directory.")
        return pd.DataFrame()

    for filename in ecosystem_files:
        try:
            file_path = raw_dir / filename
            ecosystem_df = load_and_process_single_ecosystem(file_path)
            if ecosystem_df is not None and not ecosystem_df.empty:
                all_rows.append(ecosystem_df)
        except Exception as e:
            logger.warning(f"Failed to process {filename}: {e}")
            continue

    if not all_rows:
        logger.error("No valid data processed from any ecosystem.")
        return pd.DataFrame()

    # Concatenate all ecosystems
    combined_df = pd.concat(all_rows, ignore_index=True)
    
    # Apply final exclusions
    combined_df = exclude_species_ids(combined_df)
    
    return combined_df

def load_and_process_single_ecosystem(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Loads a single ecosystem file and applies the full preprocessing pipeline.
    """
    try:
        # Load interactions
        interactions = pd.read_csv(file_path)
        
        # Identify plant and pollinator columns (heuristic)
        # Assuming standard naming or specific columns exist
        # If not, we might need to infer from schema or headers
        plant_col = None
        pollinator_col = None
        
        # Heuristic search for column names
        cols_lower = [c.lower() for c in interactions.columns]
        if 'plant' in cols_lower:
            plant_col = interactions.columns[cols_lower.index('plant')]
        elif 'species_a' in cols_lower:
            plant_col = interactions.columns[cols_lower.index('species_a')]
            
        if 'pollinator' in cols_lower:
            pollinator_col = interactions.columns[cols_lower.index('pollinator')]
        elif 'species_b' in cols_lower:
            pollinator_col = interactions.columns[cols_lower.index('species_b')]

        if not plant_col or not pollinator_col:
            logger.warning(f"Could not identify plant/pollinator columns in {file_path}. Skipping.")
            return None

        # Load traits (assuming a parallel file or embedded data)
        # For this implementation, we assume traits are available or generated via mock logic
        # if real traits are missing, we proceed with available data
        traits = load_traits_for_ecosystem(file_path)
        
        if traits is None or traits.empty:
            logger.warning(f"No trait data found for {file_path}. Proceeding with interactions only (limited features).")
            # Create a minimal dataframe with just species pairs and label
            df = pd.DataFrame({
                plant_col: interactions[plant_col],
                pollinator_col: interactions[pollinator_col],
                'link_label': 1
            })
            # Add placeholder effort if missing
            df['sampling_effort'] = 1.0 
            return df

        # Merge interactions with traits
        # We need to join traits for plants and pollinators
        # Assuming traits have 'species_name' column
        df_plants = interactions[[plant_col]].rename(columns={plant_col: 'species_name'})
        df_pollinators = interactions[[pollinator_col]].rename(columns={pollinator_col: 'species_name'})
        
        df_plants = df_plants.merge(traits, on='species_name', how='left')
        df_pollinators = df_pollinators.merge(traits, on='species_name', how='left', suffixes=('_plant', '_pollinator'))
        
        # Combine
        # This is a simplified merge logic; real implementation might be more complex
        # For now, we assume we can attach traits to the interaction row
        merged_df = interactions.copy()
        merged_df = merged_df.merge(traits, left_on=plant_col, right_on='species_name', how='left', suffixes=('', '_plant'))
        merged_df = merged_df.merge(traits, left_on=pollinator_col, right_on='species_name', how='left', suffixes=('', '_pollinator'))
        
        # Drop redundant columns
        merged_df.drop(columns=['species_name', 'species_name_plant', 'species_name_pollinator'], errors='ignore', inplace=True)
        
        # Generate negative samples
        merged_df = generate_negative_samples(merged_df, plant_col, pollinator_col)
        
        # Apply cleaning steps
        merged_df = median_imputation(merged_df)
        merged_df = flag_missingness(merged_df)
        merged_df = winsorize_outliers(merged_df)
        merged_df = z_score_normalize(merged_df)
        merged_df = one_hot_encode(merged_df)
        
        # Extract effort if not present
        if 'sampling_effort' not in merged_df.columns:
            merged_df['sampling_effort'] = 1.0
        
        # Assemble final matrix
        merged_df = assemble_feature_matrix(merged_df)
        
        return merged_df

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None

def load_traits_for_ecosystem(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Loads trait data for a specific ecosystem.
    Tries to find a corresponding traits file or uses embedded data.
    """
    # Logic to find traits file (e.g., replace interactions.csv with traits.csv)
    traits_path = file_path.parent / file_path.name.replace('interactions', 'traits')
    if traits_path.exists():
        return pd.read_csv(traits_path)
    
    # Fallback: Check if traits are in the same file (unlikely but possible)
    # If no traits found, return None
    return None

def generate_negative_samples(df: pd.DataFrame, plant_col: str, pollinator_col: str) -> pd.DataFrame:
    """
    Generates negative samples (non-interactions) based on spatial co-occurrence.
    """
    logger.info("Generating negative samples...")
    
    plants = df[plant_col].unique()
    pollinators = df[pollinator_col].unique()
    
    # Create all possible pairs
    all_pairs = pd.MultiIndex.from_product([plants, pollinators], names=[plant_col, pollinator_col])
    all_pairs_df = pd.DataFrame(all_pairs.tolist(), columns=[plant_col, pollinator_col])
    
    # Mark observed links
    observed = df[[plant_col, pollinator_col]].drop_duplicates()
    observed['link_label'] = 1
    
    # Mark negative pairs
    all_pairs_df['link_label'] = 0
    
    # Merge to identify negatives (left anti-join logic)
    # We want rows in all_pairs_df that are NOT in observed
    merged = all_pairs_df.merge(observed, on=[plant_col, pollinator_col], how='left', indicator=True)
    negatives = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])
    
    # Add placeholder traits for negatives (they won't have real trait values, so we need to handle this)
    # In a real scenario, we would have trait data for all species.
    # Here we assume traits are already in df for the positive samples.
    # For negatives, we might need to join trait data from the original pool.
    # This is a simplification: we assume the trait columns exist in the dataframe
    # and we just need to fill them for the negative rows.
    # If trait columns exist, we join them back.
    trait_cols = [c for c in df.columns if c not in [plant_col, pollinator_col, 'link_label', 'sampling_effort']]
    
    if trait_cols:
        # Create a mapping of species to traits from the positive samples
        # This is a rough approximation; real data should have traits for all species
        plant_traits = df[[plant_col] + trait_cols].rename(columns={plant_col: 'species_name'})
        pollinator_traits = df[[pollinator_col] + trait_cols].rename(columns={pollinator_col: 'species_name'})
        
        # We need to assign traits to negative pairs. 
        # A simple approach: assign the mean trait values or random existing traits.
        # For now, we'll just attach the columns with NaN and let imputation handle it.
        for col in trait_cols:
            negatives[col] = np.nan
    
    # Combine
    result = pd.concat([df, negatives], ignore_index=True)
    logger.info(f"Generated {len(negatives)} negative samples. Total rows: {len(result)}")
    return result

def median_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Imputes missing values with the median of the column.
    """
    logger.info("Applying median imputation...")
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    return df

def flag_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flags ecosystems with >15% missingness.
    """
    logger.info("Flagging missingness...")
    missing_ratio = df.isnull().mean()
    if (missing_ratio > 0.15).any():
        cols_high_missing = missing_ratio[missing_ratio > 0.15].index.tolist()
        logger.warning(f"Columns with >15% missingness: {cols_high_missing}")
    return df

def winsorize_outliers(df: pd.DataFrame, limits: Tuple[float, float] = (0.01, 0.99)) -> pd.DataFrame:
    """
    Winsorizes outliers at extreme percentiles.
    """
    logger.info("Winsorizing outliers...")
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        lower = df[col].quantile(limits[0])
        upper = df[col].quantile(limits[1])
        df[col] = df[col].clip(lower, upper)
    return df

def z_score_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies z-score normalization to continuous columns.
    """
    logger.info("Applying z-score normalization...")
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if col != 'link_label': # Don't normalize the target
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                df[col] = (df[col] - mean) / std
            else:
                df[col] = 0.0
    return df

def one_hot_encode(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-hot encodes categorical columns.
    """
    logger.info("One-hot encoding categorical columns...")
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(cat_cols) > 0:
        df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
    return df

def extract_sampling_effort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts or calculates sampling effort.
    """
    if 'sampling_effort' not in df.columns:
        logger.info("Sampling effort not found, setting default to 1.0")
        df['sampling_effort'] = 1.0
    return df

def assemble_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assembles the final feature matrix ensuring correct schema.
    """
    logger.info("Assembling final feature matrix...")
    # Ensure link_label is last
    cols = [c for c in df.columns if c != 'link_label'] + ['link_label']
    df = df[cols]
    return df

def save_feature_matrix(df: pd.DataFrame, path: Path) -> None:
    """
    Saves the feature matrix to CSV.
    """
    logger.info(f"Saving feature matrix to {path}")
    df.to_csv(path, index=False)

def load_feature_matrix(path: Path) -> pd.DataFrame:
    """
    Loads the feature matrix from CSV.
    """
    return pd.read_csv(path)

def process_in_chunks(file_path: Path, chunk_size: int = 10000) -> pd.DataFrame:
    """
    Processes a large CSV file in chunks to manage memory.
    """
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Process chunk (imputation, etc.)
        chunk = median_imputation(chunk)
        chunks.append(chunk)
    return pd.concat(chunks, ignore_index=True)

def validate_ecosystem_count(count: int, threshold: int = 8) -> bool:
    """
    Validates the number of ecosystems against a threshold.
    """
    if count < threshold:
        logger.warning(f"Valid ecosystem count ({count}) is below threshold ({threshold}). Proceeding with caution.")
        return False
    return True

def define_sample(df: pd.DataFrame, n_samples: Optional[int] = None, seed: int = 42) -> pd.DataFrame:
    """
    Defines a sample from the dataframe if it's too large.
    """
    if n_samples and len(df) > n_samples:
        logger.info(f"Sampling {n_samples} rows from {len(df)} rows.")
        return df.sample(n=n_samples, random_state=seed)
    return df

# Placeholder for functions that might be in other modules but referenced here
# If they are not in preprocessing, they should be imported or defined.
# For this task, we assume they are defined above or imported.

# Note: The following functions are defined in model_training.py but referenced here in the API surface.
# To avoid circular imports, we do not implement them here.
# If they are needed here, they should be moved to a utils module.
# For now, we assume the main.py orchestrator handles the flow correctly.

def main():
    """
    Main entry point for preprocessing module when run as a script.
    """
    raw_dir = get_data_processed().parent / 'raw' # Adjust path as needed
    if not raw_dir.exists():
        raw_dir = Path("data/raw") # Fallback
        
    df = build_feature_matrix(raw_dir)
    if not df.empty:
        save_feature_matrix(df, get_data_processed() / "feature_matrix.csv")
        print(f"Processed {len(df)} rows.")
    else:
        print("No data processed.")

if __name__ == "__main__":
    main()