import logging
import json
import hashlib
import os
import signal
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from utils import get_logger, get_project_paths

def get_project_paths() -> Dict[str, Path]:
    """Return project paths as a dictionary."""
    root = Path(__file__).parent.parent
    return {
        'root': root,
        'raw': root / 'data' / 'raw',
        'processed': root / 'data' / 'processed',
        'state': root / 'state',
        'reports': root / 'data' / 'reports'
    }

def compute_checksum(df: pd.DataFrame, path: str) -> str:
    """Compute SHA256 checksum of a dataframe and save it."""
    content = df.to_csv(index=False).encode('utf-8')
    hash_val = hashlib.sha256(content).hexdigest()
    checksum_path = path + '.sha256'
    with open(checksum_path, 'w') as f:
        f.write(hash_val)
    return hash_val

def is_polyester(smiles: str) -> bool:
    """Check if a molecule is a polyester by detecting ester groups."""
    try:
        import rdkit.Chem as Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        
        # SMARTS pattern for ester: C(=O)O
        # More specific: [C;H0](=[O])[O]
        pattern = Chem.MolFromSmarts('[C;H0](=[O])[O]')
        if pattern is None:
            return False
        
        matches = mol.GetSubstructMatches(pattern)
        return len(matches) > 0
    except Exception as e:
        logging.error(f"Error checking polyester: {e}")
        return False

def smiles_to_graph_features(smiles: str) -> Optional[Dict[str, Any]]:
    """Convert SMILES to a dictionary of graph features."""
    try:
        import rdkit.Chem as Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Atom features: [atomic_num, degree, formal_charge, num_h, chirality]
        atom_features = []
        for atom in mol.GetAtoms():
            feat = [
                atom.GetAtomicNum(),
                atom.GetDegree(),
                atom.GetFormalCharge(),
                atom.GetTotalNumHs(),
                1 if atom.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED else 0
            ]
            atom_features.append(feat)
        
        # Bond features: [bond_type, conjugation, ring]
        bond_features = []
        edge_index = []
        for bond in mol.GetBonds():
            feat = [
                int(bond.GetBondType()),
                1 if bond.GetIsConjugated() else 0,
                1 if bond.IsInRing() else 0
            ]
            bond_features.append(feat)
            edge_index.append([bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()])
            edge_index.append([bond.GetEndAtomIdx(), bond.GetBeginAtomIdx()])
        
        return {
            'atom_features': atom_features,
            'bond_features': bond_features,
            'edge_index': edge_index,
            'smiles': smiles
        }
    except Exception as e:
        logging.error(f"Error converting SMILES to graph: {e}")
        return None

def validate_environmental_data(record: Dict[str, Any]) -> List[str]:
    """Check for missing environmental data (temp, pH, UV)."""
    missing = []
    fields = ['temperature', 'ph', 'uv']
    for field in fields:
        if pd.isna(record.get(field)) or record.get(field) is None:
            missing.append(field)
    return missing

