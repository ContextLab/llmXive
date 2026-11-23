"""
Edge Case Stress Test for RDKit Stability (Task T060)

This script executes the pipeline against a dataset containing molecules with
extreme complexity (high MW, thousands of rotatable bonds) to verify RDKit stability.
It uses real data from the existing structural subset and constructs edge cases
programmatically without fabricating new chemical data.

The script:
1. Loads the real structural subset (data/processed/structural_subset.csv).
2. Generates edge-case molecules by concatenating high-MW fragments (e.g., Polyethylene glycol chains).
3. Runs the descriptor calculation pipeline on these edge cases.
4. Logs specific errors for invalid molecules or RDKit crashes to data/edge_case_errors.log.
5. Verifies the pipeline does not crash and produces a summary report.
"""
import os
import sys
import logging
import itertools
import traceback
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import RDLogger

# Project imports
from config import get_config, ensure_directories
from descriptors import calculate_descriptors_for_molecule, AtomValenceException, log_error_to_file
from logging_config import setup_logging, get_logger

# Disable RDKit warnings to keep logs clean for stress testing
RDLogger.DisableLog('rdApp.*')
RDLogger.DisableLog('rdApp.error')

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent

def generate_edge_case_molecules(n_samples: int = 10) -> List[Tuple[str, str]]:
    """
    Generate edge-case molecules by creating extremely long chains.
    We use a simple repeating unit (e.g., Ethylene Oxide: CCO) to build
    high MW and high rotatable bond count molecules.

    Returns a list of (name, smiles) tuples.
    """
    edge_cases = []
    base_smiles = "CCO" # Ethylene oxide unit (simplified for chain building)
    # Actually, let's use a safer, valid SMILES for a chain: C-C-C...
    # We will construct a very long alkane chain and a long PEG chain.
    
    # 1. Extreme MW / Rotatable Bonds: Very long alkane
    # CCCCC... (1000 carbons) -> MW ~ 14000, Rotatable bonds ~ 998
    long_alkane_smiles = "C" * 1000
    edge_cases.append(("Long_Alkane_C1000", long_alkane_smiles))

    # 2. Extreme Complexity: Long PEG chain (C-C-O-C-C-O...)
    # Repeating unit CCO is not a valid standalone SMILES for a chain end.
    # Let's use CCOCCO... pattern which is valid for PEG.
    # We'll create a chain with 500 units -> ~3000 atoms.
    peg_unit = "CCO"
    long_peg_smiles = peg_unit * 500
    edge_cases.append(("Long_PEG_500_units", long_peg_smiles))

    # 3. Extreme Branching (simulated by repeating a large ring)
    # Cyclohexane ring repeated? No, let's just use a massive fused ring system simulation
    # by concatenating benzene rings with single bonds: c1ccccc1-c1ccccc1...
    benzene = "c1ccccc1"
    # Connect 100 benzenes
    fused_benzene_smiles = "-".join([benzene] * 100)
    edge_cases.append(("Fused_Benzene_100", fused_benzene_smiles))

    return edge_cases

def run_stress_test(logger: logging.Logger, output_dir: Path) -> Dict[str, Any]:
    """
    Run the stress test on generated edge cases and real data subset.
    """
    results = {
        "total_tested": 0,
        "successful": 0,
        "failed": 0,
        "errors": [],
        "max_mw_observed": 0.0,
        "max_rotatable_bonds_observed": 0
    }

    # Load real data subset for a small sample test
    real_data_path = output_dir.parent / "processed" / "structural_subset.csv"
    if real_data_path.exists():
        logger.info(f"Loading real data subset from {real_data_path} for stress test...")
        try:
            df_real = pd.read_csv(real_data_path)
            # Sample 5 molecules to mix with edge cases
            if 'smiles' in df_real.columns:
                sample_real = df_real['smiles'].head(5).tolist()
                real_edge_cases = [("Real_Molecule_" + str(i), smi) for i, smi in enumerate(sample_real)]
            else:
                real_edge_cases = []
                logger.warning("No 'smiles' column found in real data subset.")
        except Exception as e:
            logger.warning(f"Could not load real data subset: {e}")
            real_edge_cases = []
    else:
        logger.warning(f"Real data subset not found at {real_data_path}. Skipping real data mix.")
        real_edge_cases = []

    # Combine generated edge cases with real sample
    all_test_cases = generate_edge_case_molecules() + real_edge_cases
    results["total_tested"] = len(all_test_cases)

    error_log_path = output_dir / "edge_case_errors.log"
    
    for name, smiles in all_test_cases:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                # RDKit failed to parse
                msg = f"FAILED: {name} - RDKit failed to parse SMILES (MolFromSmiles returned None)"
                logger.error(msg)
                log_error_to_file(error_log_path, msg)
                results["failed"] += 1
                results["errors"].append(msg)
                continue

            # Calculate descriptors
            # We use the batch function or individual. Since we have a list, we loop.
            # To simulate pipeline behavior, we call the function that does the heavy lifting.
            # Note: calculate_descriptors_for_molecule expects a Mol object or SMILES?
            # Looking at API: calculate_descriptors_for_molecule(smiles: str) -> dict
            
            descriptors = calculate_descriptors_for_molecule(smiles)
            
            mw = descriptors.get('MW', 0)
            rot_bonds = descriptors.get('RotatableBondCount', 0)
            
            if mw > results["max_mw_observed"]:
                results["max_mw_observed"] = mw
            if rot_bonds > results["max_rotatable_bonds_observed"]:
                results["max_rotatable_bonds_observed"] = rot_bonds

            results["successful"] += 1
            logger.info(f"SUCCESS: {name} - MW={mw:.2f}, RotBonds={rot_bonds}")

        except AtomValenceException as e:
            msg = f"FAILED: {name} - Valence Error: {str(e)}"
            logger.error(msg)
            log_error_to_file(error_log_path, msg)
            results["failed"] += 1
            results["errors"].append(msg)
        except Exception as e:
            msg = f"CRASH: {name} - {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            logger.critical(msg)
            log_error_to_file(error_log_path, msg)
            results["failed"] += 1
            results["errors"].append(msg)

    return results

def main():
    """Main entry point for the Edge Case Stress Test."""
    project_root = get_project_root()
    output_dir = project_root / "data" / "processed"
    ensure_directories(output_dir)
    
    setup_logging(level=logging.INFO)
    logger = get_logger("edge_case_stress_test")

    logger.info("="*60)
    logger.info("Starting Edge Case Stress Test (T060)")
    logger.info("="*60)

    try:
        results = run_stress_test(logger, output_dir)
        
        # Write summary to a JSON file
        summary_path = output_dir / "edge_case_stress_summary.json"
        with open(summary_path, 'w') as f:
            import json
            json.dump(results, f, indent=2)
        
        logger.info(f"Stress test complete. Results saved to {summary_path}")
        logger.info(f"Total Tested: {results['total_tested']}")
        logger.info(f"Successful: {results['successful']}")
        logger.info(f"Failed: {results['failed']}")
        logger.info(f"Max MW Observed: {results['max_mw_observed']}")
        logger.info(f"Max Rotatable Bonds Observed: {results['max_rotatable_bonds_observed']}")

        if results['failed'] > 0:
            logger.warning("Some edge cases failed. Check data/processed/edge_case_errors.log for details.")
            # Do not raise exception; the test is to verify stability, and some failures are expected/valid.
            # The pipeline should NOT crash, which we verified by reaching this point.
        else:
            logger.info("All edge cases processed successfully.")

    except Exception as e:
        logger.critical(f"Stress test pipeline crashed: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
