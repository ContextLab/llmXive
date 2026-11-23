import os
import sys
import json
import hashlib
import logging
import pandas as pd

def setup_script_logging():
    """Sets up logging for the generation script."""
    # Basic setup for this script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def generate_reference_substructures(logger: logging.Logger) -> pd.DataFrame:
    """
    Generates a curated list of known reactive substructures based on embedded SMILES rules.
    This is a deterministic generation to ensure reproducibility (FR-008).
    
    Returns:
        pd.DataFrame: A dataframe containing the generated substructures.
    """
    logger.info("Generating reference substructures...")
    
    # Embedded rules for reactive substructures (SMILES)
    # These are standard, well-known reactive motifs
    substructures = [
        {
            "name": "Benzene",
            "smiles": "c1ccccc1",
            "description": "Aromatic ring, common scaffold.",
            "source": "Embedded Rule Set v1"
        },
        {
            "name": "Ethylene",
            "smiles": "C=C",
            "description": "Alkene double bond, reactive site.",
            "source": "Embedded Rule Set v1"
        },
        {
            "name": "Acetylene",
            "smiles": "C#C",
            "description": "Alkyne triple bond, highly reactive.",
            "source": "Embedded Rule Set v1"
        },
        {
            "name": "Carbonyl",
            "smiles": "C=O",
            "description": "Carbonyl group, electrophilic center.",
            "source": "Embedded Rule Set v1"
        },
        {
            "name": "Hydroxyl",
            "smiles": "O",
            "description": "Hydroxyl group, nucleophilic.",
            "source": "Embedded Rule Set v1"
        },
        {
            "name": "Amine Primary",
            "smiles": "N",
            "description": "Primary amine, nucleophilic.",
            "source": "Embedded Rule Set v1"
        },
        {
            "name": "Nitro",
            "smiles": "[N+](=O)[O-]",
            "description": "Nitro group, electron withdrawing.",
            "source": "Embedded Rule Set v1"
        },
        {
            "name": "Cyano",
            "smiles": "C#N",
            "description": "Cyano group, electron withdrawing.",
            "source": "Embedded Rule Set v1"
        },
        {
            "name": "Epoxide",
            "smiles": "C1OC1",
            "description": "Epoxide ring, strained and reactive.",
            "source": "Embedded Rule Set v1"
        },
        {
            "name": "Aldehyde",
            "smiles": "C=O",
            "description": "Aldehyde group (simplified SMILES).",
            "source": "Embedded Rule Set v1"
        }
    ]
    
    df = pd.DataFrame(substructures)
    logger.info(f"Generated {len(df)} substructures.")
    return df

def validate_against_checksums(df: pd.DataFrame, checksums_path: str) -> bool:
    """
    Validates the generated dataframe by calculating its hash and comparing to checksums.json.
    This is a placeholder for the actual checksum validation logic which usually happens
    after saving to disk.
    """
    # In a real flow, we would save to temp, calc hash, compare.
    # Here we just return True if the dataframe is not empty.
    if df.empty:
        return False
    return True

def main():
    """Main entry point for the generation script."""
    logger = setup_script_logging()
    
    # Define paths relative to project root
    # Assuming the script is run from the project root or code/data
    # We use a standard structure: data/raw/reference_substructures_raw.csv
    raw_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    
    output_path = os.path.join(raw_dir, 'reference_substructures_raw.csv')
    checksums_path = os.path.join(raw_dir, 'checksums.json')
    
    try:
        df = generate_reference_substructures(logger)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved reference substructures to {output_path}")
        
        # Calculate hash for the generated file to update checksums.json
        # This logic is usually in a separate verification step, but we do it here for completeness
        # of the generation task if needed.
        # However, T009b handles the verification against the manifest.
        # We just ensure the file is created.
        
    except Exception as e:
        logger.error(f"Failed to generate reference substructures: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
