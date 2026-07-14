"""
Molecular descriptor calculation module using RDKit.

Calculates molecular weight, polar surface area, polarizability,
H-bond counts, van der Waals volume, and kinetic diameter.
"""
import logging
from typing import Dict, Any, Optional, List, Union

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdDetermineBonds
from rdkit import RDLogger

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

logger = logging.getLogger(__name__)


def calculate_descriptors(smiles: str) -> Dict[str, float]:
    """
    Calculate a comprehensive set of molecular descriptors for a given SMILES string.

    This function computes:
    - Molecular Weight (MW)
    - Polar Surface Area (TPSA)
    - Polarizability (approximated via molar refractivity)
    - H-bond Donor Count
    - H-bond Acceptor Count
    - van der Waals Volume (approximated via MolVolume)
    - Kinetic Diameter (estimated via critical volume correlation)

    Args:
        smiles (str): The SMILES string representing the molecule.

    Returns:
        Dict[str, float]: A dictionary of calculated descriptors.
                        Returns a dict with NaN values if parsing fails.
    """
    default_result = {
        "molecular_weight": np.nan,
        "polar_surface_area": np.nan,
        "polarizability": np.nan,
        "h_bond_donors": np.nan,
        "h_bond_acceptors": np.nan,
        "vdw_volume": np.nan,
        "kinetic_diameter": np.nan
    }

    if not smiles or not isinstance(smiles, str):
        logger.warning(f"Invalid SMILES input: {smiles}")
        return default_result

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES: {smiles}")
            return default_result

        # Ensure hydrogens are added for accurate volume/diameter calculations
        mol = Chem.AddHs(mol)

        # 1. Molecular Weight
        mw = Descriptors.MolWt(mol)

        # 2. Polar Surface Area (TPSA)
        tpsa = Descriptors.TPSA(mol)

        # 3. Polarizability (approximated via Molar Refractivity)
        # RDKit's CalcMolMR returns molar refractivity.
        # Polarizability (alpha) in Angstrom^3 is roughly MR / 2.267 (Clausius-Mossotti)
        # However, in QSAR contexts, MR is often used directly as a proxy for polarizability/volume.
        # We will calculate MR and store it as 'polarizability' proxy as per common QSAR practice
        # when explicit polarizability tensors are not available.
        mr = rdMolDescriptors.CalcMolMR(mol)
        
        # 4. H-Bond Counts
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)

        # 5. Van der Waals Volume
        # rdMolDescriptors.CalcMolVolume returns the van der Waals volume in Angstrom^3
        vdw_vol = rdMolDescriptors.CalcMolVolume(mol)

        # 6. Kinetic Diameter
        # Kinetic diameter is not a direct RDKit descriptor.
        # It is often estimated from the critical volume or molecular volume.
        # A common approximation for small molecules: d_kinetic ~ (6 * V_mol / pi)^(1/3) * 0.95
        # where V_mol is the molecular volume.
        # We use the calculated vdw_vol as V_mol.
        # Note: This is an estimation. Real kinetic diameter depends on orientation.
        if vdw_vol > 0:
            # Calculate effective spherical diameter from volume
            # V = 4/3 * pi * r^3  => r = (3V / 4pi)^(1/3)
            # d = 2r
            effective_radius = (3 * vdw_vol / (4 * np.pi)) ** (1/3)
            effective_diameter = 2 * effective_radius
            
            # Apply a scaling factor often used to convert vdW volume to kinetic diameter
            # The factor 0.95 is empirical for many organic molecules to account for shape
            # and the difference between static vdW surface and dynamic collision cross-section.
            kinetic_diam = effective_diameter * 0.95
        else:
            kinetic_diam = np.nan

        return {
            "molecular_weight": float(mw),
            "polar_surface_area": float(tpsa),
            "polarizability": float(mr),
            "h_bond_donors": float(hbd),
            "h_bond_acceptors": float(hba),
            "vdw_volume": float(vdw_vol),
            "kinetic_diameter": float(kinetic_diam)
        }

    except Exception as e:
        logger.error(f"Error calculating descriptors for {smiles}: {e}")
        return default_result


def calculate_descriptors_batch(df: pd.DataFrame, 
                                smiles_col: str = "smiles",
                                output_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculate descriptors for a batch of molecules in a DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame containing SMILES strings.
        smiles_col (str): Name of the column containing SMILES strings.
        output_cols (Optional[List[str]]): Specific columns to calculate. 
                                           If None, calculates all defined descriptors.

    Returns:
        pd.DataFrame: The original DataFrame with new descriptor columns appended.
    """
    if output_cols is None:
        output_cols = [
            "molecular_weight", 
            "polar_surface_area", 
            "polarizability", 
            "h_bond_donors", 
            "h_bond_acceptors", 
            "vdw_volume", 
            "kinetic_diameter"
        ]

    # Initialize new columns with NaN
    for col in output_cols:
        df[col] = np.nan

    # Process row by row
    results = []
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        desc = calculate_descriptors(smiles)
        
        # Filter results to only requested columns
        row_results = {col: desc.get(col, np.nan) for col in output_cols}
        results.append(row_results)
        
        if idx % 100 == 0:
            logger.info(f"Processed {idx}/{len(df)} molecules")

    # Create a DataFrame from results and concat
    desc_df = pd.DataFrame(results, index=df.index)
    df = pd.concat([df, desc_df], axis=1)

    return df


def main():
    """
    Entry point for testing the descriptor calculation.
    Reads a sample CSV (if exists) or runs a demo.
    """
    logger.info("Running descriptor calculation module self-test.")
    
    # Demo molecules
    demo_smiles = [
        "C",          # Methane
        "CCO",        # Ethanol
        "c1ccccc1",   # Benzene
        "CC(=O)O",    # Acetic Acid
        "N#C"         # Cyanide (invalid for some, but valid SMILES)
    ]
    
    demo_df = pd.DataFrame({"smiles": demo_smiles})
    
    logger.info(f"Calculating descriptors for {len(demo_df)} demo molecules...")
    result_df = calculate_descriptors_batch(demo_df)
    
    print(result_df[["smiles", "molecular_weight", "kinetic_diameter", "polarizability"]].to_string())
    
    logger.info("Descriptor calculation module test completed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()