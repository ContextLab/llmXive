import os
import re
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from pymatgen.core import Structure
from cif_parsing import parse_cif_with_pymatgen
from error_handling import handle_corrupt_cif, log_processing_statistics
from config import get_data_dir, get_base_dir
from utils import fix_seed, setup_logging

logger = logging.getLogger(__name__)

def parse_cif_metadata(cif_path: str) -> Dict[str, Any]:
    """Parse metadata from a CIF file using pymatgen."""
    try:
        structure = parse_cif_with_pymatgen(cif_path)
        if structure is None:
            return {}
        
        metadata = {
            "unit_cell_volume": structure.lattice.volume,
            "n_atoms": len(structure),
            "lattice_system": _determine_lattice_system(structure.lattice),
            "temperature_K": _extract_temperature(cif_path),
            "has_solvent": _check_solvent(cif_path)
        }
        return metadata
    except Exception as e:
        logger.error(f"Failed to parse metadata for {cif_path}: {e}")
        raise

def _determine_lattice_system(lattice) -> str:
    """Determine lattice system from pymatgen Lattice object."""
    try:
        # Use symmetry analysis if available, otherwise estimate from angles
        if hasattr(lattice, 'system'):
            return str(lattice.system)
        
        a, b, c = lattice.abc
        alpha, beta, gamma = lattice.angles
        
        # Simplified lattice system determination
        if np.allclose([alpha, beta, gamma], 90) and np.allclose([a, b, c], a):
            return "cubic"
        elif np.allclose([alpha, beta, gamma], 90) and np.allclose([a, b], a):
            return "tetragonal"
        elif np.allclose([alpha, beta, gamma], 90):
            return "orthorhombic"
        elif np.allclose([alpha, gamma], 90) and np.allclose(beta, 120) and np.allclose(a, b):
            return "hexagonal"
        elif np.allclose(alpha, gamma, 90) and np.allclose(a, b):
            return "monoclinic"
        else:
            return "triclinic"
    except Exception:
        return "unknown"

