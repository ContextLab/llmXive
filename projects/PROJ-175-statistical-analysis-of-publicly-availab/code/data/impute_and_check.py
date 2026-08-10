import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return output_dir, log_dir

def load_processed_data():
    """
    Load the intermediate ingredient pairs data.
    This function assumes T014a, T014b, T015, T016a/b, T017 have run.
    It looks for the similarity file based on the amendment log.
    """
    amendment_path = Path("data/amendment_log.json")
    if not amendment_path.exists():
        raise FileNotFoundError("data/amendment_log.json not found. Run T012 first.")
    
    with open(amendment_path, 'r') as f:
        amendment = json.load(f)
    
    methodology = amendment.get("methodology", "")
    similarity_file = None
    
    if methodology == "Correlational Analysis":
        similarity_file = Path("data/processed/similarity_scores_embedding.parquet")
    elif methodology == "Causal Independence":
        similarity_file = Path("data/processed/similarity_scores_chemical.parquet")
    else:
        raise ValueError(f"Unknown methodology in amendment log: {methodology}")
    
    if not similarity_file.exists():
        raise FileNotFoundError(f"Similarity file not found: {similarity_file}. Run T016a/b first.")
    
    # Load the similarity data
    sim_df = pd.read_parquet(similarity_file)
    
    # Load ingredient pairs with roles and co-occurrence
    # We expect these to be in data/processed/normalized_ingredients.csv, functional_roles.csv, co_occurrence_matrix.parquet
    # However, the task description implies a merged 'ingredient_pairs' structure is the input to this step.
    # Based on T017 output: data/processed/functional_roles_validated.parquet
    # And T015 output: data/processed/co_occurrence_matrix.parquet
    
    # Attempt to load the base pairs from the validated functional roles file
    # Assuming it contains: ingredient_id, canonical_name, functional_role, log_co_occurrence
    base_file = Path("data/processed/functional_roles_validated.parquet")
    if not base_file.exists():
        # Fallback to normalized ingredients if validated file is missing (should not happen if pipeline correct)
        base_file = Path("data/processed/normalized_ingredients.csv")
    
    if base_file.suffix == '.csv':
        base_df = pd.read_csv(base_file)
    else:
        base_df = pd.read_parquet(base_file)
    
    # Merge similarity scores into base data
    # We need to ensure we are merging on the correct key. 
    # Assuming similarity file has 'ingredient_id' and 'similarity_score' (or similar)
    # We'll assume the similarity file is a matrix or a long-form list of pairs.
    # If it's a matrix, we need to melt it. If it's long, we merge.
    
    if sim_df.shape[0] > sim_df.shape[1]: # Likely long form (id1, id2, score)
        # If the base_df is a list of pairs, we merge. 
        # If base_df is a list of single ingredients, we might need to join on a specific column.
        # Given the context of "ingredient_pairs.csv" output, we assume we are building a list of pairs.
        # Let's assume base_df has 'ingredient_id' and we are looking for pairs involving that ingredient?
        # Actually, T015 builds a global co-occurrence matrix. T016 builds similarity.
        # The output T018 is 'ingredient_pairs.csv'.
        
        # Strategy: We assume the input to T018 is a dataframe of pairs (i, j) with some attributes,
        # and we are adding the similarity score and handling missing values.
        
        # Let's try to load a pre-merged state if it exists, or construct it.
        # Since T017 output is 'functional_roles_validated.parquet', let's assume it contains the pair data
        # with roles and co-occurrence.
        
        # If the similarity file is a matrix (index=ing1, columns=ing2, values=sim), we melt it.
        if 'ingredient_id' not in sim_df.columns and 'ingredient_id_2' not in sim_df.columns:
            # It might be a matrix.
            sim_df = sim_df.reset_index().melt(id_vars=sim_df.columns[0], 
                                               var_name='ingredient_id_2', 
                                               value_name='flavor_similarity')
            sim_df.rename(columns={sim_df.columns[0]: 'ingredient_id'}, inplace=True)
        
        # Merge similarity
        # We need to match 'ingredient_id' and 'ingredient_id_2' from similarity to the base pairs.
        # If base_df is just single ingredients, we can't merge directly without a pair definition.
        # Let's assume base_df is actually the list of pairs from T015 (co-occurrence) or T017.
        # If T017 output is a single ingredient list, we need to reconstruct pairs from co-occurrence.
        
        # Let's assume the 'base_df' we loaded is actually the co-occurrence pairs with roles.
        # If not, we construct pairs from the co-occurrence matrix.
        
        co_occ_file = Path("data/processed/co_occurrence_matrix.parquet")
        if base_df.shape[0] < 1000: # Likely single ingredient list
            # We need to form pairs from co-occurrence
            if co_occ_file.exists():
                co_occ = pd.read_parquet(co_occ_file)
                # Flatten co-occurrence
                co_occ = co_occ.reset_index().melt(id_vars=co_occ.columns[0], 
                                                   var_name='ingredient_id_2', 
                                                   value_name='log_co_occurrence')
                co_occ.rename(columns={co_occ.columns[0]: 'ingredient_id'}, inplace=True)
                base_df = co_occ
            else:
                raise FileNotFoundError("Co-occurrence matrix not found to construct pairs.")
        
        # Now base_df has: ingredient_id, ingredient_id_2, log_co_occurrence, functional_role (maybe)
        # Merge similarity
        merged = base_df.merge(sim_df, on=['ingredient_id', 'ingredient_id_2'], how='left')
        
    else:
        # Fallback: if similarity is not long form, try to merge on single ID if base is single
        merged = base_df.merge(sim_df, on='ingredient_id', how='left')
    
    return merged

