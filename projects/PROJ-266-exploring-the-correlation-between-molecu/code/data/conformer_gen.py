import logging
import sys
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# RDKit imports
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
    from rdkit import RDLogger
    from rdkit.Chem import rdMolTransforms
except ImportError:
    raise ImportError("RDKit is required for this task. Please install it via 'pip install rdkit'")

# Project imports
from utils.logging import get_logger, setup_logging_for_script
from utils.config import get_project_root

# Disable RDKit warnings
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

def load_filtered_data() -> pd.DataFrame:
    """
    Load the filtered data from the previous step (T010).
    
    Returns:
        pd.DataFrame: The filtered dataset containing 'smiles' and 'logPapp' columns.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "filtered_data.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Please ensure T010 (preprocessing) has been completed successfully.")
    
    logger.info(f"Loading filtered data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['smiles', 'logPapp']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    # Filter for valid SMILES and logPapp
    df = df[df['smiles'].notna() & (df['smiles'].str.strip() != '')]
    df = df[df['logPapp'].notna()]
    
    logger.info(f"Loaded {len(df)} valid records for conformer generation.")
    return df

def generate_conformers(smiles_list: List[str], 
                        num_conformers: int = 50, 
                        energy_window: float = 10.0) -> Tuple[List[Chem.Mol], List[int]]:
    """
    Generate 3D conformer ensembles for a list of SMILES strings.
    
    Implements FR-003: Conformer Generation
    
    Args:
        smiles_list: List of SMILES strings.
        num_conformers: Number of conformers to generate per molecule (default: 50).
        energy_window: Maximum energy window in kcal/mol to keep conformers (default: 10.0).
    
    Returns:
        Tuple containing:
            - List of RDKit Mol objects with conformers attached.
            - List of conformer IDs for the lowest energy conformer per molecule.
    """
    valid_mols = []
    lowest_energy_ids = []
    
    logger.info(f"Generating conformers for {len(smiles_list)} molecules...")
    
    for i, smiles in enumerate(smiles_list):
        if i % 50 == 0:
            logger.info(f"Processing molecule {i}/{len(smiles_list)}")
        
        # Create molecule
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Invalid SMILES at index {i}: {smiles}")
            continue
        
        # Add hydrogens
        mol = Chem.AddHs(mol)
        
        # Generate conformers
        params = Chem.EmbedMultipleConfsParameters()
        params.numConformers = num_conformers
        params.pruneRmsThresh = 0.5
        params.useRandomCoords = True
        params.maxAttempts = 500
        
        try:
            conf_ids = Chem.EmbedMultipleConfs(mol, params)
            if not conf_ids:
                logger.warning(f"Failed to generate conformers for molecule {i}")
                continue
            
            # Optimize geometry
            # Using MMFF94 if available, otherwise UFF
            try:
                ff = AllChem.MMFFGetMoleculeForceField(mol, AllChem.MMFFGetMoleculeProperties(mol))
                if ff:
                    ff.Minimize(maxIts=200)
                else:
                    # Fallback to UFF
                    ff = AllChem.UFFGetMoleculeForceField(mol)
                    if ff:
                        ff.Minimize(maxIts=200)
            except Exception as e:
                logger.warning(f"Energy minimization failed for molecule {i}: {e}")
            
            # Calculate energies and filter by window
            energies = []
            for conf_id in conf_ids:
                try:
                    ff = AllChem.MMFFGetMoleculeForceField(mol, AllChem.MMFFGetMoleculeProperties(mol))
                    if ff:
                        energies.append(ff.CalcEnergy())
                    else:
                        ff = AllChem.UFFGetMoleculeForceField(mol)
                        energies.append(ff.CalcEnergy())
                except Exception:
                    energies.append(float('inf'))
            
            if not energies:
                continue
            
            min_energy = min(energies)
            filtered_conf_ids = [cid for cid, ene in zip(conf_ids, energies) 
                                 if ene <= min_energy + energy_window]
            
            # Remove conformers outside the window
            all_conf_ids = list(mol.GetConformerIds())
            for cid in all_conf_ids:
                if cid not in filtered_conf_ids:
                    mol.RemoveConformer(cid)
            
            # Record the lowest energy conformer ID (the first one after filtering)
            if filtered_conf_ids:
                lowest_energy_ids.append(filtered_conf_ids[0])
                valid_mols.append(mol)
            else:
                logger.warning(f"No conformers within energy window for molecule {i}")
                
        except Exception as e:
            logger.warning(f"Error generating conformers for molecule {i}: {e}")
            continue
    
    logger.info(f"Successfully generated conformers for {len(valid_mols)} molecules.")
    return valid_mols, lowest_energy_ids

def save_conformers(mols: List[Chem.Mol], 
                    lowest_energy_ids: List[int], 
                    smiles_list: List[str]) -> None:
    """
    Save the generated conformer ensembles to a pickle file.
    
    Args:
        mols: List of RDKit Mol objects with conformers.
        lowest_energy_ids: List of conformer IDs for the lowest energy conformer.
        smiles_list: List of SMILES strings corresponding to the molecules.
    """
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "conformers.pkl"
    
    # Prepare data structure
    data = {
        'molecules': mols,
        'lowest_energy_conformer_id': lowest_energy_ids,
        'smiles': smiles_list,
        'conformer_count': [mol.GetNumConformers() for mol in mols]
    }
    
    logger.info(f"Saving conformers to {output_path}")
    with open(output_path, 'wb') as f:
        pickle.dump(data, f)
    
    logger.info(f"Saved {len(mols)} molecules with conformers.")

def main():
    """Main entry point for the conformer generation script."""
    # Setup logging
    setup_logging_for_script(__name__)
    
    try:
        # Load filtered data
        df = load_filtered_data()
        
        # Extract SMILES
        smiles_list = df['smiles'].tolist()
        
        # Generate conformers
        mols, lowest_energy_ids = generate_conformers(smiles_list)
        
        # Save results
        if mols:
            save_conformers(mols, lowest_energy_ids, smiles_list)
            
            # Invoke checksum utility
            from utils.checksum import scan_and_register_data_files
            scan_and_register_data_files()
            logger.info("Checksum utility invoked successfully.")
        else:
            logger.error("No molecules with conformers were generated. Exiting.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Conformer generation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()