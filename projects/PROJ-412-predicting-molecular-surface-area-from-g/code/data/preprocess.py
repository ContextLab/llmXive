import os
import sys
import json
import logging
import hashlib
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors
from rdkit import RDLogger
from rdkit.Chem import rdDistGeom

# Import from project modules
from code.config import RANDOM_SEED, MAX_MOLECULES
from code.utils.logging import get_logger, log_errors
from code.utils.seed import set_seed

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

# Constants for ETKDG parameters
DEFAULT_NUM_THREADS = 1
DEFAULT_MAX_ATTEMPTS = 20
DEFAULT_ENERGY_MIN_STEPS = 200
FAILURE_REASON_ETKDG_FAIL = 'ETKDG_FAIL'
FAILURE_REASON_MINIMIZATION_FAIL = 'MINIMIZATION_FAIL'
FAILURE_REASON_INVALID_VALENCE = 'INVALID_VALENCE'
FAILURE_REASON_CONFORMER_GENERATION_FAIL = 'CONFORMER_GENERATION_FAIL'
FAILURE_REASON_UNKNOWN_FAIL = 'UNKNOWN_FAIL'

def load_conformer_params(params_path: Path) -> Dict[str, Any]:
    """Load conformer parameters from JSON file."""
    if not params_path.exists():
        logger.warning(f"Conformer params file not found: {params_path}. Using defaults.")
        return {
            "numThreads": DEFAULT_NUM_THREADS,
            "maxAttempts": DEFAULT_MAX_ATTEMPTS,
            "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
            "random_seed": RANDOM_SEED
        }
    try:
        with open(params_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading conformer params: {e}. Using defaults.")
        return {
            "numThreads": DEFAULT_NUM_THREADS,
            "maxAttempts": DEFAULT_MAX_ATTEMPTS,
            "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
            "random_seed": RANDOM_SEED
        }

def extract_2d_features(mol: Chem.Mol) -> Tuple[np.ndarray, np.ndarray]:
    """Extract 2D graph features (atom and bond features)."""
    # Atom features: [atom_type, hybridization, formal_charge]
    atom_features = []
    for atom in mol.GetAtoms():
        atom_type = atom.GetAtomicNum()
        hybridization = int(atom.GetHybridization())
        formal_charge = atom.GetFormalCharge()
        atom_features.append([atom_type, hybridization, formal_charge])
    node_features = np.array(atom_features, dtype=np.float32)

    # Edge features: [bond_type, conjugated, aromatic]
    edge_features = []
    edge_list = []
    for bond in mol.GetBonds():
        start_idx = bond.GetBeginAtomIdx()
        end_idx = bond.GetEndAtomIdx()
        bond_type = int(bond.GetBondType())
        conjugated = int(bond.GetIsConjugated())
        aromatic = int(bond.GetIsAromatic())
        edge_features.append([bond_type, conjugated, aromatic])
        edge_list.append([start_idx, end_idx])
        edge_list.append([end_idx, start_idx]) # Add reverse edge for undirected graph

    edge_features = np.array(edge_features * 2, dtype=np.float32) if edge_features else np.empty((0, 3), dtype=np.float32)
    return node_features, edge_features

def calculate_molecular_weight(mol: Chem.Mol) -> float:
    """Calculate molecular weight using RDKit."""
    return float(rdMolDescriptors.CalcExactMolWt(mol))

def process_molecule_2d(smiles: str, seed_offset: int = 0) -> Optional[Dict[str, Any]]:
    """Process a single molecule: validate, generate conformer, extract features."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        # Add hydrogens for 3D generation
        mol_h = Chem.AddHs(mol)

        # Check atom count (filter > 100 atoms)
        atom_count = mol_h.GetNumAtoms()
        if atom_count > 100:
            return None # Filtered out

        # 3D Conformer Generation
        # Use a seed based on the global seed + offset to ensure reproducibility
        current_seed = RANDOM_SEED + seed_offset

        # Generate conformer using ETKDG
        params = AllChem.ETKDGv3()
        params.randomSeed = current_seed
        params.numThreads = DEFAULT_NUM_THREADS
        params.maxAttempts = DEFAULT_MAX_ATTEMPTS

        try:
            conf_id = AllChem.EmbedMolecule(mol_h, params)
            if conf_id == -1:
                return {
                    "smiles": smiles,
                    "failure_reason": FAILURE_REASON_ETKDG_FAIL,
                    "atom_count": atom_count,
                    "numThreads": DEFAULT_NUM_THREADS,
                    "maxAttempts": DEFAULT_MAX_ATTEMPTS,
                    "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
                    "random_seed": current_seed,
                    "success": False
                }

            # Energy Minimization
            try:
                result = AllChem.MMFFOptimizeMolecule(mol_h, maxIters=DEFAULT_ENERGY_MIN_STEPS)
                if result != 0:
                    return {
                        "smiles": smiles,
                        "failure_reason": FAILURE_REASON_MINIMIZATION_FAIL,
                        "atom_count": atom_count,
                        "numThreads": DEFAULT_NUM_THREADS,
                        "maxAttempts": DEFAULT_MAX_ATTEMPTS,
                        "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
                        "random_seed": current_seed,
                        "success": False
                    }
            except Exception as e:
                return {
                    "smiles": smiles,
                    "failure_reason": FAILURE_REASON_MINIMIZATION_FAIL,
                    "atom_count": atom_count,
                    "numThreads": DEFAULT_NUM_THREADS,
                    "maxAttempts": DEFAULT_MAX_ATTEMPTS,
                    "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
                    "random_seed": current_seed,
                    "success": False
                }

            # Extract 2D features
            node_features, edge_features = extract_2d_features(mol)

            # Get conformer coordinates
            conf = mol_h.GetConformer()
            coords = conf.GetPositions()

            return {
                "smiles": smiles,
                "node_features": node_features,
                "edge_features": edge_features,
                "molecular_weight": calculate_molecular_weight(mol),
                "atom_count": atom_count,
                "conformer_coords": coords,
                "success": True
            }

        except ValueError as ve:
            return {
                "smiles": smiles,
                "failure_reason": FAILURE_REASON_INVALID_VALENCE,
                "atom_count": atom_count,
                "numThreads": DEFAULT_NUM_THREADS,
                "maxAttempts": DEFAULT_MAX_ATTEMPTS,
                "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
                "random_seed": current_seed,
                "success": False
            }
        except RuntimeError as re:
            # Determine if ETKDG or Minimization failure
            # Since we catch ETKDG failure explicitly above, this is likely minimization or generic
            if "ETKDG" in str(re):
                return {
                    "smiles": smiles,
                    "failure_reason": FAILURE_REASON_ETKDG_FAIL,
                    "atom_count": atom_count,
                    "numThreads": DEFAULT_NUM_THREADS,
                    "maxAttempts": DEFAULT_MAX_ATTEMPTS,
                    "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
                    "random_seed": current_seed,
                    "success": False
                }
            else:
                return {
                    "smiles": smiles,
                    "failure_reason": FAILURE_REASON_MINIMIZATION_FAIL,
                    "atom_count": atom_count,
                    "numThreads": DEFAULT_NUM_THREADS,
                    "maxAttempts": DEFAULT_MAX_ATTEMPTS,
                    "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
                    "random_seed": current_seed,
                    "success": False
                }
        except Exception as e:
            return {
                "smiles": smiles,
                "failure_reason": FAILURE_REASON_UNKNOWN_FAIL,
                "atom_count": atom_count,
                "numThreads": DEFAULT_NUM_THREADS,
                "maxAttempts": DEFAULT_MAX_ATTEMPTS,
                "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
                "random_seed": current_seed,
                "success": False
            }

    except Exception as e:
        # Catch-all for unexpected errors
        return {
            "smiles": smiles,
            "failure_reason": FAILURE_REASON_UNKNOWN_FAIL,
            "atom_count": 0,
            "numThreads": DEFAULT_NUM_THREADS,
            "maxAttempts": DEFAULT_MAX_ATTEMPTS,
            "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
            "random_seed": RANDOM_SEED,
            "success": False
        }

def process_chunk_3d(df_chunk: pd.DataFrame, start_offset: int = 0) -> Tuple[List[Dict], List[Dict], int, int]:
    """Process a chunk of molecules for 3D conformer generation.
    
    Returns:
        successful_results: List of dicts with conformer data
        failed_results: List of dicts with failure info
        total_attempted: Count of molecules attempted
        total_failed: Count of molecules failed
    """
    successful_results = []
    failed_results = []
    total_attempted = 0
    total_failed = 0

    for idx, row in df_chunk.iterrows():
        smiles = row['smiles']
        # Use row index as offset to ensure unique seeds within chunk
        result = process_molecule_2d(smiles, seed_offset=idx + start_offset)
        total_attempted += 1

        if result is None:
            # Invalid SMILES or filtered out (e.g., >100 atoms)
            # Log to excluded molecules if needed, but here we just skip
            continue
        
        if result.get('success', False):
            successful_results.append(result)
        else:
            failed_results.append(result)
            total_failed += 1

    return successful_results, failed_results, total_attempted, total_failed

def save_conformer_params(params: Dict[str, Any], output_path: Path):
    """Save conformer parameters to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.info(f"Saved conformer params to {output_path}")

def save_failure_report(failures: List[Dict], output_path: Path):
    """Save failure report to CSV."""
    if not failures:
        # Create empty file with headers if no failures
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=['smiles', 'failure_reason', 'atom_count', 'numThreads', 'maxAttempts', 'energyMinimizationSteps', 'random_seed']).to_csv(output_path, index=False)
        logger.warning(f"No conformer failures to report. Created empty file at {output_path}")
        return

    df_failures = pd.DataFrame(failures)
    # Ensure columns are in the correct order
    cols = ['smiles', 'failure_reason', 'atom_count', 'numThreads', 'maxAttempts', 'energyMinimizationSteps', 'random_seed']
    df_failures = df_failures[cols]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_failures.to_csv(output_path, index=False)
    logger.info(f"Saved {len(failures)} conformer failures to {output_path}")