def preprocess_dataset(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Load raw data, filter polyesters, validate environmental data, and convert to graphs.
    """
    logger = get_logger()
    df = pd.read_csv(input_path)
    
    # Filter polyesters
    logger.info(f"Filtering polyesters from {len(df)} records...")
    df['is_polyester'] = df['smiles'].apply(is_polyester)
    df_polyester = df[df['is_polyester']].copy()
    logger.info(f"Found {len(df_polyester)} polyester records.")
    
    # Validate environmental data
    logger.info("Validating environmental data...")
    missing_env_records = []
    valid_records = []
    
    for idx, row in df_polyester.iterrows():
        missing = validate_environmental_data(row.to_dict())
        if missing:
            missing_env_records.append({
                'record_id': row.get('source_id', idx),
                'missing_fields': ','.join(missing)
            })
        else:
            valid_records.append(row)
    
    # Save flagged records
    if missing_env_records:
        flagged_df = pd.DataFrame(missing_env_records)
        flagged_path = get_project_paths()['raw'] / 'flagged_env_data.csv'
        flagged_df.to_csv(str(flagged_path), index=False)
        logger.info(f"Saved {len(missing_env_records)} records with missing env data to {flagged_path}")
    
    if not valid_records:
        logger.warning("No valid records after environmental filtering!")
        return pd.DataFrame()
    
    valid_df = pd.DataFrame(valid_records)
    
    # Convert to graphs
    logger.info("Converting SMILES to graphs...")
    graph_data = []
    for _, row in valid_df.iterrows():
        graph = smiles_to_graph_features(row['smiles'])
        if graph:
            # Flatten graph features for CSV storage or store as JSON string
            # For simplicity in CSV, we'll store the graph as a JSON string in a column
            graph['source_id'] = row.get('source_id')
            graph['degradation_pathway'] = row.get('degradation_pathway')
            graph['temperature'] = row.get('temperature')
            graph['ph'] = row.get('ph')
            graph['uv'] = row.get('uv')
            graph_data.append(graph)
    
    if not graph_data:
        logger.error("No valid graphs generated.")
        return pd.DataFrame()
    
    # Save to parquet (or CSV if parquet is not desired, but spec says parquet)
    # Since we need to store lists in parquet, we can use object dtype
    output_df = pd.DataFrame(graph_data)
    # Convert lists to strings for CSV compatibility if needed, but parquet handles lists
    # However, for the final CSV output, we might need to serialize lists
    # Let's save to parquet first as requested in T015
    parquet_path = get_project_paths()['processed'] / 'graphs.parquet'
    output_df.to_parquet(str(parquet_path), index=False)
    logger.info(f"Saved graph data to {parquet_path}")
    
    # Also save a CSV version for downstream tasks if needed
    # We'll serialize the lists to JSON strings for the CSV
    csv_output = output_df.copy()
    for col in ['atom_features', 'bond_features', 'edge_index']:
        if col in csv_output.columns:
            csv_output[col] = csv_output[col].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)
    
    csv_path = get_project_paths()['processed'] / 'processed_graph_dataset.csv'
    csv_output.to_csv(str(csv_path), index=False)
    compute_checksum(csv_output, str(csv_path))
    logger.info(f"Saved processed graph dataset to {csv_path}")
    
    return csv_output

def confirm_exclusion_decision(excluded_count: int):
    """Confirm that records with missing environmental data are excluded."""
    logger = get_logger()
    paths = get_project_paths()
    decision_log = {
        'status': 'exclusion_confirmed',
        'excluded_count': excluded_count,
        'reason': 'Missing environmental data (temp/pH/UV) is excluded as per Plan Correction.',
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    log_path = paths['processed'] / 'exclusion_decision_log.json'
    with open(str(log_path), 'w') as f:
        json.dump(decision_log, f, indent=2)
    
    logger.info(f"Exclusion decision logged to {log_path}")

def subsample_dataset(df: pd.DataFrame, target_size: int = 150, seed: int = 42) -> pd.DataFrame:
    """Subsample dataset with stratified sampling."""
    if len(df) <= target_size:
        return df
    
    # Stratify by degradation_pathway
    stratify_col = 'degradation_pathway'
    if stratify_col not in df.columns:
        # If no pathway column, just sample randomly
        return df.sample(n=target_size, random_state=seed)
    
    try:
        return df.groupby(stratify_col, group_keys=False).apply(
            lambda x: x.sample(n=min(len(x), int(target_size * len(x) / len(df))), random_state=seed)
        )
    except Exception as e:
        logging.error(f"Stratified sampling failed: {e}. Falling back to random sample.")
        return df.sample(n=target_size, random_state=seed)

def main():
    """
    Main entry point for preprocessing.
    Can be called with --mode power_analysis or --mode preprocess.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Preprocessing pipeline')
    parser.add_argument('--mode', type=str, default='preprocess', choices=['preprocess', 'power_analysis'], help='Mode of operation')
    args = parser.parse_args()
    
    logger = get_logger()
    paths = get_project_paths()
    
    if args.mode == 'power_analysis':
        # This is handled by power_analysis.py, but we can call it here if needed
        from power_analysis import run_power_analysis_from_csv
        input_path = paths['processed'] / 'processed_graph_dataset.csv'
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return
        run_power_analysis_from_csv(str(input_path))
        return
    
    # Preprocess mode
    input_path = paths['raw'] / 'raw_polymer_records.csv'
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    df = preprocess_dataset(str(input_path), str(paths['processed'] / 'processed_graph_dataset.csv'))
    
    if df.empty:
        logger.error("Preprocessing resulted in an empty dataset.")
        return
    
    # Confirm exclusion
    # We need to know how many were excluded. This info is in flagged_env_data.csv
    flagged_path = paths['raw'] / 'flagged_env_data.csv'
    excluded_count = 0
    if flagged_path.exists():
        excluded_count = len(pd.read_csv(flagged_path))
    
    confirm_exclusion_decision(excluded_count)
    
    # Save pre-augmented dataset
    pre_aug_path = paths['processed'] / 'pre_augmented_graph_dataset.csv'
    df.to_csv(str(pre_aug_path), index=False)
    compute_checksum(df, str(pre_aug_path))
    logger.info(f"Saved pre-augmented dataset to {pre_aug_path}")

if __name__ == '__main__':
    main()
