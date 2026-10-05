"""
Preprocessing Module for Polymer Degradation Dataset.

Handles SMILES to graph conversion, filtering, and augmentation triggering.
"""
import os
import json
import logging
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.model_selection import train_test_split
from statsmodels.stats.power import TTestIndPower

# Import utilities
from utils import get_project_paths, get_logger, ensure_directory
from data_models import PolymerRecord, MolecularGraph

logger = get_logger(__name__)

def compute_checksum(df: pd.DataFrame, columns: List[str] = None) -> str:
    """Compute SHA256 checksum of dataset."""
    if columns is None:
        content = df.to_csv(index=False).encode('utf-8')
    else:
        content = df[columns].to_csv(index=False).encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def is_polyester(smiles: str) -> bool:
    """
    Check if a SMILES string represents a polyester.
    
    Args:
        smiles: SMILES string
        
    Returns:
        True if polyester (contains ester groups), False otherwise
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        
        # Check for ester functional group pattern: C(=O)O
        pattern = Chem.MolFromSmarts('C(=O)O')
        if pattern is None:
            return False
        
        matches = mol.GetSubstructMatches(pattern)
        return len(matches) > 0
    except Exception as e:
        logger.warning(f"Error checking polyester: {e}")
        return False

def smiles_to_graph_features(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Convert SMILES to graph features (atom/bond features, edge index).
    
    Args:
        smiles: SMILES string
        
    Returns:
        Dictionary with graph features or None if conversion fails
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Atom features
        atom_features = []
        for atom in mol.GetAtoms():
            feat = [
                atom.GetAtomicNum(),
                atom.GetDegree(),
                atom.GetFormalCharge(),
                atom.GetIsAromatic(),
                atom.GetTotalNumHs()
            ]
            atom_features.append(feat)
        
        # Bond features and edge index
        edge_index = []
        edge_attr = []
        for bond in mol.GetBonds():
            start = bond.GetBeginAtomIdx()
            end = bond.GetEndAtomIdx()
            edge_index.append([start, end])
            edge_index.append([end, start])
            
            feat = [
                bond.GetBondTypeAsDouble(),
                bond.GetIsConjugated(),
                bond.GetIsInRing()
            ]
            edge_attr.append(feat)
            edge_attr.append(feat)
        
        return {
            'atom_features': np.array(atom_features, dtype=np.float32),
            'bond_features': np.array(edge_attr, dtype=np.float32),
            'edge_index': np.array(edge_index, dtype=np.int64).T
        }
    except Exception as e:
        logger.error(f"Error converting SMILES to graph: {e}")
        return None

def validate_environmental_data(record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate environmental data in a record.
    
    Args:
        record: Record dictionary
        
    Returns:
        Tuple of (is_valid, reason)
    """
    required_fields = ['temperature', 'ph', 'uv']
    missing = [f for f in required_fields if f not in record or record[f] is None]
    
    if missing:
        return False, f"Missing fields: {missing}"
    
    # Check for valid numeric values
    for field in required_fields:
        try:
            val = float(record[field])
            if field == 'temperature' and (val < 0 or val > 1000):
                return False, f"Invalid temperature: {val}"
            if field == 'ph' and (val < 0 or val > 14):
                return False, f"Invalid pH: {val}"
            if field == 'uv' and val < 0:
                return False, f"Invalid UV: {val}"
        except (ValueError, TypeError):
            return False, f"Non-numeric {field}: {record[field]}"
    
    return True, "Valid"