def save_conformers_parquet(successful_results: List[Dict], output_path: Path):
    """Save successful conformers to Parquet."""
    if not successful_results:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Create empty dataframe with expected schema
        df = pd.DataFrame(columns=['smiles', 'node_features', 'edge_features', 'molecular_weight', 'atom_count', 'conformer_coords'])
        df.to_parquet(output_path, index=False)
        logger.warning(f"No successful conformers to save. Created empty file at {output_path}")
        return

    # Prepare data for DataFrame
    data = []
    for res in successful_results:
        data.append({
            'smiles': res['smiles'],
            'node_features': res['node_features'],
            'edge_features': res['edge_features'],
            'molecular_weight': res['molecular_weight'],
            'atom_count': res['atom_count'],
            'conformer_coords': res['conformer_coords']
        })
    
    df = pd.DataFrame(data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(successful_results)} successful conformers to {output_path}")

def save_state_file(total_attempted: int, total_failed: int, output_path: Path):
    """Save the global state (counts) to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "total_attempted": total_attempted,
        "total_failed": total_failed,
        "global_failure_rate": total_failed / total_attempted if total_attempted > 0 else 0.0
    }
    with open(output_path, 'w') as f:
        json.dump(state, f, indent=2)
    logger.info(f"Saved state to {output_path}")

def main():
    """Main entry point for T015a: 3D conformer generation."""
    set_seed(RANDOM_SEED)
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "processed" / "sampled_dataset.parquet"
    output_dir = project_root / "data" / "processed"
    params_path = output_dir / "conformer_params.json"
    failure_report_path = output_dir / "failure_report.csv"
    conformers_path = output_dir / "conformers.parquet"
    state_path = output_dir / "conformer_state.json"
    log_path = project_root / "logs" / "conformer_failures.log"

    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Load input data
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Please run T014-Sample first.")
        sys.exit(1)

    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} molecules from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    # Save conformer parameters
    params = {
        "numThreads": DEFAULT_NUM_THREADS,
        "maxAttempts": DEFAULT_MAX_ATTEMPTS,
        "energyMinimizationSteps": DEFAULT_ENERGY_MIN_STEPS,
        "random_seed": RANDOM_SEED
    }
    save_conformer_params(params, params_path)

    # Process chunks
    # We process the whole dataset as one chunk for simplicity, but could be chunked
    all_successful = []
    all_failed = []
    total_attempted_global = 0
    total_failed_global = 0

    # Process in batches to manage memory and log state periodically
    batch_size = 1000
    total_rows = len(df)
    
    for i in range(0, total_rows, batch_size):
        chunk = df.iloc[i:i+batch_size]
        start_offset = i
        
        successful, failed, attempted, failed_count = process_chunk_3d(chunk, start_offset)
        
        all_successful.extend(successful)
        all_failed.extend(failed)
        total_attempted_global += attempted
        total_failed_global += failed_count

        # Log state after each batch
        save_state_file(total_attempted_global, total_failed_global, state_path)
        
        # Check global failure rate
        if total_attempted_global > 0:
            failure_rate = total_failed_global / total_attempted_global
            if failure_rate > 0.10:
                logger.warning(f"Global failure rate {failure_rate:.2%} exceeds 10% threshold. Halting.")
                # Log failures to log file
                with open(log_path, 'a') as f_log:
                    for fail in all_failed:
                        f_log.write(f"{fail['smiles']} - {fail['failure_reason']}\n")
                
                # Save final failure report
                save_failure_report(all_failed, failure_report_path)
                # Save empty conformers file if all failed or partial
                save_conformers_parquet(all_successful, conformers_path)
                sys.exit(1)

    # Final state save
    save_state_file(total_attempted_global, total_failed_global, state_path)

    # Log final failure counts to log file
    with open(log_path, 'a') as f_log:
        for fail in all_failed:
            f_log.write(f"{fail['smiles']} - {fail['failure_reason']}\n")

    # Save outputs
    save_failure_report(all_failed, failure_report_path)
    save_conformers_parquet(all_successful, conformers_path)

    logger.info(f"Conformer generation complete. Total attempted: {total_attempted_global}, Failed: {total_failed_global}")
    logger.info(f"Success rate: {(total_attempted_global - total_failed_global) / total_attempted_global:.2%}" if total_attempted_global > 0 else "Success rate: N/A")

if __name__ == "__main__":
    main()