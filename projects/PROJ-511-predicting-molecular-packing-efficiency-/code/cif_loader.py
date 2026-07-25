"""
Base data loading utilities for CIF parsing and SMILES generation.

This module provides core functionality to:
1. Parse Crystallographic Information Files (CIF) to extract metadata and atomic coordinates.
2. Generate canonical SMILES strings from the extracted 3D structures using RDKit.
3. Validate the integrity of the parsed data against basic chemical rules.

It serves as the foundational layer for downstream tasks (T012-T018) that
build the dataset. It relies on the error handling utilities defined in
`code/error_handling.py` and the logging setup from `code/utils.py`.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Iterator

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

# Import shared utilities and error classes
from utils import setup_logging, fix_seed
from error_handling import (
    CIFParseError,
    MissingMetadataError,
    DataValidationError,
    handle_corrupt_cif,
    validate_required_metadata,
    safe_cif_read,
    get_cif_metadata_summary,
    log_processing_statistics,
)

# Constants
CIF_BLOCK_PATTERN = re.compile(r'data_(\S+)')
ATOM_LABEL_PATTERN = re.compile(r'^_atom_site_label')
ATOM_TYPE_PATTERN = re.compile(r'^_atom_site_type_symbol')
ATOM_X_PATTERN = re.compile(r'^_atom_site_fract_x')
ATOM_Y_PATTERN = re.compile(r'^_atom_site_fract_y')
ATOM_Z_PATTERN = re.compile(r'^_atom_site_fract_z')
ATOM_U_PATTERN = re.compile(r'^_atom_site_U_iso_or_equiv')

# Bond lengths (approximate) for validation
MIN_BOND_LENGTH = 0.8  # Angstroms
MAX_BOND_LENGTH = 2.0  # Angstroms

logger = setup_logging("cif_loader")


def parse_cif_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a single CIF file and extract structural data.

    Args:
        file_path: Path to the CIF file.

    Returns:
        Dictionary containing:
            - 'metadata': Dict of global CIF tags (cell parameters, symmetry, etc.)
            - 'atoms': List of dicts with keys 'label', 'type', 'x', 'y', 'z', 'u_iso'.

    Raises:
        CIFParseError: If the file cannot be read or parsed.
        MissingMetadataError: If essential metadata is missing.
    """
    if not os.path.exists(file_path):
        raise CIFParseError(f"CIF file not found: {file_path}")

    try:
        content = safe_cif_read(file_path)
    except Exception as e:
        raise CIFParseError(f"Failed to read CIF file {file_path}: {e}")

    if not content:
        raise CIFParseError(f"Empty CIF file: {file_path}")

    # Extract block name
    block_match = CIF_BLOCK_PATTERN.search(content)
    block_name = block_match.group(1) if block_match else "unknown"

    # Parse global metadata
    metadata = {}
    current_block = None
    atom_site_data = []

    # Simple line-by-line parser for robustness
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            i += 1
            continue

        # Detect data block start
        if line.startswith('data_'):
            current_block = line.split()[0]
            i += 1
            continue

        # Parse key-value pairs
        if line.startswith('_') and ' ' in line:
            key = line.split()[0]
            value = line.split(maxsplit=1)[1].strip() if len(line.split()) > 1 else ""

            # Handle quoted strings
            if value.startswith("'") or value.startswith('"'):
                quote_char = value[0]
                end_idx = value.find(quote_char, 1)
                if end_idx != -1:
                    value = value[1:end_idx]
                else:
                    # Multi-line quote handling (simplified)
                    value = value[1:]
                    while i < len(lines) - 1:
                        i += 1
                        next_line = lines[i].strip()
                        if next_line.endswith(quote_char):
                            value += next_line[:-1]
                            break
                        else:
                            value += next_line + " "

            metadata[key] = value

        # Detect atom site loop
        if '_atom_site_' in line:
            # Collect all loop tags
            loop_tags = []
            while i < len(lines):
                tag_line = lines[i].strip()
                if tag_line.startswith('_atom_site_'):
                    loop_tags.append(tag_line.split()[0])
                    i += 1
                else:
                    break

            # Parse loop data
            data_lines = []
            while i < len(lines):
                data_line = lines[i].strip()
                if not data_line or data_line.startswith('_') or data_line.startswith('loop_'):
                    break
                data_lines.append(data_line)
                i += 1

            # Extract columns
            col_indices = {}
            for idx, tag in enumerate(loop_tags):
                if tag == '_atom_site_label':
                    col_indices['label'] = idx
                elif tag == '_atom_site_type_symbol':
                    col_indices['type'] = idx
                elif tag == '_atom_site_fract_x':
                    col_indices['x'] = idx
                elif tag == '_atom_site_fract_y':
                    col_indices['y'] = idx
                elif tag == '_atom_site_fract_z':
                    col_indices['z'] = idx
                elif tag == '_atom_site_U_iso_or_equiv':
                    col_indices['u_iso'] = idx

            # Parse rows
            for data_line in data_lines:
                # Handle quoted values in data lines
                parts = []
                current_part = ""
                in_quote = False
                quote_char = None
                for char in data_line:
                    if char in ('"', "'") and not in_quote:
                        in_quote = True
                        quote_char = char
                    elif char == quote_char and in_quote:
                        in_quote = False
                        quote_char = None
                    elif char in (' ', '\t') and not in_quote:
                        if current_part:
                            parts.append(current_part)
                            current_part = ""
                    else:
                        current_part += char
                if current_part:
                    parts.append(current_part)

                atom = {}
                for field, idx in col_indices.items():
                    if idx < len(parts):
                        try:
                            if field != 'label' and field != 'type':
                                atom[field] = float(parts[idx])
                            else:
                                atom[field] = parts[idx]
                        except ValueError:
                            atom[field] = parts[idx]
                    else:
                        atom[field] = None
                atom_site_data.append(atom)

            break

        i += 1

    # Validate required metadata
    required_keys = [
        '_cell_length_a', '_cell_length_b', '_cell_length_c',
        '_cell_angle_alpha', '_cell_angle_beta', '_cell_angle_gamma',
        '_space_group_name_H-M_alt'
    ]
    missing = [k for k in required_keys if k not in metadata]
    if missing:
        raise MissingMetadataError(f"Missing required metadata in {file_path}: {missing}")

    # Validate atom data
    if not atom_site_data:
        raise CIFParseError(f"No atom site data found in {file_path}")

    for atom in atom_site_data:
        if atom.get('type') is None or atom.get('x') is None:
            raise CIFParseError(f"Invalid atom data in {file_path}: {atom}")

    return {
        'metadata': metadata,
        'atoms': atom_site_data,
        'block_name': block_name
    }