def _extract_temperature(cif_path: str) -> float:
    """Extract temperature from CIF file."""
    try:
        with open(cif_path, 'r') as f:
            content = f.read()
        
        # Try common temperature keys
        patterns = [
            r'_exptl_temperature\s+([0-9.]+)',
            r'_cell_measurement_reflns_temperature\s+([0-9.]+)',
            r'_diffrn_ambient_temperature\s+([0-9.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        return 298.0  # Default to room temperature
    except Exception:
        return 298.0

def _check_solvent(cif_path: str) -> bool:
    """Check if CIF contains solvent molecules."""
    try:
        with open(cif_path, 'r') as f:
            content = f.read()
        
        # Check for common solvent patterns in formula
        solvent_patterns = [
            r'_chemical_formula_sum\s+.*[Hh][Oo]',  # Water
            r'_chemical_formula_sum\s+.*[Cc][Hh][3]',  # Methanol
            r'_chemical_formula_sum\s+.*[Ee][Tt][Hh]',  # Ethanol
        ]
        
        for pattern in solvent_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    except Exception:
        return False

def extract_atom_count_from_formula(formula: str) -> int:
    """Extract total atom count from chemical formula string."""
    if not formula:
        return 0
    
    # Simple regex to count atoms (basic implementation)
    # This is a simplified version; a full implementation would use a chemistry library
    elements = re.findall(r'([A-Z][a-z]?)(\d*)', formula.replace(' ', ''))
    total = 0
    for elem, count in elements:
        total += int(count) if count else 1
    return total

def generate_smiles_from_cif(cif_path: str) -> Tuple[Optional[str], str]:
    """
    Generate SMILES from CIF file.
    
    Returns:
        Tuple of (smiles, source) where source is 'extracted' or 'generated'
        
    Constraints:
        - Only uses SMILES if explicitly present in CIF (_chemical_structure_SMILES)
        - Raises error if SMILES is missing (FR-002: no 3D connectivity inference)
    """
    try:
        with open(cif_path, 'r') as f:
            content = f.read()
        
        # Check for explicit SMILES in CIF
        smiles_match = re.search(r'_chemical_structure_SMILES\s+["\']?([^"\'\n]+)["\']?', content, re.IGNORECASE)
        if smiles_match:
            smiles = smiles_match.group(1).strip()
            # Validate SMILES
            mol = Chem.MolFromSmiles(smiles)
            if mol is not None:
                return smiles, "extracted"
        
        # If no explicit SMILES, raise error as per FR-002
        raise ValueError("No explicit SMILES found in CIF file. SMILES generation from 3D coordinates is not permitted.")
        
    except Exception as e:
        logger.error(f"Failed to generate SMILES for {cif_path}: {e}")
        raise

def record_confounders(cif_path: str) -> Dict[str, Any]:
    """Record confounder variables from CIF file."""
    try:
        metadata = parse_cif_metadata(cif_path)
        return {
            "lattice_system": metadata.get("lattice_system", "unknown"),
            "temperature_K": metadata.get("temperature_K", 298.0),
            "has_solvent": metadata.get("has_solvent", False)
        }
    except Exception as e:
        logger.error(f"Failed to record confounders for {cif_path}: {e}")
        return {
            "lattice_system": "unknown",
            "temperature_K": 298.0,
            "has_solvent": False
        }

def flag_source(smiles_source: str) -> str:
    """Flag the source of the SMILES string."""
    return smiles_source

def process_single_cif(cif_path: str) -> Optional[Dict[str, Any]]:
    """Process a single CIF file and extract all required data."""
    try:
        # Generate SMILES
        smiles, smiles_source = generate_smiles_from_cif(cif_path)
        
        # Extract metadata
        metadata = parse_cif_metadata(cif_path)
        
        # Extract confounders
        confounders = record_confounders(cif_path)
        
        # Extract COD ID from filename
        cod_id = os.path.splitext(os.path.basename(cif_path))[0]
        
        result = {
            "cod_id": cod_id,
            "smiles": smiles,
            "smiles_source": smiles_source,
            "unit_cell_volume": metadata.get("unit_cell_volume", 0.0),
            "n_atoms": metadata.get("n_atoms", 0),
            "lattice_system": confounders["lattice_system"],
            "temperature_K": confounders["temperature_K"],
            "has_solvent": confounders["has_solvent"]
        }
        
        return result
    except Exception as e:
        logger.error(f"Failed to process {cif_path}: {e}")
        return None

def main():
    """Main function to parse all CIF files and generate dataset_intermediate.csv."""
    setup_logging()
    fix_seed(42)
    
    start_time = time.time()
    
    data_dir = get_data_dir()
    raw_cif_dir = os.path.join(data_dir, "raw_cif")
    output_path = os.path.join(data_dir, "dataset_intermediate.csv")
    
    # Get list of CIF files
    cif_files = [f for f in os.listdir(raw_cif_dir) if f.endswith('.cif')]
    logger.info(f"Found {len(cif_files)} CIF files to process.")
    
    results = []
    success_count = 0
    failure_count = 0
    
    for cif_file in cif_files:
        cif_path = os.path.join(raw_cif_dir, cif_file)
        try:
            result = process_single_cif(cif_path)
            if result:
                results.append(result)
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logger.error(f"Error processing {cif_file}: {e}")
            failure_count += 1
    
    # Create DataFrame
    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(df)} records to {output_path}")
    else:
        logger.warning("No records processed successfully.")
        # Create empty DataFrame with correct columns
        df = pd.DataFrame(columns=[
            "cod_id", "smiles", "smiles_source", "unit_cell_volume", 
            "n_atoms", "lattice_system", "temperature_K", "has_solvent"
        ])
        df.to_csv(output_path, index=False)
    
    end_time = time.time()
    
    # Log statistics
    log_processing_statistics(success_count, failure_count, len(cif_files), start_time, end_time)
    
    logger.info("CIF parsing completed.")

if __name__ == "__main__":
    main()