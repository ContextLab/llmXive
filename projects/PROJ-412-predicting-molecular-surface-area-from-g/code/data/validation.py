"""
Validation and error handling module for molecular data processing.

This module provides robust validation for SMILES strings and conformer generation,
with failure rate monitoring and early termination logic.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem

from code.utils.logging import get_logger
from code.utils.config import get_data_dir

# Import from preprocess module for conformer generation
from code.data.preprocess import generate_conformers

@dataclass
class ValidationStats:
    """Statistics for validation and processing failures."""
    total_molecules: int = 0
    valid_smiles: int = 0
    invalid_smiles: int = 0
    conformer_success: int = 0
    conformer_failed: int = 0
    excluded_atoms: int = 0
    failed_molecules: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def smiles_validity_rate(self) -> float:
        if self.total_molecules == 0:
            return 0.0
        return self.valid_smiles / self.total_molecules
    
    @property
    def conformer_success_rate(self) -> float:
        if self.valid_smiles == 0:
            return 0.0
        return self.conformer_success / self.valid_smiles
    
    @property
    def overall_failure_rate(self) -> float:
        """Calculate overall failure rate (invalid SMILES + failed conformers)."""
        if self.total_molecules == 0:
            return 0.0
        failures = self.invalid_smiles + self.conformer_failed
        return failures / self.total_molecules
    
    def log_summary(self, logger: logging.Logger) -> None:
        """Log a summary of validation statistics."""
        logger.info("=" * 60)
        logger.info("VALIDATION STATISTICS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total molecules processed: {self.total_molecules}")
        logger.info(f"Valid SMILES: {self.valid_smiles} ({self.smiles_validity_rate:.2%})")
        logger.info(f"Invalid SMILES: {self.invalid_smiles} ({1 - self.smiles_validity_rate:.2%})")
        logger.info(f"Conformer generation successful: {self.conformer_success} ({self.conformer_success_rate:.2%})")
        logger.info(f"Conformer generation failed: {self.conformer_failed} ({1 - self.conformer_success_rate:.2%})")
        logger.info(f"Molecules excluded (too many atoms): {self.excluded_atoms}")
        logger.info(f"Overall failure rate: {self.overall_failure_rate:.2%}")
        logger.info("=" * 60)
        
        if self.failed_molecules:
            logger.warning(f"First 5 failed molecules:")
            for i, fail in enumerate(self.failed_molecules[:5]):
                logger.warning(f"  {i+1}. SMILES: {fail.get('smiles', 'N/A')[:50]}...")
                logger.warning(f"     Reason: {fail.get('reason', 'Unknown')}")
                logger.warning(f"     Atom count: {fail.get('atom_count', 'N/A')}")

def validate_smiles_syntax(smiles: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SMILES string syntax using RDKit.
    
    Args:
        smiles: SMILES string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not smiles or not isinstance(smiles, str):
        return False, "Empty or invalid SMILES type"
        
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False, "RDKit failed to parse SMILES"
        
        # Check for basic sanity
        if mol.GetNumAtoms() == 0:
            return False, "Molecule has no atoms"
            
        # Check for explicit hydrogens that might indicate issues
        if mol.GetNumExplicitHs() > mol.GetNumAtoms() * 4:
            return False, "Suspicious number of explicit hydrogens"
            
        return True, None
        
    except Exception as e:
        return False, f"Exception during validation: {str(e)}"

def check_atom_count(mol: Chem.Mol, max_atoms: int = 100) -> Tuple[bool, int]:
    """
    Check if molecule exceeds maximum atom count.
    
    Args:
        mol: RDKit Mol object
        max_atoms: Maximum allowed atoms
        
    Returns:
        Tuple of (is_valid, atom_count)
    """
    atom_count = mol.GetNumAtoms()
    return atom_count <= max_atoms, atom_count

def process_single_molecule_with_validation(
    smiles: str,
    max_atoms: int = 100,
    logger: Optional[logging.Logger] = None
) -> Tuple[Optional[Chem.Mol], Optional[Dict[str, Any]]]:
    """
    Process a single molecule with full validation and error tracking.
    
    Args:
        smiles: SMILES string
        max_atoms: Maximum allowed atoms
        logger: Optional logger instance
        
    Returns:
        Tuple of (mol_object, failure_info)
        - mol_object: RDKit Mol if successful, None otherwise
        - failure_info: Dict with failure details if failed, None otherwise
    """
    failure_info = None
    
    # Validate SMILES syntax
    is_valid, error_msg = validate_smiles_syntax(smiles)
    if not is_valid:
        failure_info = {
            'smiles': smiles,
            'reason': f"Invalid SMILES: {error_msg}",
            'stage': 'smiles_validation',
            'atom_count': 0
        }
        return None, failure_info
    
    # Convert to RDKit Mol
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        failure_info = {
            'smiles': smiles,
            'reason': 'Failed to convert to RDKit Mol',
            'stage': 'rdkit_conversion',
            'atom_count': 0
        }
        return None, failure_info
    
    # Check atom count
    valid_atoms, atom_count = check_atom_count(mol, max_atoms)
    if not valid_atoms:
        failure_info = {
            'smiles': smiles,
            'reason': f'Too many atoms ({atom_count} > {max_atoms})',
            'stage': 'atom_count_check',
            'atom_count': atom_count
        }
        return None, failure_info
    
    # Try conformer generation
    try:
        # Add hydrogens for better conformer generation
        mol_with_h = Chem.AddHs(mol)
        
        # Generate conformer
        params = AllChem.ETKDGv3()
        params.randomSeed = 42
        params.maxAttempts = 50
        params.numThreads = 1
        
        success = AllChem.EmbedMolecule(mol_with_h, params)
        
        if success == -1:
            failure_info = {
                'smiles': smiles,
                'reason': 'Conformer generation failed (EmbedMolecule returned -1)',
                'stage': 'conformer_generation',
                'atom_count': atom_count
            }
            return None, failure_info
        
        # Energy minimization
        try:
            AllChem.UFFOptimizeMolecule(mol_with_h, maxIters=200)
        except Exception as e:
            # Optimization failure is not fatal, log but continue
            if logger:
                logger.warning(f"Energy minimization failed for {smiles[:50]}: {str(e)}")
        
        # Return without hydrogens for consistency
        mol_no_h = Chem.RemoveHs(mol_with_h)
        return mol_no_h, None
        
    except Exception as e:
        failure_info = {
            'smiles': smiles,
            'reason': f'Conformer generation exception: {str(e)}',
            'stage': 'conformer_generation',
            'atom_count': atom_count
        }
        return None, failure_info

def validate_and_process_dataset(
    input_file: str,
    output_file: str,
    max_atoms: int = 100,
    failure_rate_threshold: float = 0.10,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Validate and process a dataset with failure rate monitoring.
    
    This function processes molecules from a parquet file, validates SMILES,
    generates conformers, and halts if the failure rate exceeds the threshold.
    
    Args:
        input_file: Path to input parquet file
        output_file: Path to output parquet file
        max_atoms: Maximum allowed atoms per molecule
        failure_rate_threshold: Maximum acceptable failure rate (default 0.10 = 10%)
        logger: Optional logger instance
        
    Returns:
        True if processing completed successfully, False if halted due to failures
        
    Raises:
        RuntimeError: If failure rate exceeds threshold
    """
    import pandas as pd
    
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Starting validation and processing of {input_file}")
    logger.info(f"Max atoms threshold: {max_atoms}")
    logger.info(f"Failure rate threshold: {failure_rate_threshold:.1%}")
    
    # Load data
    try:
        df = pd.read_parquet(input_file)
    except Exception as e:
        raise RuntimeError(f"Failed to load input file: {str(e)}")
    
    logger.info(f"Loaded {len(df)} molecules from {input_file}")
    
    # Initialize statistics
    stats = ValidationStats()
    stats.total_molecules = len(df)
    
    # Process molecules
    valid_records = []
    failure_records = []
    
    for idx, row in df.iterrows():
        smiles = row.get('smiles', '')
        if not smiles:
            continue
        
        mol, failure_info = process_single_molecule_with_validation(
            smiles, max_atoms, logger
        )
        
        if mol is not None:
            stats.valid_smiles += 1
            stats.conformer_success += 1
            # Add molecule data to record
            record = row.to_dict()
            record['mol_obj'] = mol  # Store for downstream processing
            valid_records.append(record)
        else:
            if failure_info:
                stage = failure_info.get('stage', 'unknown')
                if stage == 'smiles_validation':
                    stats.invalid_smiles += 1
                elif stage == 'conformer_generation':
                    stats.conformer_failed += 1
                elif stage == 'atom_count_check':
                    stats.excluded_atoms += 1
                
                stats.failed_molecules.append(failure_info)
                failure_records.append(failure_info)
    
    # Calculate failure rate
    overall_failure_rate = stats.overall_failure_rate
    logger.info(f"Processing complete. Overall failure rate: {overall_failure_rate:.2%}")
    
    # Log summary
    stats.log_summary(logger)
    
    # Check failure rate threshold
    if overall_failure_rate > failure_rate_threshold:
        error_msg = (
            f"CRITICAL: Overall failure rate ({overall_failure_rate:.2%}) exceeds "
            f"threshold ({failure_rate_threshold:.1%}). Halting pipeline."
        )
        logger.error(error_msg)
        
        # Save failure report before halting
        if failure_records:
            failure_df = pd.DataFrame(failure_records)
            failure_report_path = str(Path(output_file).parent / "validation_failures.csv")
            failure_df.to_csv(failure_report_path, index=False)
            logger.info(f"Failure report saved to {failure_report_path}")
        
        raise RuntimeError(error_msg)
    
    # Save valid records
    if valid_records:
        # Create output dataframe
        output_df = pd.DataFrame(valid_records)
        
        # Remove mol_obj before saving (not serializable to parquet)
        # The mol_obj should be used in the next processing step
        if 'mol_obj' in output_df.columns:
            mol_objects = output_df.pop('mol_obj')
            output_df.to_parquet(output_file, index=False)
            # Return the mol_objects for further processing
            return True, mol_objects
        else:
            output_df.to_parquet(output_file, index=False)
            return True
    else:
        logger.warning("No valid molecules to save")
        return False

def main():
    """Main entry point for validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate and process molecular dataset')
    parser.add_argument('--input', type=str, required=True, help='Input parquet file')
    parser.add_argument('--output', type=str, required=True, help='Output parquet file')
    parser.add_argument('--max-atoms', type=int, default=100, help='Maximum atoms per molecule')
    parser.add_argument('--failure-threshold', type=float, default=0.10, help='Maximum failure rate')
    
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    
    try:
        success = validate_and_process_dataset(
            args.input,
            args.output,
            args.max_atoms,
            args.failure_threshold,
            logger
        )
        
        if success:
            logger.info("Validation and processing completed successfully")
            sys.exit(0)
        else:
            logger.warning("Validation completed but no valid molecules found")
            sys.exit(1)
            
    except RuntimeError as e:
        logger.error(f"Pipeline halted: {str(e)}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(3)

if __name__ == '__main__':
    main()