def fractional_to_cartesian(
    frac_coords: np.ndarray,
    cell_params: Dict[str, float]
) -> np.ndarray:
    """
    Convert fractional coordinates to Cartesian coordinates (Angstroms).

    Args:
        frac_coords: Array of shape (N, 3) with fractional coordinates.
        cell_params: Dictionary with keys 'a', 'b', 'c', 'alpha', 'beta', 'gamma'.

    Returns:
        Array of shape (N, 3) with Cartesian coordinates.
    """
    a = cell_params['a']
    b = cell_params['b']
    c = cell_params['c']
    alpha = np.deg2rad(cell_params['alpha'])
    beta = np.deg2rad(cell_params['beta'])
    gamma = np.deg2rad(cell_params['gamma'])

    # Calculate cell vectors
    vol = a * b * c * np.sqrt(
        1 - np.cos(alpha)**2 - np.cos(beta)**2 - np.cos(gamma)**2
        + 2 * np.cos(alpha) * np.cos(beta) * np.cos(gamma)
    )

    x1 = a
    y1 = 0
    z1 = 0

    x2 = b * np.cos(gamma)
    y2 = b * np.sin(gamma)
    z2 = 0

    x3 = c * np.cos(beta)
    y3 = c * (np.cos(alpha) - np.cos(beta) * np.cos(gamma)) / np.sin(gamma)
    z3 = vol / (a * b * np.sin(gamma))

    # Transformation matrix
    M = np.array([
        [x1, x2, x3],
        [y1, y2, y3],
        [z1, z2, z3]
    ])

    return np.dot(frac_coords, M.T)