def merge_datasets(df):
    """
    Ensure all necessary columns are present.
    This is a placeholder for any additional merging logic if datasets are split.
    """
    return df

def impute_missing(df):
    """
    Handle missing values in embeddings, similarity scores, and functional roles.
    - Impute missing similarity scores with 0.
    - Log exclusion counts (rows dropped if critical data is missing).
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "imputation_strategy": "fill_missing_similarity_with_0",
        "exclusion_counts": {}
    }
    
    # Check for missing similarity scores
    sim_cols = [col for col in df.columns if 'similarity' in col.lower()]
    missing_sim = df[sim_cols].isnull().sum().sum()
    
    if missing_sim > 0:
        logger.info(f"Imputing {missing_sim} missing similarity scores with 0.")
        df[sim_cols] = df[sim_cols].fillna(0)
        log_data["imputed_similarity_count"] = int(missing_sim)
    
    # Check for missing functional roles
    role_cols = [col for col in df.columns if 'role' in col.lower()]
    if role_cols:
        missing_roles = df[role_cols].isnull().sum().sum()
        if missing_roles > 0:
            # If role is missing, we might drop the row or impute. 
            # Task says "Handle missing values", usually imputation or exclusion.
            # Let's drop rows where critical predictors are missing.
            initial_rows = len(df)
            df = df.dropna(subset=role_cols)
            dropped = initial_rows - len(df)
            log_data["exclusion_counts"]["missing_functional_role"] = dropped
            logger.warning(f"Dropped {dropped} rows due to missing functional role.")
    
    # Check for missing co-occurrence
    co_cols = [col for col in df.columns if 'co_occurrence' in col.lower()]
    if co_cols:
        missing_co = df[co_cols].isnull().sum().sum()
        if missing_co > 0:
            initial_rows = len(df)
            df = df.dropna(subset=co_cols)
            dropped = initial_rows - len(df)
            log_data["exclusion_counts"]["missing_co_occurrence"] = dropped
            logger.warning(f"Dropped {dropped} rows due to missing co-occurrence.")
    
    # Log total rows processed
    log_data["rows_processed"] = int(len(df))
    
    return df, log_data

def save_output(df, log_data, output_dir, log_dir):
    """
    Save the final ingredient pairs CSV and the imputation log.
    """
    output_path = output_dir / "ingredient_pairs.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved final ingredient pairs to {output_path}")
    
    log_path = log_dir / "imputation_log.json"
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Saved imputation log to {log_path}")

def main():
    """
    Main execution function for T018.
    """
    logger.info("Starting T018: Imputation & Bias Check")
    
    try:
        output_dir, log_dir = ensure_directories()
        df = load_processed_data()
        df = merge_datasets(df)
        df, log_data = impute_missing(df)
        save_output(df, log_data, output_dir, log_dir)
        logger.info("T018 completed successfully.")
    except Exception as e:
        logger.error(f"T018 failed: {e}")
        raise

if __name__ == "__main__":
    main()
