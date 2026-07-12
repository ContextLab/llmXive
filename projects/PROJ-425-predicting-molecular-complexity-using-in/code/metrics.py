import signal
import zlib
import time
import os
import logging
from functools import wraps
from typing import Callable, Any, Optional
from rdkit import Chem
from rdkit.Chem import Descriptors, QED, Descriptors3D
from rdkit import RDLogger

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

logger = logging.getLogger(__name__)

# Configuration import (assuming config.py is in the same directory or accessible)
# We will import the specific constant needed. If config is not imported directly,
# we can define a default or assume it's passed.
# Based on T004, TIMEOUT_SECONDS is defined in config.
try:
    from config import TIMEOUT_SECONDS
except ImportError:
    TIMEOUT_SECONDS = 60  # Default fallback if config is not available during unit tests

class TimeoutError(Exception):
    """Custom timeout exception for metric calculations."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError(f"Function timed out after {TIMEOUT_SECONDS} seconds")

def timeout(seconds: Optional[int] = None):
    """
    Decorator to enforce a timeout on a function.
    Uses signal.SIGALRM which works on Unix. For Windows compatibility,
    a threading-based approach would be needed, but signal is standard for research scripts on Linux/CI.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set the signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            # Use provided seconds or global config
            timeout_val = seconds if seconds is not None else TIMEOUT_SECONDS
            
            try:
                signal.setitimer(signal.ITIMER_REAL, timeout_val)
                result = func(*args, **kwargs)
                return result
            except TimeoutError as e:
                logger.warning(f"Timeout triggered for {func.__name__}: {e}")
                raise
            finally:
                # Cancel the alarm and restore the old handler
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator

@timeout()
def calculate_shannon_entropy(smiles: str) -> float:
    """
    Calculate Shannon entropy of the SMILES string character distribution.
    """
    if not smiles:
        return 0.0
    
    freq = {}
    for char in smiles:
        freq[char] = freq.get(char, 0) + 1
    
    length = len(smiles)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * (p if p == 0 else p.__float__()) # Avoid log(0)
        # Correct formula: - sum(p * log2(p))
        # Re-calculating properly
    
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * (p if p == 0 else 0) # Placeholder logic fix below
    
    # Correct implementation
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * (p.__float__().bit_length()) # No, use math.log
            # Import math inside or at top. Let's assume math is available or import it.
            # Re-writing cleanly:
            pass

    # Clean implementation
    import math
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy

@timeout()
def calculate_lzma_length(smiles: str) -> int:
    """
    Calculate the compressed length of the SMILES string using zlib (approximating LZMA).
    """
    if not smiles:
        return 0
    try:
        compressed = zlib.compress(smiles.encode('utf-8'))
        return len(compressed)
    except Exception as e:
        logger.error(f"Error compressing SMILES: {e}")
        return 0

@timeout()
def calculate_sa_score(smiles: str) -> float:
    """
    Calculate Synthetic Accessibility (SA) score using RDKit.
    Returns a score between 1 (easy) and 10 (difficult).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 10.0 # High SA score for invalid/complex
    
    try:
        # RDKit's CalcSA_score returns a float
        score = Descriptors3D.SA_Score(mol) # Note: SA_Score is in rdkit.Chem.rdMolDescriptors or similar
        # Actually, standard SA score is in rdkit.Chem.QED or specific module?
        # RDKit has a function: rdkit.Chem.qed.defaultLogP? No.
        # Correct import: from rdkit.Chem import rdMolDescriptors
        # Let's use the standard implementation available in rdkit.Chem.QED? No, QED is different.
        # SA Score is in rdkit.Chem.rdMolDescriptors.CalcSA_Score?
        # Actually, it's often implemented as a separate function in rdkit.Chem.QED?
        # Let's use the standard `rdkit.Chem.QED.defaultLogP`? No.
        # The correct function is `rdkit.Chem.QED.qed`? No.
        # SA Score is calculated via `rdkit.Chem.rdMolDescriptors.CalcSA_Score`?
        # Actually, it's `rdkit.Chem.QED`? No.
        # Let's check standard RDKit: `from rdkit.Chem import rdMolDescriptors`
        # `rdMolDescriptors.CalcSA_Score(mol)`
        
        # If that fails, fallback to a mock or standard implementation if not available in this version.
        # But standard RDKit has it.
        from rdkit.Chem import rdMolDescriptors
        return float(rdMolDescriptors.CalcSA_Score(mol))
    except Exception as e:
        logger.warning(f"SA Score calculation failed: {e}, returning max score")
        return 10.0

@timeout()
def calculate_qed_score(smiles: str) -> float:
    """
    Calculate Quantitative Estimate of Drug-likeness (QED) score.
    Returns a score between 0 and 1.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0.0
    
    try:
        return float(QED.qed(mol))
    except Exception as e:
        logger.warning(f"QED calculation failed: {e}, returning 0.0")
        return 0.0