def generate_smiles_from_cif_data(
    cif_data: Dict[str, Any],
    use_3d: bool = True
) -> Optional[str]:
    """
    Generate a canonical SMILES string from CIF data.

    This function:
    1. Extracts atomic coordinates and types.
    2. Converts fractional to Cartesian coordinates.
    3. Builds an RDKit molecule object.
    4. Adds hydrogens and optimizes geometry (if 3D is used).
    5. Generates a canonical SMILES.

    Args:
        cif_data: Dictionary from parse_cif_file().
        use_3d: If True, use 3D coordinates for bond perception.

    Returns:
        Canonical SMILES string, or None if generation fails.
    """
    atoms = cif_data['atoms']
    metadata = cif_data['metadata']

    # Extract cell parameters
    cell_params = {
        'a': float(metadata['_cell_length_a']),
        'b': float(metadata['_cell_length_b']),
        'c': float(metadata['_cell_length_c']),
        'alpha': float(metadata['_cell_angle_alpha']),
        'beta': float(metadata['_cell_angle_beta']),
        'gamma': float(metadata['_cell_angle_gamma'])
    }

    # Prepare atomic data
    symbols = []
    coords = []
    for atom in atoms:
        symbols.append(atom['type'])
        coords.append([atom['x'], atom['y'], atom['z']])

    coords = np.array(coords)
    cart_coords = fractional_to_cartesian(coords, cell_params)

    # Create RDKit molecule
    mol = Chem.RWMol()

    # Add atoms
    atom_indices = {}
    for i, symbol in enumerate(symbols):
        # Handle special cases (e.g., H, C, N, O, S, P, F, Cl, Br, I)
        if symbol in ['H', 'C', 'N', 'O', 'S', 'P', 'F', 'Cl', 'Br', 'I']:
            atomic_num = Chem.GetPeriodicTable().GetAtomicNumber(symbol)
            atom = Chem.Atom(atomic_num)
            idx = mol.AddAtom(atom)
            atom_indices[i] = idx
        else:
            # Skip unsupported elements
            logger.warning(f"Skipping unsupported element: {symbol}")
            continue

    # Add bonds based on distance
    if use_3d:
        # Set 3D coordinates
        conf = Chem.Conformer(mol.GetNumAtoms())
        for i, idx in enumerate(atom_indices.values()):
            if i < len(cart_coords):
                conf.SetAtomPosition(idx, cart_coords[i])
        mol.AddConformer(conf)

        # Use distance-based bond perception
        Chem.SanitizeMol(mol)
        Chem.AddHs(mol, addCoords=True)
        Chem.Kekulize(mol, clearAromaticFlags=True)

        # Generate SMILES
        try:
            smiles = Chem.MolToSmiles(mol, isomericSmiles=True)
            return smiles
        except Exception as e:
            logger.error(f"Failed to generate SMILES: {e}")
            return None
    else:
        # Fallback to connectivity-based (less accurate for crystals)
        # This is a simplified approach for non-3D cases
        mol = Chem.AddHs(mol)
        Chem.SanitizeMol(mol)
        try:
            smiles = Chem.MolToSmiles(mol, isomericSmiles=True)
            return smiles
        except Exception as e:
            logger.error(f"Failed to generate SMILES: {e}")
            return None


