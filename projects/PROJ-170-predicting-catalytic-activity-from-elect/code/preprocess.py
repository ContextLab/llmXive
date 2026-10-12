import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

try:
    from config import get_project_root, get_data_path, get_output_path
except ImportError:
    from code.config import get_project_root, get_data_path, get_output_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_output_path() / 'run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_oc20_experimental_tof() -> pd.DataFrame:
    """Load experimental TOF data from T102."""
    path = get_data_path() / 'raw' / 'experimental_tof.csv'
    if not path.exists():
        raise FileNotFoundError(f"Experimental TOF file not found at {path}")
    logger.info(f"Loading experimental TOF from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded experimental TOF with shape {df.shape}")
    return df


def load_extracted_descriptors() -> pd.DataFrame:
    """Load descriptors extracted in T103 part a."""
    path = get_data_path() / 'processed' / 'unified_dataset.parquet'
    if not path.exists():
        raise FileNotFoundError(f"Unified dataset not found at {path}")
    logger.info(f"Loading unified dataset from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded dataset with shape {df.shape}")
    return df


def normalize_composition(comp: str) -> str:
    """Normalize composition string for matching."""
    return str(comp).strip().lower()


def normalize_facet(facet: str) -> str:
    """Normalize surface facet string for matching."""
    return str(facet).strip().lower()


def normalize_condition(condition: str) -> str:
    """Normalize synthesis condition string for matching."""
    return str(condition).strip().lower()