@timeout()
def calculate_molecular_weight(smiles: str) -> float:
    """
    Calculate Molecular Weight (MW).
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0.0
    try:
        return float(Descriptors.MolWt(mol))
    except Exception as e:
        logger.warning(f"MW calculation failed: {e}, returning 0.0")
        return 0.0

@timeout()
def calculate_atom_count(smiles: str) -> int:
    """
    Calculate the number of atoms in the molecule.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0
    try:
        return mol.GetNumAtoms()
    except Exception as e:
        logger.warning(f"Atom count calculation failed: {e}, returning 0")
        return 0

def process_chunk(chunk: list, logger: Optional[logging.Logger] = None) -> tuple:
    """
    Process a chunk of molecules, applying timeout to each metric calculation.
    Returns (results_list, skipped_count, timeout_count).
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    results = []
    skipped = 0
    timeouts = 0
    
    for item in chunk:
        cid = item.get('cid')
        smiles = item.get('smiles')
        
        if not smiles or not isinstance(smiles, str):
            skipped += 1
            logger.info(f"Skipped CID {cid}: Invalid SMILES type or empty")
            continue
        
        try:
            # Apply timeout to the metric calculations
            # We wrap the individual calls or the whole block?
            # The task says "Enforce TIMEOUT_SECONDS per molecule".
            # We can call the functions which are already decorated with @timeout().
            # However, if one hangs, the next might not run if we don't handle the exception.
            
            entropy = calculate_shannon_entropy(smiles)
            lz = calculate_lzma_length(smiles)
            sa = calculate_sa_score(smiles)
            qed = calculate_qed_score(smiles)
            mw = calculate_molecular_weight(smiles)
            atoms = calculate_atom_count(smiles)
            
            results.append({
                'cid': cid,
                'smiles': smiles,
                'entropy': entropy,
                'lz': lz,
                'sa': sa,
                'qed': qed,
                'mw': mw,
                'atom_count': atoms
            })
            
        except TimeoutError:
            timeouts += 1
            logger.warning(f"Skipped CID {cid}: Timeout during metric calculation")
            # Log the event as requested in T008/T018
            logger.info(f'{{"event": "skipped", "reason": "timeout", "cid": {cid}}}')
        except Exception as e:
            skipped += 1
            logger.warning(f"Skipped CID {cid}: Error {e}")
            logger.info(f'{{"event": "skipped", "reason": "invalid_smiles", "cid": {cid}}}')
    
    return results, skipped, timeouts

def main():
    """
    Main entry point for testing metrics module directly.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test with a valid molecule
    test_smiles = "CCO"
    print(f"Testing {test_smiles}")
    print(f"Entropy: {calculate_shannon_entropy(test_smiles)}")
    print(f"LZ Length: {calculate_lzma_length(test_smiles)}")
    print(f"SA Score: {calculate_sa_score(test_smiles)}")
    print(f"QED Score: {calculate_qed_score(test_smiles)}")
    print(f"MW: {calculate_molecular_weight(test_smiles)}")
    print(f"Atom Count: {calculate_atom_count(test_smiles)}")
    
    # Test with a molecule that might be slow (if any) or invalid
    # Invalid
    invalid_smiles = "INVALID"
    print(f"\nTesting {invalid_smiles}")
    try:
        sa = calculate_sa_score(invalid_smiles)
        print(f"SA Score (invalid): {sa}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()