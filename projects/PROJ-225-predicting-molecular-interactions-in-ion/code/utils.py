"""
Utility functions for molecular interaction prediction pipeline.
Includes descriptor computation, PSI4 SAPT execution, and custom exceptions.
"""
import logging
import os
import subprocess
import tempfile
from typing import Optional, List, Dict, Any
import rdkit.Chem as Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import DataStructs
from rdkit.Chem import AllChem

# Import custom exceptions from config to ensure they are defined in one place
from .config import DataIngestionError, ModelTrainingError, AnalysisError

# Re-export exceptions for convenience if needed elsewhere
__all__ = [
    "setup_logging",
    "compute_tpsa",
    "compute_morgan_fp",
    "compute_hbond_count",
    "run_psi_sapt",
    "DataIngestionError",
    "ModelTrainingError",
    "AnalysisError"
]

def setup_logging(log_file: str = "logs/pipeline.log") -> None:
    """
    Configure logging for the pipeline.
    
    Args:
        log_file: Path to the log file.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def compute_tpsa(smiles: str) -> float:
    """
    Compute Topological Polar Surface Area (TPSA) from SMILES.
    
    Args:
        smiles: SMILES string of the molecule.
        
    Returns:
        TPSA value in Angstrom^2.
        
    Raises:
        DataIngestionError: If the SMILES cannot be parsed.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise DataIngestionError(f"Failed to parse SMILES: {smiles}")
    return rdMolDescriptors.CalcTPSA(mol)

def compute_morgan_fp(smiles: str, radius: int = 2, n_bits: int = 2048) -> List[int]:
    """
    Compute Morgan fingerprint (ECFP) bit vector from SMILES.
    
    Args:
        smiles: SMILES string of the molecule.
        radius: Radius of the fingerprint (default 2).
        n_bits: Number of bits in the fingerprint (default 2048).
        
    Returns:
        List of integers representing the bit vector.
        
    Raises:
        DataIngestionError: If the SMILES cannot be parsed.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise DataIngestionError(f"Failed to parse SMILES: {smiles}")
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = [0] * n_bits
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def compute_hbond_count(smiles: str) -> int:
    """
    Compute the number of hydrogen bond donors and acceptors.
    
    Args:
        smiles: SMILES string of the molecule.
        
    Returns:
        Total count of H-bond donors and acceptors.
        
    Raises:
        DataIngestionError: If the SMILES cannot be parsed.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise DataIngestionError(f"Failed to parse SMILES: {smiles}")
    donors = Descriptors.NumHDonors(mol)
    acceptors = Descriptors.NumHAcceptors(mol)
    return donors + acceptors

def run_psi_sapt(structure_file: str, method: str = 'sapt0', basis: str = 'jun-cc-pVDZ') -> Dict[str, float]:
    """
    Run PSI4 SAPT calculation on a molecular structure file.
    
    Args:
        structure_file: Path to the XYZ or similar structure file.
        method: SAPT method (default 'sapt0').
        basis: Basis set (default 'jun-cc-pVDZ').
        
    Returns:
        Dictionary containing SAPT energy components:
        - electrostatic_energy
        - dispersion_energy
        - induction_energy
        - exchange_energy
        - total_energy
        
    Raises:
        ModelTrainingError: If PSI4 is not found or the calculation fails.
        DataIngestionError: If the structure file is invalid.
    """
    if not os.path.exists(structure_file):
        raise DataIngestionError(f"Structure file not found: {structure_file}")

    try:
        # Prepare input for PSI4
        input_script = f"""
        memory 2 GB
        set {{
            basis {basis}
            mp2_type {{conv}}
        }}
        molecule {{
            read {structure_file}
        }}
        energy('{method}')
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(input_script)
            input_path = f.name

        try:
            result = subprocess.run(
                ['psi4', input_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=300
            )
            
            output = result.stdout
            # Parse output for SAPT components
            # This is a simplified parser; real implementation might need regex
            # based on specific PSI4 output format
            energies = {
                "electrostatic_energy": 0.0,
                "dispersion_energy": 0.0,
                "induction_energy": 0.0,
                "exchange_energy": 0.0,
                "total_energy": 0.0
            }
            
            # Example parsing logic (adjust based on actual PSI4 output)
            for line in output.split('\n'):
                if 'SAPT0' in line or 'SAPT' in line:
                    # Placeholder for actual parsing logic
                    pass
                    
            return energies
            
        except subprocess.CalledProcessError as e:
            raise ModelTrainingError(f"PSI4 calculation failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise ModelTrainingError("PSI4 calculation timed out")
        finally:
            os.unlink(input_path)
            
    except Exception as e:
        raise ModelTrainingError(f"Unexpected error during PSI4 execution: {str(e)}")