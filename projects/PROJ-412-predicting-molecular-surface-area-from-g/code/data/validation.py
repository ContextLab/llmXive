import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project utils to ensure correct logging setup
from code.utils.logging import get_logger
from code.utils.config import get_project_root, get_data_dir

# Import RDKit for SMILES validation
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError:
    raise ImportError("RDKit is required. Please install it via: pip install rdkit")

# Import functions from preprocess to handle the actual generation and counting
# We need to ensure we are using the same logic as T014 for consistency
from code.data.preprocess import generate_conformers, load_conformer_config

logger = get_logger(__name__)

FAILURE_THRESHOLD = 0.10  # 10% failure rate threshold

class ValidationStats:
    """Container for validation statistics."""
    def __init__(self):
        self.total_processed: int = 0
        self.valid_smiles: int = 0
        self.invalid_smiles: int = 0
        self.conformer_failures: int = 0
        self.conformer_successes: int = 0
        self.excluded_molecules: List[Dict[str, Any]] = []

    def add_invalid_smiles(self, smiles: str, reason: str):
        self.invalid_smiles += 1
        self.excluded_molecules.append({
            "smiles": smiles,
            "type": "invalid_smiles",
            "reason": reason
        })

    def add_conformer_failure(self, smiles: str, reason: str):
        self.conformer_failures += 1
        self.excluded_molecules.append({
            "smiles": smiles,
            "type": "conformer_failure",
            "reason": reason
        })

    def add_success(self):
        self.valid_smiles += 1
        self.conformer_successes += 1

    @property
    def total_attempts(self) -> int:
        return self.valid_smiles + self.invalid_smiles

    @property
    def total_conformer_attempts(self) -> int:
        return self.conformer_successes + self.conformer_failures

    @property
    def invalid_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.invalid_smiles / self.total_attempts

    @property
    def conformer_failure_rate(self) -> float:
        if self.total_conformer_attempts == 0:
            return 0.0
        return self.conformer_failures / self.total_conformer_attempts

    def log_summary(self):
        logger.info(f"Validation Summary:")
        logger.info(f"  Total SMILES processed: {self.total_attempts}")
        logger.info(f"  Valid SMILES: {self.valid_smiles}")
        logger.info(f"  Invalid SMILES: {self.invalid_smiles} ({self.invalid_rate:.2%})")
        logger.info(f"  Conformer Generation Successes: {self.conformer_successes}")
        logger.info(f"  Conformer Generation Failures: {self.conformer_failures} ({self.conformer_failure_rate:.2%})")

        # Check thresholds
        if self.invalid_rate > FAILURE_THRESHOLD:
            logger.critical(f"INVALID SMILES RATE ({self.invalid_rate:.2%}) exceeds threshold ({FAILURE_THRESHOLD:.2%}). HALTING.")
            raise RuntimeError(f"Invalid SMILES rate {self.invalid_rate:.2%} exceeds threshold {FAILURE_THRESHOLD:.2%}")

        if self.conformer_failure_rate > FAILURE_THRESHOLD:
            logger.critical(f"CONFORMER FAILURE RATE ({self.conformer_failure_rate:.2%}) exceeds threshold ({FAILURE_THRESHOLD:.2%}). HALTING.")
            raise RuntimeError(f"Conformer failure rate {self.conformer_failure_rate:.2%} exceeds threshold {FAILURE_THRESHOLD:.2%}")

        logger.info("Validation thresholds passed.")

def validate_smiles_syntax(smiles: str) -> Tuple[bool, Optional[str]]:
    """
    Validates the syntax of a SMILES string using RDKit.
    
    Args:
        smiles: The SMILES string to validate.
        
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    if not smiles or not isinstance(smiles, str):
        return False, "Empty or non-string input"
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False, "RDKit failed to parse SMILES"
        
        # Check for any issues with the molecule (e.g., valence errors)
        # Note: MolFromSmiles can sometimes return a molecule with warnings
        # We perform a basic sanity check
        if mol.GetNumAtoms() == 0:
            return False, "Molecule has no atoms"
            
        return True, None
    except Exception as e:
        return False, f"RDKit parsing exception: {str(e)}"

def process_single_molecule_with_validation(
    smiles: str, 
    stats: ValidationStats,
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Processes a single molecule: validates SMILES, attempts conformer generation.
    Updates stats and returns molecule data if successful, None otherwise.
    
    Args:
        smiles: The SMILES string.
        stats: The ValidationStats object to update.
        config: Optional conformer generation config.
        
    Returns:
        Dictionary with molecule data if successful, None if failed.
    """
    # 1. Validate SMILES
    is_valid, error_msg = validate_smiles_syntax(smiles)
    if not is_valid:
        stats.add_invalid_smiles(smiles, error_msg)
        return None
    
    # 2. Generate Conformer (simulating the logic from T014)
    # We call the existing generate_conformers logic but wrap it to catch failures
    # Since generate_conformers returns a list of conformers or raises/returns empty on failure
    try:
        # Re-create molecule object for conformer generation
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            # Should be caught by validate_smiles_syntax, but double check
            stats.add_invalid_smiles(smiles, "MolFromSmiles returned None during processing")
            return None
        
        # Add hydrogens
        mol = Chem.AddHs(mol)
        
        # Generate conformers using the utility
        # Note: generate_conformers in preprocess.py expects a Mol object and config
        # We assume it returns a list of successful conformers or raises an exception
        # If it returns an empty list, that counts as a failure
        confs = generate_conformers(mol, config)
        
        if not confs or len(confs) == 0:
            stats.add_conformer_failure(smiles, "No conformers generated")
            return None
        
        # Success
        stats.add_success()
        
        # Return minimal data structure for the pipeline (in real usage, this would be more complex)
        # The actual graph conversion happens in the next step (preprocess.py)
        return {
            "smiles": smiles,
            "mol": mol,
            "conformers": confs
        }
        
    except Exception as e:
        stats.add_conformer_failure(smiles, f"Conformer generation exception: {str(e)}")
        return None