def align_datasets(df_descriptors: pd.DataFrame, df_experimental: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Align DFT descriptors with experimental TOF data using exact string matching.
    
    FR-002: Align using exact string matching on:
    - composition
    - surface_facet
    - synthesis_condition
    
    Returns:
    - Aligned DataFrame
    - Alignment metrics
    """
    logger.info("Starting alignment using exact string matching (FR-002)")
    
    # Ensure required columns exist
    required_cols_desc = ['composition', 'surface_facet', 'synthesis_condition']
    required_cols_exp = ['composition', 'surface_facet', 'synthesis_condition', 'experimental_tof']
    
    for col in required_cols_desc:
        if col not in df_descriptors.columns:
            logger.warning(f"Column '{col}' not in descriptors, initializing with default")
            df_descriptors[col] = 'unknown'
    
    for col in required_cols_exp:
        if col not in df_experimental.columns:
            logger.warning(f"Column '{col}' not in experimental data")
            if col == 'experimental_tof':
                raise ValueError("experimental_tof column required in experimental data")
            df_experimental[col] = 'unknown'
    
    # Create normalized keys for exact matching
    df_descriptors['_align_key'] = (
        df_descriptors['composition'].apply(normalize_composition) + '|' +
        df_descriptors['surface_facet'].apply(normalize_facet) + '|' +
        df_descriptors['synthesis_condition'].apply(normalize_condition)
    )
    
    df_experimental['_align_key'] = (
        df_experimental['composition'].apply(normalize_composition) + '|' +
        df_experimental['surface_facet'].apply(normalize_facet) + '|' +
        df_experimental['synthesis_condition'].apply(normalize_condition)
    )
    
    # Perform exact match merge
    df_aligned = df_descriptors.merge(
        df_experimental[['_align_key', 'experimental_tof']],
        on='_align_key',
        how='inner'
    )
    
    # Remove alignment key
    df_aligned = df_aligned.drop(columns=['_align_key'])
    
    # Create alignment metrics
    total_experimental = len(df_experimental)
    total_descriptors = len(df_descriptors)
    aligned_count = len(df_aligned)
    
    metrics = {
        'total_experimental_entries': total_experimental,
        'total_descriptor_entries': total_descriptors,
        'aligned_entries': aligned_count,
        'alignment_rate': aligned_count / max(total_experimental, 1),
        'excluded_by_fr002': total_experimental - aligned_count
    }
    
    logger.info(f"Alignment complete:")
    logger.info(f"  - Total experimental: {total_experimental}")
    logger.info(f"  - Total descriptors: {total_descriptors}")
    logger.info(f"  - Aligned: {aligned_count}")
    logger.info(f"  - Alignment rate: {metrics['alignment_rate']:.2%}")
    
    return df_aligned, metrics


def validate_descriptor_columns(df: pd.DataFrame) -> List[str]:
    """Ensure all required descriptor columns are present."""
    required_descriptors = [
        'd_band_center',
        'p_band_center',
        'bader_charges',
        'activation_barrier',
        'reaction_energy'
    ]
    
    missing = [col for col in required_descriptors if col not in df.columns]
    if missing:
        logger.warning(f"Missing descriptor columns: {missing}")
        # Initialize missing columns with NaN
        for col in missing:
            df[col] = np.nan
    
    return [col for col in required_descriptors if col in df.columns or col not in missing]


def get_numeric_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify all numeric columns that are NOT the target variable.
    Target variable is 'experimental_tof'.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Exclude the target variable from scaling features
    target_var = 'experimental_tof'
    if target_var in numeric_cols:
        numeric_cols.remove(target_var)
    
    logger.info(f"Identified {len(numeric_cols)} numeric feature columns")
    return numeric_cols


def build_stoichiometry_vocabulary(df: pd.DataFrame) -> Dict[str, int]:
    """
    Build global element vocabulary from composition strings.
    Returns a mapping of element symbols to unique indices.
    """
    logger.info("Building stoichiometry vocabulary from compositions")
    elements = set()
    
    for comp_str in df['composition'].fillna(''):
        # Simple element extraction: split by non-alphanumeric chars
        import re
        # Match element symbols (uppercase optionally followed by lowercase)
        matches = re.findall(r'[A-Z][a-z]?', str(comp_str))
        elements.update(matches)
    
    # Create vocabulary (sorted for reproducibility)
    vocab = {elem: idx for idx, elem in enumerate(sorted(elements))}
    logger.info(f"Built vocabulary with {len(vocab)} unique elements")
    return vocab


def composition_to_stoich_vector(comp_str: str, vocab: Dict[str, int], vocab_size: int) -> np.ndarray:
    """
    Convert composition string to normalized stoichiometry vector.
    Vector is indexed by element vocabulary and normalized by total count.
    """
    import re
    vector = np.zeros(vocab_size)
    
    if pd.isna(comp_str) or comp_str == '':
        return vector
    
    # Extract element-count pairs
    comp_str = str(comp_str)
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, comp_str)
    
    total_count = 0.0
    for elem, count_str in matches:
        if elem in vocab:
            count = float(count_str) if count_str else 1.0
            vector[vocab[elem]] = count
            total_count += count
    
    # Normalize by total count
    if total_count > 0:
        vector = vector / total_count
    
    return vector


def perform_knn_imputation(df: pd.DataFrame, k: int = 5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform k-NN imputation on descriptor columns based on stoichiometry similarity.
    Target variable (experimental_tof) is excluded from distance calculation.
    Entries with <k neighbors are flagged for exclusion.
    
    Returns:
    - DataFrame with imputed values and exclusion flags
    - Imputation statistics
    """
    logger.info(f"Starting k-NN imputation with k={k}")
    
    # Build stoichiometry vocabulary
    vocab = build_stoichiometry_vocabulary(df)
    vocab_size = len(vocab)
    
    # Identify descriptor columns (all numeric except experimental_tof)
    descriptor_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                     if col != 'experimental_tof']
    
    logger.info(f"Descriptor columns for imputation: {descriptor_cols}")
    
    # Create stoichiometry vectors
    stoich_vectors = np.array([
        composition_to_stoich_vector(comp, vocab, vocab_size)
        for comp in df['composition']
    ])
    
    # Build k-NN model on stoichiometry space
    knn = NearestNeighbors(n_neighbors=k+1, algorithm='auto')  # +1 because query includes itself
    knn.fit(stoich_vectors)
    
    # Track imputation statistics
    imputation_stats = {
        'total_entries': len(df),
        'entries_with_missing': 0,
        'total_imputations': 0,
        'entries_excluded_insufficient_neighbors': 0,
        'excluded_indices': []
    }
    
    df_imputed = df.copy()
    df_imputed['is_imputed'] = False
    df_imputed['excluded_from_training'] = False
    df_imputed['imputation_neighbors'] = 0
    
    # For each entry, check if imputation is needed
    for idx in range(len(df_imputed)):
        row = df_imputed.iloc[idx]
        
        # Check if any descriptor is missing
        has_missing = any(pd.isna(row[col]) for col in descriptor_cols)
        
        if has_missing:
            imputation_stats['entries_with_missing'] += 1
            
            # Find k nearest neighbors in stoichiometry space
            distances, indices = knn.kneighbors([stoich_vectors[idx]])
            
            # Skip self (first neighbor)
            neighbor_indices = indices[0][1:]
            
            if len(neighbor_indices) < k:
                # Insufficient neighbors: flag for exclusion
                logger.warning(f"Entry {idx} has only {len(neighbor_indices)} neighbors (need {k}), excluding from training")
                df_imputed.at[idx, 'excluded_from_training'] = True
                imputation_stats['entries_excluded_insufficient_neighbors'] += 1
                imputation_stats['excluded_indices'].append(int(idx))
            else:
                # Perform imputation using neighbor mean
                for col in descriptor_cols:
                    if pd.isna(row[col]):
                        neighbor_values = df_imputed.iloc[neighbor_indices][col].dropna()
                        if len(neighbor_values) > 0:
                            imputed_value = neighbor_values.mean()
                            df_imputed.at[idx, col] = imputed_value
                            df_imputed.at[idx, 'is_imputed'] = True
                            imputation_stats['total_imputations'] += 1
                
                df_imputed.at[idx, 'imputation_neighbors'] = len(neighbor_indices)
    
    logger.info(f"Imputation complete:")
    logger.info(f"  - Entries with missing values: {imputation_stats['entries_with_missing']}")
    logger.info(f"  - Total imputations performed: {imputation_stats['total_imputations']}")
    logger.info(f"  - Entries excluded (insufficient neighbors): {imputation_stats['entries_excluded_insufficient_neighbors']}")
    
    return df_imputed, imputation_stats


