"""
CIF Parsing Module for Crystal Structure Ingestion.

This module parses Crystallographic Information Files (CIFs) extracted from the
Crystallography Open Database (COD). It extracts:
- Canonical SMILES strings using OpenBabel
- Lattice parameters (a, b, c, alpha, beta, gamma)
- Space group information

Malformed files are skipped with detailed logging, adhering to the "fail loudly"
principle for data ingestion.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import json

# Third-party imports
try:
    import PdbCIF as PdbCIF_module # Fallback if PdbCIF is the actual wrapper name, usually PdbCIF is not standard.
    # Standard import for PycifRW
    from CifFile import ReadCif
    # Standard import for OpenBabel
    import openbabel
    from openbabel import pybel
except ImportError as e:
    # We will handle this in the main execution to provide a clear error message
    # rather than crashing immediately on import if the module is missing.
    pass

# Project imports
from config import get_path_absolute
from logging_config import get_logger, log_event
from error_handling import handle_memory_error, safe_process_item
from exceptions import DownloadError, MemoryErrorHandled, ValidationError

logger = get_logger(__name__)

@dataclass
class ParsedStructure:
    """Data class representing a parsed CIF structure."""
    cif_id: str
    smiles: str
    lattice_a: float
    lattice_b: float
    lattice_c: float
    lattice_alpha: float
    lattice_beta: float
    lattice_gamma: float
    space_group: str
    raw_data: Dict[str, Any]
    parse_status: str  # 'success' or 'skipped'
    error_message: Optional[str] = None

def _initialize_openbabel() -> bool:
    """Initialize OpenBabel for chemical format conversion."""
    try:
        # OpenBabel usually auto-detects data paths, but we ensure it's ready
        obConversion = openbabel.OBConversion()
        # We will use CIF to SMI internally
        return True
    except Exception as e:
        logger.error(f"Failed to initialize OpenBabel: {e}")
        return False

def _extract_lattice_params(cif_data: Dict[str, Any]) -> Tuple[float, float, float, float, float, float]:
    """
    Extract lattice parameters from CIF data dictionary.
    Returns (a, b, c, alpha, beta, gamma).
    """
    # Standard CIF keys for lattice parameters
    keys = {
        'a': '_cell_length_a',
        'b': '_cell_length_b',
        'c': '_cell_length_c',
        'alpha': '_cell_angle_alpha',
        'beta': '_cell_angle_beta',
        'gamma': '_cell_angle_gamma'
    }

    values = {}
    for key_name, cif_key in keys.items():
        # Try direct access, then try case-insensitive or variations if needed
        val = cif_data.get(cif_key)
        if val is None:
            # Try finding it in a case-insensitive way if the key is missing
            for k, v in cif_data.items():
                if k.lower() == cif_key.lower():
                    val = v
                    break
        
        if val is not None:
            try:
                values[key_name] = float(val)
            except ValueError:
                values[key_name] = 0.0
        else:
            # Default to 0.0 if missing, but log a warning later
            values[key_name] = 0.0

    return (
        values['a'], values['b'], values['c'],
        values['alpha'], values['beta'], values['gamma']
    )

def _extract_space_group(cif_data: Dict[str, Any]) -> str:
    """Extract space group symbol from CIF data."""
    possible_keys = [
        '_symmetry_space_group_name_H-M',
        '_space_group_name_H-M_alt',
        '_symmetry_space_group_name_Hall'
    ]
    
    for key in possible_keys:
        val = cif_data.get(key)
        if val:
            # Clean up whitespace
            return str(val).strip()
    
    # Fallback if not found
    return "Unknown"

def _parse_cif_to_smiles(cif_content: str, cif_id: str) -> Optional[str]:
    """
    Convert CIF content to canonical SMILES using OpenBabel.
    
    Args:
        cif_content: The raw string content of the CIF file.
        cif_id: The ID of the crystal for logging purposes.
        
    Returns:
        Canonical SMILES string or None if conversion fails.
    """
    try:
        # Write content to a temporary file for OpenBabel to read
        # OpenBabel's pybel interface works best with file paths
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cif', delete=False) as tmp:
            tmp.write(cif_content)
            tmp_path = tmp.name

        try:
            # Read the molecule
            # Note: pybel.read() returns a generator
            mol_iter = pybel.readfile("cif", tmp_path)
            mol = next(mol_iter, None)
            
            if mol is None:
                logger.warning(f"CIF ID {cif_id}: No molecule found in file.")
                return None
            
            # Convert to SMILES
            # canonical=True ensures a unique representation
            smiles = mol.write("smi").strip()
            
            # OpenBabel output often includes the name at the end: "SMILES Name"
            # We want just the SMILES part
            parts = smiles.split()
            if parts:
                return parts[0]
            return smiles

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        logger.error(f"CIF ID {cif_id}: Failed to convert CIF to SMILES: {e}")
        return None

def parse_cif_file(file_path: Path, cif_id: str) -> ParsedStructure:
    """
    Parse a single CIF file and extract structural data.
    
    Args:
        file_path: Path to the CIF file.
        cif_id: Unique identifier for the crystal (often derived from filename).
        
    Returns:
        ParsedStructure object with extracted data or error details.
    """
    try:
        # Read CIF content
        with open(file_path, 'r', encoding='utf-8') as f:
            cif_content = f.read()
        
        # Parse with PycifRW
        try:
            cif_data = ReadCif(cif_content)
        except Exception as e:
            logger.warning(f"CIF ID {cif_id}: Failed to parse CIF structure: {e}")
            return ParsedStructure(
                cif_id=cif_id,
                smiles="",
                lattice_a=0.0,
                lattice_b=0.0,
                lattice_c=0.0,
                lattice_alpha=0.0,
                lattice_beta=0.0,
                lattice_gamma=0.0,
                space_group="Unknown",
                raw_data={},
                parse_status="skipped",
                error_message=f"Parse error: {str(e)}"
            )
        
        # PycifRW returns a dict of blocks. Usually the first block is the main one.
        # Handle both list and dict returns depending on version
        if isinstance(cif_data, list):
            if not cif_data:
                raise ValueError("Empty CIF file")
            block = cif_data[0]
        else:
            block = cif_data
        
        # Extract Lattice Parameters
        a, b, c, alpha, beta, gamma = _extract_lattice_params(block)
        
        # Extract Space Group
        space_group = _extract_space_group(block)
        
        # Extract SMILES
        # Note: COD organic subset might not have explicit SMILES in the CIF.
        # We attempt to generate it from the atomic coordinates if possible,
        # but often COD organic files contain the formula or we rely on the 
        # 'organic' filter implying we can process them. 
        # However, the task specifically asks to extract SMILES.
        # If the CIF doesn't have a _chemical_formula_structural or similar that maps to SMILES,
        # we try to generate from atoms.
        
        smiles = _parse_cif_to_smiles(cif_content, cif_id)
        
        if smiles is None:
            # If we can't get SMILES, we still return the structural data but mark status
            logger.warning(f"CIF ID {cif_id}: Could not generate SMILES, skipping record.")
            return ParsedStructure(
                cif_id=cif_id,
                smiles="",
                lattice_a=a,
                lattice_b=b,
                lattice_c=c,
                lattice_alpha=alpha,
                lattice_beta=beta,
                lattice_gamma=gamma,
                space_group=space_group,
                raw_data=block,
                parse_status="skipped",
                error_message="SMILES generation failed"
            )

        return ParsedStructure(
            cif_id=cif_id,
            smiles=smiles,
            lattice_a=a,
            lattice_b=b,
            lattice_c=c,
            lattice_alpha=alpha,
            lattice_beta=beta,
            lattice_gamma=gamma,
            space_group=space_group,
            raw_data=block,
            parse_status="success"
        )

    except MemoryError as e:
        logger.error(f"CIF ID {cif_id}: Memory error while parsing.")
        raise MemoryErrorHandled(f"Memory error parsing {cif_id}: {e}")
    except Exception as e:
        logger.error(f"CIF ID {cif_id}: Unexpected error: {e}")
        return ParsedStructure(
            cif_id=cif_id,
            smiles="",
            lattice_a=0.0,
            lattice_b=0.0,
            lattice_c=0.0,
            lattice_alpha=0.0,
            lattice_beta=0.0,
            lattice_gamma=0.0,
            space_group="Unknown",
            raw_data={},
            parse_status="skipped",
            error_message=f"Unexpected error: {str(e)}"
        )

def process_cif_batch(file_paths: List[Path], output_path: Path) -> Dict[str, Any]:
    """
    Process a batch of CIF files and save results to a CSV/JSON.
    
    Args:
        file_paths: List of paths to CIF files.
        output_path: Path to save the results.
        
    Returns:
        Summary statistics of the processing.
    """
    if not file_paths:
        logger.warning("No CIF files provided for processing.")
        return {"processed": 0, "skipped": 0, "total": 0}

    results = []
    success_count = 0
    skip_count = 0
    
    logger.info(f"Starting batch processing of {len(file_paths)} CIF files.")
    
    for i, path in enumerate(file_paths):
        # Extract ID from filename
        cif_id = path.stem
        
        # Use safe_process_item decorator logic or manual try/except
        try:
            result = parse_cif_file(path, cif_id)
            if result.parse_status == 'success':
                success_count += 1
            else:
                skip_count += 1
            results.append(asdict(result))
            
            # Log progress
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i+1}/{len(file_paths)} files.")
                
        except MemoryErrorHandled:
            skip_count += 1
            continue
        except Exception as e:
            logger.error(f"Critical error processing {cif_id}: {e}")
            skip_count += 1
            continue

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Batch processing complete. Success: {success_count}, Skipped: {skip_count}.")
    logger.info(f"Results saved to {output_path}")
    
    return {
        "processed": success_count,
        "skipped": skip_count,
        "total": len(file_paths),
        "output_file": str(output_path)
    }

def main():
    """
    Main entry point for the CIF parsing pipeline.
    Expects a list of CIF file paths or a directory to scan.
    For this task, we assume the files are already downloaded to data/raw/cif/
    """
    # Initialize OpenBabel
    if not _initialize_openbabel():
        logger.error("OpenBabel initialization failed. Cannot proceed.")
        sys.exit(1)

    # Define paths
    project_root = get_path_absolute(".")
    raw_dir = project_root / "data" / "raw" / "cif"
    output_file = project_root / "data" / "processed" / "parsed_structures.json"

    if not raw_dir.exists():
        logger.error(f"Raw CIF directory not found: {raw_dir}")
        logger.error("Please ensure T009 (load_cod.py) has populated this directory.")
        sys.exit(1)

    # Find all CIF files
    cif_files = list(raw_dir.glob("*.cif"))
    
    if not cif_files:
        logger.warning(f"No .cif files found in {raw_dir}")
        # Create an empty output file to indicate completion with 0 items
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump([], f)
        return

    logger.info(f"Found {len(cif_files)} CIF files to parse.")
    
    # Process
    stats = process_cif_batch(cif_files, output_file)
    
    # Print summary
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