def validate_and_process_dataset(
    input_file: str,
    output_file: Optional[str] = None,
    config_path: Optional[str] = None
) -> ValidationStats:
    """
    Main entry point for validating and processing a dataset of SMILES.
    Reads input, validates each entry, attempts conformer generation,
    logs failures, and halts if failure rate > 10%.
    
    Args:
        input_file: Path to input file (CSV/JSON/TXT with SMILES).
        output_file: Optional path to save valid processed data.
        config_path: Path to conformer config JSON.
        
    Returns:
        ValidationStats object with full results.
        
    Raises:
        RuntimeError: If failure rate exceeds threshold.
    """
    stats = ValidationStats()
    
    # Load config
    if config_path:
        config = load_conformer_config(config_path)
    else:
        # Default config or load from standard location
        project_root = get_project_root()
        default_config_path = project_root / "code" / "utils" / "conformer_config.json"
        if default_config_path.exists():
            config = load_conformer_config(str(default_config_path))
        else:
            config = {} # Fallback to defaults inside generate_conformers
    
    logger.info(f"Starting validation and processing of {input_file}")
    
    # Read input file
    # Assuming simple format: one SMILES per line or CSV with 'smiles' column
    smiles_list = []
    try:
        if input_file.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(input_file)
            if 'smiles' in df.columns:
                smiles_list = df['smiles'].dropna().tolist()
            else:
                logger.error(f"CSV file {input_file} does not contain 'smiles' column")
                raise ValueError(f"Missing 'smiles' column in {input_file}")
        elif input_file.endswith('.txt'):
            with open(input_file, 'r') as f:
                smiles_list = [line.strip() for line in f if line.strip()]
        else:
            # Fallback: try reading as lines
            with open(input_file, 'r') as f:
                smiles_list = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Failed to read input file {input_file}: {e}")
        raise
    
    logger.info(f"Loaded {len(smiles_list)} SMILES strings.")
    
    # Process each molecule
    valid_results = []
    for i, smiles in enumerate(smiles_list):
        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i+1}/{len(smiles_list)} molecules...")
        
        result = process_single_molecule_with_validation(smiles, stats, config)
        if result:
            valid_results.append(result)
    
    # Log summary and check thresholds
    stats.log_summary()
    
    # If we reach here, thresholds were passed
    if output_file:
        # Save valid results
        logger.info(f"Saving {len(valid_results)} valid molecules to {output_file}")
        # In a real scenario, we would serialize the graph data or conformers here
        # For now, we just save the SMILES that passed
        # This is a placeholder for the actual data persistence logic
        # The actual graph generation and SASA calculation would happen in a subsequent pipeline step
        # or integrated here if the task required the full graph output.
        # Given the task is specifically about validation and halting, we ensure the logic is sound.
        # We will save a JSON of the valid SMILES for demonstration, 
        # but in the full pipeline, this would feed into preprocess.py for graph conversion.
        import json
        with open(output_file, 'w') as f:
            json.dump([r['smiles'] for r in valid_results], f)
    
    return stats

def main():
    """Command line interface for validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate SMILES and conformer generation")
    parser.add_argument("--input", type=str, required=True, help="Input SMILES file")
    parser.add_argument("--output", type=str, help="Output file for valid SMILES")
    parser.add_argument("--config", type=str, help="Path to conformer config JSON")
    
    args = parser.parse_args()
    
    try:
        validate_and_process_dataset(args.input, args.output, args.config)
        logger.info("Validation completed successfully.")
    except RuntimeError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()