def scale_features(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[pd.DataFrame, StandardScaler]:
    """
    Scale selected numeric features to zero mean and unit variance.
    """
    if not feature_cols:
        logger.warning("No feature columns to scale")
        return df, StandardScaler()
    
    df_scaled = df.copy()
    scaler = StandardScaler()
    
    logger.info(f"Scaling {len(feature_cols)} features")
    scaled_values = scaler.fit_transform(df_scaled[feature_cols])
    df_scaled[feature_cols] = scaled_values
    
    logger.info("Scaling completed")
    return df_scaled, scaler


def save_scaler(scaler: StandardScaler, feature_cols: List[str], output_path: Path) -> None:
    """Save the fitted scaler metadata."""
    scaler_data = {
        'mean': scaler.mean_.tolist(),
        'scale': scaler.scale_.tolist(),
        'var': scaler.var_.tolist(),
        'feature_names': feature_cols
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(scaler_data, f, indent=2)
    
    logger.info(f"Scaler saved to {output_path}")


def generate_catalyst_ids(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate unique catalyst_id by hashing composition, surface_facet, and synthesis_condition.
    """
    logger.info("Generating catalyst IDs")
    
    def make_catalyst_id(row):
        key = f"{row.get('composition', '')}|{row.get('surface_facet', '')}|{row.get('synthesis_condition', '')}"
        hash_obj = hashlib.sha256(key.encode())
        return hash_obj.hexdigest()[:16]
    
    df['catalyst_id'] = df.apply(make_catalyst_id, axis=1)
    logger.info(f"Generated {len(df['catalyst_id'].unique())} unique catalyst IDs")
    return df


def validate_schema_compliance(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame complies with aligned_dataset.schema.yaml.
    """
    logger.info("Validating schema compliance")
    
    required_fields = [
        'catalyst_id',
        'composition',
        'surface_facet',
        'synthesis_condition',
        'd_band_center',
        'experimental_tof',
        'is_imputed',
        'excluded_from_training'
    ]
    
    missing_fields = [f for f in required_fields if f not in df.columns]
    if missing_fields:
        logger.error(f"Missing required fields: {missing_fields}")
        return False
    
    # Check for NaN in target
    if df['experimental_tof'].isna().any():
        logger.error("Found NaN values in experimental_tof (target variable)")
        return False
    
    logger.info("Schema validation passed")
    return True


def main():
    """
    Main execution for T104: Stoichiometry vocabulary, k-NN imputation, and final aligned dataset.
    
    This task:
    1. Builds global element vocabulary
    2. Performs k=5 stoichiometry-space imputation
    3. Applies scaling to zero mean/unit variance
    4. Generates catalyst_id and exclusion flags
    5. Writes aligned_dataset.csv conforming to contract schema
    """
    logger.info("=" * 60)
    logger.info("Starting T104: Stoichiometry vocabulary, k-NN imputation, and final aligned dataset")
    logger.info("=" * 60)
    
    try:
        # Load unified dataset from T103
        df = load_extracted_descriptors()
        
        # Build stoichiometry vocabulary
        vocab = build_stoichiometry_vocabulary(df)
        vocab_path = get_data_path() / 'processed' / 'stoich_vocab.json'
        vocab_path.parent.mkdir(parents=True, exist_ok=True)
        with open(vocab_path, 'w') as f:
            json.dump(vocab, f, indent=2)
        logger.info(f"Saved stoichiometry vocabulary to {vocab_path}")
        
        # Perform k-NN imputation (k=5)
        df_imputed, imputation_stats = perform_knn_imputation(df, k=5)
        
        # Save imputation statistics
        imputation_log_path = get_output_path() / 'imputation_log.json'
        imputation_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(imputation_log_path, 'w') as f:
            json.dump(imputation_stats, f, indent=2)
        logger.info(f"Saved imputation log to {imputation_log_path}")
        
        # Get numeric feature columns for scaling
        feature_cols = get_numeric_feature_columns(df_imputed)
        
        # Scale features
        df_scaled, scaler = scale_features(df_imputed, feature_cols)
        
        # Generate catalyst IDs
        df_scaled = generate_catalyst_ids(df_scaled)
        
        # Validate schema compliance
        if not validate_schema_compliance(df_scaled):
            raise ValueError("Schema validation failed")
        
        # Save scaler metadata
        scaler_path = get_project_root() / 'code' / 'models' / 'scaler_metadata.json'
        scaler_path.parent.mkdir(parents=True, exist_ok=True)
        save_scaler(scaler, feature_cols, scaler_path)
        
        # Write final aligned dataset (CSV format)
        output_path = get_data_path() / 'processed' / 'aligned_dataset.csv'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_scaled.to_csv(output_path, index=False)
        logger.info(f"Saved aligned dataset to {output_path}")
        logger.info(f"Final dataset shape: {df_scaled.shape}")
        
        # Verification
        logger.info("=" * 60)
        logger.info("T104 Verification:")
        logger.info(f"  - Stoichiometry vocabulary size: {len(vocab)}")
        logger.info(f"  - Entries with imputation: {df_scaled['is_imputed'].sum()}")
        logger.info(f"  - Entries excluded from training: {df_scaled['excluded_from_training'].sum()}")
        logger.info(f"  - Final dataset rows: {len(df_scaled)}")
        logger.info(f"  - NaN in experimental_tof: {df_scaled['experimental_tof'].isna().sum()}")
        logger.info(f"  - Unique catalyst IDs: {len(df_scaled['catalyst_id'].unique())}")
        logger.info("=" * 60)
        logger.info("T104 completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in T104: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
