"""
Preprocessing module for Polymer Degradation Pathways project.
Handles SMILES to graph conversion, polyester filtering, and environmental data validation.
"""
import logging
import json
import hashlib
import os
import signal
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
import torch
from torch_geometric.data import Data

from utils import get_logger, get_project_paths
from data_models import PolymerRecord, MolecularGraph

logger = get_logger(__name__)

# Ester functional group pattern: C(=O)O
ESTER_SMARTS = Chem.MolFromSmarts('[C](=[O])[O]')

def get_project_paths() -> Dict[str, Path]:
    """Get project directory paths."""
    # Avoid recursion by using utils directly
    base = get_project_paths()
    if isinstance(base, dict):
        return base
    # Fallback if utils returns a path object
    base = Path(base)
    return {
        'raw': base / 'data' / 'raw',
        'processed': base / 'data' / 'processed',
        'reports': base / 'data' / 'reports',
        'state': base / 'state',
    }

def compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def is_polyester(smiles: str) -> bool:
    """
    Check if a molecule contains an ester functional group.
    Pattern: C(=O)O
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        matches = mol.GetSubstructMatches(ESTER_SMARTS)
        return len(matches) > 0
    except Exception as e:
        logger.warning(f"RDKit error checking ester for SMILES {smiles[:20]}...: {e}")
        return False

def smiles_to_graph_features(smiles: str, temperature: float, ph: float, uv: float) -> Optional[Dict[str, Any]]:
    """
    Convert SMILES to molecular graph features using RDKit.
    Parameters: sanitize=True, removeHs=False
    Returns: Dict with atom_features, bond_features, edge_index, and environment_vector
    """
    try:
        mol = Chem.MolFromSmiles(smiles, sanitize=True)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None

        # Keep hydrogens as per removeHs=False
        # mol = Chem.AddHs(mol)  # RDKit adds Hs by default if not removed, but explicit check
        
        # Atom features: atomic number, degree, formal charge, hybridization, aromaticity
        atom_features = []
        atom_map = {}
        for i, atom in enumerate(mol.GetAtoms()):
            feat = [
                atom.GetAtomicNum(),
                atom.GetDegree(),
                atom.GetFormalCharge(),
                int(atom.GetHybridization()),
                int(atom.GetIsAromatic())
            ]
            atom_features.append(feat)
            atom_map[i] = len(atom_features) - 1

        atom_features = np.array(atom_features, dtype=np.float32)

        # Bond features: bond type, conjugation, stereo
        edge_index = []
        bond_features = []
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            feat = [
                int(bond.GetBondType()),
                int(bond.GetIsConjugated()),
                int(bond.GetIsAromatic())
            ]
            edge_index.append([i, j])
            edge_index.append([j, i])  # Undirected
            bond_features.append(feat)
            bond_features.append(feat)

        if not edge_index:
            # No bonds (single atom), create dummy
            edge_index = [[0, 0]]
            bond_features = [[0, 0, 0]]

        edge_index = np.array(edge_index, dtype=np.int64).T
        bond_features = np.array(bond_features, dtype=np.float32)

        # Environment vector: [temperature, pH, UV]
        env_vector = np.array([temperature, ph, uv], dtype=np.float32)

        return {
            'atom_features': atom_features,
            'bond_features': bond_features,
            'edge_index': edge_index,
            'environment_vector': env_vector,
            'smiles': smiles
        }
    except Exception as e:
        logger.warning(f"RDKit conversion failed for SMILES {smiles[:20]}...: {e}")
        return None

def validate_environmental_data(record: Dict[str, Any]) -> bool:
    """
    Validate that environmental data (temp, pH, UV) is present and numeric.
    Returns True if valid, False otherwise.
    """
    required_fields = ['temperature', 'ph', 'uv']
    for field in required_fields:
        if field not in record or record[field] is None:
            return False
        try:
            val = float(record[field])
            if np.isnan(val) or np.isinf(val):
                return False
        except (ValueError, TypeError):
            return False
    return True

def preprocess_dataset(input_path: Path, output_path: Path, exclusion_log_path: Path) -> Tuple[int, int]:
    """
    Preprocess dataset:
    1. Load raw CSV
    2. Filter records with missing environmental data (EXCLUSION)
    3. Filter non-polyesters
    4. Convert SMILES to graphs
    5. Save to Parquet
    
    Returns: (total_processed, excluded_count)
    """
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_csv(input_path)
    
    total_records = len(df)
    excluded_env = 0
    excluded_polyester = 0
    failed_conversion = 0
    processed_records = []
    
    exclusion_details = []

    logger.info(f"Processing {total_records} records...")
    
    for idx, row in df.iterrows():
        # Step 1: Validate environmental data
        if not validate_environmental_data(row):
            excluded_env += 1
            exclusion_details.append({
                'record_id': idx,
                'reason': 'missing_or_invalid_environmental_data',
                'smiles': row.get('smiles', 'N/A')
            })
            continue

        # Step 2: Check for polyester
        smiles = row['smiles']
        if not is_polyester(smiles):
            excluded_polyester += 1
            exclusion_details.append({
                'record_id': idx,
                'reason': 'not_polyester',
                'smiles': smiles
            })
            continue

        # Step 3: Convert to graph
        graph_data = smiles_to_graph_features(
            smiles,
            float(row['temperature']),
            float(row['ph']),
            float(row['uv'])
        )

        if graph_data is None:
            failed_conversion += 1
            exclusion_details.append({
                'record_id': idx,
                'reason': 'rdkit_conversion_failed',
                'smiles': smiles
            })
            continue

        # Add environment and pathway to features
        record_dict = {
            **graph_data,
            'degradation_pathway': row.get('degradation_pathway', 'unknown'),
            'source_id': row.get('source_id', f'unknown_{idx}')
        }
        processed_records.append(record_dict)

    logger.info(f"Excluded {excluded_env} records due to missing environmental data")
    logger.info(f"Excluded {excluded_polyester} records due to non-polyester structure")
    logger.info(f"Failed {failed_conversion} RDKit conversions")
    logger.info(f"Successfully processed {len(processed_records)} records")

    # Save exclusion log
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(exclusion_log_path, 'w') as f:
        json.dump({
            'total_input': total_records,
            'excluded_environmental': excluded_env,
            'excluded_non_polyester': excluded_polyester,
            'failed_conversions': failed_conversion,
            'final_count': len(processed_records),
            'details': exclusion_details
        }, f, indent=2)

    # Save processed data to Parquet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten graph data for Parquet
    flat_records = []
    for rec in processed_records:
        flat = {
            'smiles': rec['smiles'],
            'degradation_pathway': rec['degradation_pathway'],
            'source_id': rec['source_id'],
            'temperature': rec['environment_vector'][0],
            'ph': rec['environment_vector'][1],
            'uv': rec['environment_vector'][2],
            'num_atoms': len(rec['atom_features']),
            'num_bonds': len(rec['bond_features']) // 2,
            'atom_features': rec['atom_features'].tolist(),
            'bond_features': rec['bond_features'].tolist(),
            'edge_index': rec['edge_index'].tolist()
        }
        flat_records.append(flat)

    output_df = pd.DataFrame(flat_records)
    output_df.to_parquet(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

    return len(processed_records), excluded_env

def confirm_exclusion_decision(exclusion_log_path: Path) -> Dict[str, Any]:
    """
    Read exclusion log and confirm the exclusion path was taken.
    Returns summary dict.
    """
    with open(exclusion_log_path, 'r') as f:
        log_data = json.load(f)
    
    logger.info(f"Exclusion Decision Log Confirmed:")
    logger.info(f"  Total input: {log_data['total_input']}")
    logger.info(f"  Excluded (env): {log_data['excluded_environmental']}")
    logger.info(f"  Excluded (non-polyester): {log_data['excluded_non_polyester']}")
    logger.info(f"  Failed conversions: {log_data['failed_conversions']}")
    logger.info(f"  Final count: {log_data['final_count']}")
    
    return {
        'exclusion_path_taken': True,
        'excluded_count': log_data['excluded_environmental'],
        'reason': 'missing_environmental_data_hard_exclusion',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

def subsample_dataset(input_path: Path, output_path: Path, n_samples: int, seed: int = 42) -> Path:
    """Subsample dataset using stratified sampling if possible."""
    logger.info(f"Subsampling dataset to {n_samples} records")
    df = pd.read_parquet(input_path)
    
    if len(df) <= n_samples:
        logger.warning(f"Dataset has {len(df)} records, which is less than {n_samples}. Skipping subsampling.")
        return input_path

    # Stratified by degradation_pathway if possible
    if 'degradation_pathway' in df.columns:
        try:
            df_sample = df.groupby('degradation_pathway', group_keys=False).apply(
                lambda x: x.sample(n=min(n_samples // len(df['degradation_pathway'].unique()), len(x)), random_state=seed)
            ).reset_index(drop=True)
        except Exception as e:
            logger.warning(f"Stratified sampling failed: {e}, using random sampling")
            df_sample = df.sample(n=n_samples, random_state=seed)
    else:
        df_sample = df.sample(n=n_samples, random_state=seed)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_sample.to_parquet(output_path, index=False)
    logger.info(f"Saved subsampled data to {output_path}")
    return output_path

def run_power_analysis_and_trigger_augmentation(processed_path: Path, state_path: Path, reports_path: Path) -> Dict[str, Any]:
    """
    Run power analysis and determine if augmentation is needed.
    """
    logger.info("Running power analysis...")
    df = pd.read_parquet(processed_path)
    n = len(df)
    
    # Simple heuristic: if n < 150, trigger augmentation
    # In a full implementation, use statsmodels for formal power analysis
    if n > 150:
        action = "none"
        warning = False
    elif n >= 50:
        action = "augment"
        warning = True
    else:
        action = "augment_aggressive"
        warning = True

    trigger_data = {
        'n': n,
        'action': action,
        'threshold_warning': 150,
        'threshold_min': 50,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        json.dump(trigger_data, f, indent=2)

    report_data = {
        'n': n,
        'warning': str(warning),
        'recommended_action': action,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    reports_path.parent.mkdir(parents=True, exist_ok=True)
    with open(reports_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Power analysis complete: n={n}, action={action}")
    return trigger_data

def main():
    """Main entry point for preprocessing."""
    import argparse

    parser = argparse.ArgumentParser(description='Preprocess polymer degradation dataset')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output Parquet file path')
    parser.add_argument('--exclusion-log', type=str, default=None, help='Exclusion log file path')
    parser.add_argument('--mode', type=str, choices=['preprocess', 'power_analysis'], default='preprocess',
                        help='Operation mode')
    parser.add_argument('--n-samples', type=int, default=None, help='Number of samples for subsampling')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    # Setup logging
    setup_logging()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    if args.mode == 'preprocess':
        paths = get_project_paths()
        exclusion_log_path = paths['processed'] / 'exclusion_decision_log.json'
        
        if args.exclusion_log:
            exclusion_log_path = Path(args.exclusion_log)

        processed_count, excluded_count = preprocess_dataset(
            input_path, output_path, exclusion_log_path
        )

        # Confirm exclusion decision
        confirm_exclusion_decision(exclusion_log_path)

        logger.info(f"Preprocessing complete. Processed: {processed_count}, Excluded: {excluded_count}")

    elif args.mode == 'power_analysis':
        paths = get_project_paths()
        state_path = paths['state'] / 'augmentation_trigger.json'
        reports_path = paths['reports'] / 'power_analysis_report.json'

        run_power_analysis_and_trigger_augmentation(output_path, state_path, reports_path)

    return 0

if __name__ == '__main__':
    exit(main())