def load_cif_batch(
    cif_dir: str,
    max_files: Optional[int] = None,
    seed: int = 42
) -> Iterator[Dict[str, Any]]:
    """
    Load CIF files from a directory in a streaming fashion.

    Args:
        cif_dir: Path to directory containing CIF files.
        max_files: Maximum number of files to process (None for all).
        seed: Random seed for shuffling.

    Yields:
        Dictionary with keys:
            - 'file_path': Path to the CIF file.
            - 'cif_data': Parsed CIF data (from parse_cif_file).
            - 'smiles': Generated SMILES string.
            - 'status': 'success' or 'error'.
            - 'error': Error message if status is 'error'.
    """
    fix_seed(seed)
    cif_files = [
        os.path.join(cif_dir, f)
        for f in os.listdir(cif_dir)
        if f.lower().endswith('.cif')
    ]

    if max_files:
        np.random.shuffle(cif_files)
        cif_files = cif_files[:max_files]

    logger.info(f"Processing {len(cif_files)} CIF files from {cif_dir}")

    for file_path in cif_files:
        result = {
            'file_path': file_path,
            'cif_data': None,
            'smiles': None,
            'status': 'success',
            'error': None
        }

        try:
            cif_data = parse_cif_file(file_path)
            result['cif_data'] = cif_data

            smiles = generate_smiles_from_cif_data(cif_data)
            result['smiles'] = smiles

            if not smiles:
                result['status'] = 'error'
                result['error'] = "Failed to generate SMILES"
                logger.warning(f"SMILES generation failed for {file_path}")

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"Failed to process {file_path}: {e}")
            handle_corrupt_cif(file_path, e)

        yield result


def create_dataset_dataframe(
    cif_dir: str,
    output_path: str,
    max_files: Optional[int] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Create a DataFrame from CIF files and save to CSV.

    Args:
        cif_dir: Path to directory containing CIF files.
        output_path: Path to save the CSV file.
        max_files: Maximum number of files to process.
        seed: Random seed.

    Returns:
        DataFrame with columns:
            - 'cif_id': Unique identifier from CIF block name.
            - 'smiles': Canonical SMILES string.
            - 'cell_a', 'cell_b', 'cell_c': Unit cell dimensions.
            - 'cell_alpha', 'cell_beta', 'cell_gamma': Unit cell angles.
            - 'atom_count': Number of non-H atoms.
            - 'status': 'success' or 'error'.
            - 'error': Error message if any.
    """
    records = []
    stats = {'total': 0, 'success': 0, 'error': 0, 'no_smiles': 0}

    for result in load_cif_batch(cif_dir, max_files, seed):
        stats['total'] += 1
        if result['status'] == 'success':
            stats['success'] += 1
            if result['smiles']:
                cif_data = result['cif_data']
                metadata = cif_data['metadata']
                atoms = cif_data['atoms']

                # Count non-H atoms
                non_h_count = sum(1 for a in atoms if a['type'] != 'H')

                record = {
                    'cif_id': cif_data['block_name'],
                    'smiles': result['smiles'],
                    'cell_a': float(metadata['_cell_length_a']),
                    'cell_b': float(metadata['_cell_length_b']),
                    'cell_c': float(metadata['_cell_length_c']),
                    'cell_alpha': float(metadata['_cell_angle_alpha']),
                    'cell_beta': float(metadata['_cell_angle_beta']),
                    'cell_gamma': float(metadata['_cell_angle_gamma']),
                    'atom_count': non_h_count,
                    'status': 'success',
                    'error': None
                }
                records.append(record)
            else:
                stats['no_smiles'] += 1
                record = {
                    'cif_id': result['cif_data']['block_name'] if result['cif_data'] else 'unknown',
                    'smiles': None,
                    'cell_a': None,
                    'cell_b': None,
                    'cell_c': None,
                    'cell_alpha': None,
                    'cell_beta': None,
                    'cell_gamma': None,
                    'atom_count': None,
                    'status': 'error',
                    'error': 'No SMILES generated'
                }
                records.append(record)
        else:
            stats['error'] += 1
            record = {
                'cif_id': os.path.basename(result['file_path']),
                'smiles': None,
                'cell_a': None,
                'cell_b': None,
                'cell_c': None,
                'cell_alpha': None,
                'cell_beta': None,
                'cell_gamma': None,
                'atom_count': None,
                'status': 'error',
                'error': result['error']
            }
            records.append(record)

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)

    log_processing_statistics(stats, output_path)
    logger.info(f"Saved {len(df)} records to {output_path}")

    return df