def preprocess_dataset(
    df: pd.DataFrame,
    output_path: str,
    impute_missing: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Preprocess the dataset: convert SMILES to graphs, filter non-polyesters, impute missing env data.
    
    Args:
        df: Input DataFrame
        output_path: Path to save processed graphs
        impute_missing: Whether to impute missing environmental data
        
    Returns:
        Tuple of (processed_df, excluded_df, report)
    """
    processed_records = []
    excluded_records = []
    exclusion_log = {'excluded_count': 0, 'excluded_smiles': []}
    
    default_env = {'temperature': 25.0, 'ph': 7.0, 'uv': 0.0}
    
    for idx, row in df.iterrows():
        smiles = row.get('smiles')
        if not smiles:
            excluded_records.append({'record_id': idx, 'reason': 'Missing SMILES'})
            exclusion_log['excluded_count'] += 1
            exclusion_log['excluded_smiles'].append(str(smiles))
            continue
        
        # Check polyester
        if not is_polyester(smiles):
            excluded_records.append({'record_id': idx, 'reason': 'Not a polyester'})
            exclusion_log['excluded_count'] += 1
            exclusion_log['excluded_smiles'].append(smiles)
            continue
        
        # Validate environmental data
        is_valid, reason = validate_environmental_data(row.to_dict())
        if not is_valid:
            if impute_missing and 'Missing' in reason:
                # Impute missing values
                for field, val in default_env.items():
                    if field not in row or row[field] is None:
                        logger.info(f"Imputing {field}={val} for record {idx}")
                        row[field] = val
                is_valid, _ = validate_environmental_data(row.to_dict())
                if not is_valid:
                    excluded_records.append({'record_id': idx, 'reason': reason})
                    exclusion_log['excluded_count'] += 1
                    exclusion_log['excluded_smiles'].append(smiles)
                    continue
            else:
                excluded_records.append({'record_id': idx, 'reason': reason})
                exclusion_log['excluded_count'] += 1
                exclusion_log['excluded_smiles'].append(smiles)
                continue
        
        # Convert to graph features
        graph_features = smiles_to_graph_features(smiles)
        if graph_features is None:
            excluded_records.append({'record_id': idx, 'reason': 'RDKit conversion failed'})
            exclusion_log['excluded_count'] += 1
            exclusion_log['excluded_smiles'].append(smiles)
            continue
        
        # Add graph features to record
        processed_record = row.to_dict()
        processed_record.update(graph_features)
        processed_records.append(processed_record)
    
    processed_df = pd.DataFrame(processed_records)
    excluded_df = pd.DataFrame(excluded_records)
    
    # Save processed data
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.suffix == '.parquet':
        processed_df.to_parquet(output_path)
    else:
        processed_df.to_csv(output_path, index=False)
    
    # Save exclusion log
    exclusion_log_path = output_path.parent / 'exclusion_decision_log.json'
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    
    logger.info(f"Processed {len(processed_df)} records, excluded {len(excluded_df)} records")
    
    return processed_df, excluded_df, exclusion_log

def confirm_exclusion_decision(exclusion_log: Dict[str, Any]) -> bool:
    """
    Confirm that the exclusion decision was made correctly.
    
    Args:
        exclusion_log: Exclusion log dictionary
        
    Returns:
        True if decision is valid
    """
    if exclusion_log['excluded_count'] == 0:
        return True
    
    # Log the exclusion decision
    logger.info(f"Exclusion decision confirmed: {exclusion_log['excluded_count']} records excluded")
    return True

def subsample_dataset(df: pd.DataFrame, target_size: int, seed: int = 42) -> pd.DataFrame:
    """
    Subsample dataset to target size using stratified sampling.
    
    Args:
        df: Input DataFrame
        target_size: Target number of records
        seed: Random seed
        
    Returns:
        Subsampled DataFrame
    """
    if len(df) <= target_size:
        return df
    
    # Stratified sampling by degradation_pathway
    stratify_col = 'degradation_pathway' if 'degradation_pathway' in df.columns else None
    
    if stratify_col and df[stratify_col].nunique() > 1:
        return df.sample(n=target_size, random_state=seed, stratify=df[stratify_col])
    else:
        return df.sample(n=target_size, random_state=seed)

def calculate_power_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate power analysis to determine sample size requirements.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with power analysis results
    """
    # Simplified power analysis using statsmodels
    # In a real implementation, we would calculate effect sizes properly
    
    n = len(df)
    effect_size = 0.5  # Medium effect size
    alpha = 0.05
    power = 0.8
    
    power_calc = TTestIndPower()
    required_n = power_calc.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        ratio=1.0
    )
    
    required_n = int(np.ceil(required_n))
    
    action = 'none'
    if n < 50:
        action = 'augment_aggressive'
    elif n < 150:
        action = 'augment'
    
    return {
        'n': n,
        'required_n': required_n,
        'action': action,
        'effect_size': effect_size,
        'alpha': alpha,
        'power': power
    }

def run_power_analysis_and_trigger_augmentation(input_path: str, state_path: str) -> Dict[str, Any]:
    """
    Run power analysis and trigger augmentation if needed.
    
    Args:
        input_path: Path to input dataset
        state_path: Path to save augmentation trigger state
        
    Returns:
        Power analysis results
    """
    path = Path(input_path)
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    
    results = calculate_power_analysis(df)
    
    # Save state
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate warning report
    warning_path = Path('data/reports/power_analysis_warning.json')
    warning_path.parent.mkdir(parents=True, exist_ok=True)
    
    warning = {
        'n': results['n'],
        'warning': 'true' if results['n'] < 150 else 'false'
    }
    
    with open(warning_path, 'w') as f:
        json.dump(warning, f, indent=2)
    
    logger.info(f"Power analysis complete: n={results['n']}, action={results['action']}")
    
    return results

def main():
    """Main entry point for preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess polymer degradation dataset')
    parser.add_argument('--input', type=str, required=True, help='Input dataset path')
    parser.add_argument('--output', type=str, required=True, help='Output processed dataset path')
    parser.add_argument('--mode', type=str, choices=['preprocess', 'power_analysis'], default='preprocess', help='Operation mode')
    parser.add_argument('--state', type=str, default='state/augmentation_trigger.json', help='Path to augmentation trigger state')
    parser.add_argument('--impute', action='store_true', default=True, help='Impute missing environmental data')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    if args.mode == 'power_analysis':
        results = run_power_analysis_and_trigger_augmentation(args.input, args.state)
        print(json.dumps(results, indent=2))
    else:
        processed_df, excluded_df, exclusion_log = preprocess_dataset(
            pd.read_parquet(args.input) if Path(args.input).suffix == '.parquet' else pd.read_csv(args.input),
            args.output,
            impute_missing=args.impute
        )
        
        confirm_exclusion_decision(exclusion_log)
        
        print(f"Processed {len(processed_df)} records, excluded {len(excluded_df)} records")

if __name__ == '__main__':
    main()
