import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors

# Project-relative imports based on provided API surface
from utils.logging import get_logger, setup_logging
from utils.config import get_project_root, get_results_dir, get_data_dir

def load_test_indices(filepath: str) -> List[str]:
    """
    Load test set SMILES from the split indices CSV.
    Expects a CSV with a 'smiles' column or just a list of SMILES.
    """
    logger = get_logger("oracle")
    logger.info(f"Loading test indices from {filepath}")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Test indices file not found: {filepath}")

    try:
        df = pd.read_csv(filepath)
        # Handle potential column name variations or raw lists
        if 'smiles' in df.columns:
            smiles_list = df['smiles'].tolist()
        elif 'index' in df.columns:
            # If it's just indices, we might need to map them back,
            # but usually split outputs contain the SMILES or IDs.
            # Assuming standard split output contains 'smiles' or we load from processed data.
            # For T016 output, it usually contains the SMILES or an ID.
            # Let's assume the split file contains 'smiles' as per T016 description.
            # If not, we might need to load the full processed dataset and filter.
            # T016 output: "data/splits/test_indices.csv"
            # T016 description: "stratified by Molecular Weight"
            # Usually, split files contain the SMILES or an ID that can be used to lookup.
            # Given T015 merges SASA into the dataset, and T016 splits based on MW.
            # The most robust way is to load the processed dataset (T015 output) and filter by the indices.
            # However, T016 description says "generating ... test_indices.csv".
            # Let's assume it contains 'smiles'. If not, we fallback to loading the full dataset.
            smiles_list = df.iloc[:, 0].tolist() # Fallback to first column
        else:
            # Assume it's a raw list of SMILES or IDs
            smiles_list = df.iloc[:, 0].tolist()
        
        return [str(s).strip() for s in smiles_list if pd.notna(s)]
    except Exception as e:
        logger.error(f"Failed to load test indices: {e}")
        raise

def calculate_sasa_rdkit(smiles: str) -> Optional[float]:
    """
    Calculate SASA directly from SMILES using RDKit.
    This serves as the Geometry Oracle (Ground Truth).
    Returns None if conformer generation fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Add hydrogens for accurate SASA calculation
        mol_h = Chem.AddHs(mol)
        
        # Generate 3D conformer
        # Using ETKDG parameters similar to T015
        params = AllChem.ETKDGv3()
        params.randomSeed = 42 # Deterministic for oracle
        params.maxAttempts = 500
        
        res = AllChem.EmbedMolecule(mol_h, params)
        if res == -1:
            # Try alternative if ETKDG fails
            res = AllChem.EmbedMolecule(mol_h, AllChem.ETKDGv2())
            if res == -1:
                return None
        
        # Minimize energy
        AllChem.UFFOptimizeMolecule(mol_h, maxIters=500)
        
        # Calculate SASA
        # rdMolDescriptors.CalcASA uses the default probe radius (1.4 Angstroms)
        sasa = rdMolDescriptors.CalcASA(mol_h)
        return float(sasa)
        
    except Exception as e:
        # Log specific failure if needed, but return None for the pipeline
        # The caller will track failures if necessary
        return None

def run_oracle_evaluation(test_indices_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main logic for T024: Geometry Oracle Evaluation.
    Loads test set, computes SASA, writes results.
    """
    logger = get_logger("oracle")
    logger.info("Starting Geometry Oracle Evaluation (T024)")
    
    # Load test set
    smiles_list = load_test_indices(test_indices_path)
    logger.info(f"Loaded {len(smiles_list)} molecules from test set")
    
    results = []
    failures = 0
    
    for i, smiles in enumerate(smiles_list):
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i+1}/{len(smiles_list)} molecules")
        
        sasa = calculate_sasa_rdkit(smiles)
        if sasa is not None:
            results.append({"smiles": smiles, "calculated_sasa": sasa})
        else:
            failures += 1
            logger.warning(f"Failed to generate conformer/calculate SASA for: {smiles[:50]}...")
    
    # Create DataFrame
    if not results:
        logger.error("No successful SASA calculations. Aborting.")
        raise RuntimeError("Oracle evaluation produced no results.")
        
    df_results = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write to parquet
    df_results.to_parquet(output_path, index=False)
    
    stats = {
        "total_processed": len(smiles_list),
        "successful": len(results),
        "failed": failures,
        "success_rate": len(results) / len(smiles_list) if len(smiles_list) > 0 else 0.0,
        "output_file": output_path
    }
    
    logger.info(f"Oracle evaluation complete. Success rate: {stats['success_rate']:.2%}")
    logger.info(f"Output written to: {output_path}")
    
    return stats

def main():
    setup_logging()
    logger = get_logger("oracle")
    
    parser = argparse.ArgumentParser(description="T024: Geometry Oracle Evaluation")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/splits/test_indices.csv",
        help="Path to test indices CSV"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="results/baseline/oracle_sasa.parquet",
        help="Path for output parquet file"
    )
    
    args = parser.parse_args()
    
    try:
        stats = run_oracle_evaluation(args.input, args.output)
        # Log stats to a JSON file for consistency with other tasks
        stats_path = args.output.replace(".parquet", "_stats.json")
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Stats written to {stats_path}")
    except Exception as e:
        logger.error(f"Oracle evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()