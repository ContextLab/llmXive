"""
Export calculated topological descriptors to CSV with checksums.

This script reads the processed EAS reactions dataset, calculates descriptors
(or loads pre-calculated ones if already present), and writes a consolidated
CSV file to data/processed/descriptors.csv with an accompanying SHA-256 checksum.
"""
import os
import sys
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import get_config
from code.utils.logger import setup_logger, handle_exception
from code.descriptors import TopologicalDescriptorCalculator, calculate_descriptors_for_smiles
from code.utils.smiles_parser import SMILESParser

# Configure logging
logger = setup_logger(__name__, level=logging.INFO)

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_eas_reactions(input_path: Path) -> List[Dict[str, Any]]:
    """Load EAS reactions from the processed CSV file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    reactions = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            reactions.append(row)
    
    logger.info(f"Loaded {len(reactions)} EAS reactions from {input_path}")
    return reactions

def export_descriptors(
    input_path: Path,
    output_path: Path,
    checksum_path: Optional[Path] = None
) -> Path:
    """
    Calculate descriptors for all reactions and export to CSV.
    
    Args:
        input_path: Path to the EAS reactions CSV
        output_path: Path to write the descriptors CSV
        checksum_path: Optional path to write the checksum file
        
    Returns:
        Path to the output CSV file
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    reactions = load_eas_reactions(input_path)
    calculator = TopologicalDescriptorCalculator()
    parser = SMILESParser()
    
    output_data = []
    invalid_count = 0
    
    for i, reaction in enumerate(reactions):
        try:
            # Extract reactant SMILES (assuming column name 'reactant_smiles')
            reactant_smiles = reaction.get('reactant_smiles')
            if not reactant_smiles:
                logger.warning(f"Row {i}: Missing reactant_smiles, skipping")
                invalid_count += 1
                continue
            
            # Parse SMILES
            mol = parser.parse_smiles(reactant_smiles)
            if mol is None:
                logger.warning(f"Row {i}: Failed to parse SMILES '{reactant_smiles}', skipping")
                invalid_count += 1
                continue
            
            # Calculate descriptors
            descriptors = calculate_descriptors_for_smiles(reactant_smiles, calculator)
            
            if descriptors is None or descriptors.get('is_connected') == False:
                logger.warning(f"Row {i}: Invalid topology (disconnected), skipping")
                invalid_count += 1
                continue
            
            # Combine reaction data with descriptors
            row_data = {
                'reaction_id': reaction.get('reaction_id', f'reaction_{i}'),
                'reactant_smiles': reactant_smiles,
                'wiener_index': descriptors.get('wiener_index', None),
                'balaban_index': descriptors.get('balaban_index', None),
                'zagreb_index': descriptors.get('zagreb_index', None),
                'is_connected': descriptors.get('is_connected', True),
                'n_atoms': descriptors.get('n_atoms', None),
                'n_bonds': descriptors.get('n_bonds', None),
            }
            
            # Add any additional metadata from the reaction record
            for key, value in reaction.items():
                if key not in row_data and key not in ['reactant_smiles', 'reaction_id']:
                    row_data[key] = value
            
            output_data.append(row_data)
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(reactions)} reactions")
                
        except Exception as e:
            logger.error(f"Error processing row {i}: {str(e)}")
            handle_exception(e)
            invalid_count += 1
            continue
    
    if len(output_data) == 0:
        raise RuntimeError("No valid descriptors calculated. Check input data and parsing logic.")
    
    # Write to CSV
    fieldnames = [
        'reaction_id', 'reactant_smiles', 'wiener_index', 'balaban_index', 
        'zagreb_index', 'is_connected', 'n_atoms', 'n_bonds'
    ]
    # Add any additional fields found in the data
    for row in output_data:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)
    
    logger.info(f"Successfully wrote {len(output_data)} descriptor records to {output_path}")
    logger.info(f"Skipped {invalid_count} invalid records")
    
    # Generate checksum
    if checksum_path is None:
        checksum_path = output_path.with_suffix('.sha256')
    
    checksum = calculate_file_checksum(output_path)
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {output_path.name}\n")
    
    logger.info(f"Generated checksum: {checksum}")
    logger.info(f"Checksum file written to: {checksum_path}")
    
    return output_path

def main():
    """Main entry point for the descriptor export script."""
    config = get_config()
    
    input_path = Path(config.get('paths', {}).get('eas_reactions', 'data/processed/eas_reactions.csv'))
    output_path = Path(config.get('paths', {}).get('descriptors', 'data/processed/descriptors.csv'))
    checksum_path = Path(config.get('paths', {}).get('descriptors_checksum', 'data/processed/descriptors.csv.sha256'))
    
    logger.info(f"Starting descriptor export pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        export_descriptors(input_path, output_path, checksum_path)
        logger.info("Descriptor export completed successfully")
    except Exception as e:
        logger.error(f"Descriptor export failed: {str(e)}")
        handle_exception(e)
        sys.exit(1)

if __name__ == "__main__":
    main()