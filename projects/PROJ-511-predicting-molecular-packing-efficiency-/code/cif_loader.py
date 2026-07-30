"""
Base data loading utilities for CIF parsing and SMILES generation.

This module provides core functionality for parsing Crystallographic Information
Files (CIF) from the Crystallography Open Database (COD), extracting molecular
coordinates, and generating SMILES representations using RDKit.

Functions:
    parse_cif_file: Parse a single CIF file and extract structural data.
    fractional_to_cartesian: Convert fractional coordinates to Cartesian.
    generate_smiles_from_cif_data: Generate SMILES from parsed CIF data.
    load_cif_batch: Load multiple CIF files from a directory.
    create_dataset_dataframe: Assemble parsed data into a pandas DataFrame.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Iterator

import numpy as np
import pandas as pd

# RDKit imports
from rdkit import Chem
from rdkit.Chem import AllChem

# Configure logger
logger = logging.getLogger(__name__)

# Bondi van der Waals radii (Angstroms) - FR-018
BONDI_RADII = {
    'H': 1.20, 'He': 1.40, 'Li': 1.82, 'Be': 1.53, 'B': 1.92, 'C': 1.70,
    'N': 1.55, 'O': 1.52, 'F': 1.47, 'Ne': 1.54, 'Na': 2.27, 'Mg': 1.73,
    'Al': 1.84, 'Si': 2.10, 'P': 1.80, 'S': 1.80, 'Cl': 1.75, 'Ar': 1.88,
    'K': 2.75, 'Ca': 2.31, 'Sc': 2.11, 'Ti': 2.00, 'V': 1.90, 'Cr': 1.89,
    'Mn': 1.80, 'Fe': 1.94, 'Co': 1.92, 'Ni': 1.63, 'Cu': 1.40, 'Zn': 1.39,
    'Ga': 1.87, 'Ge': 2.11, 'As': 1.85, 'Se': 1.90, 'Br': 1.85, 'Kr': 2.02,
    'Rb': 3.03, 'Sr': 2.49, 'Y': 2.15, 'Zr': 2.06, 'Nb': 1.98, 'Mo': 1.90,
    'Tc': 1.83, 'Ru': 1.84, 'Rh': 1.84, 'Pd': 1.63, 'Ag': 1.72, 'Cd': 1.62,
    'In': 1.93, 'Sn': 2.01, 'Sb': 2.06, 'Te': 2.06, 'I': 1.98, 'Xe': 2.16,
    'Cs': 3.43, 'Ba': 2.68, 'La': 2.07, 'Ce': 2.04, 'Pr': 2.03, 'Nd': 2.01,
    'Pm': 2.00, 'Sm': 1.99, 'Eu': 1.98, 'Gd': 1.97, 'Tb': 1.96, 'Dy': 1.95,
    'Ho': 1.94, 'Er': 1.93, 'Tm': 1.92, 'Yb': 1.91, 'Lu': 1.90, 'Hf': 2.03,
    'Ta': 2.00, 'W': 1.93, 'Re': 1.88, 'Os': 1.85, 'Ir': 1.85, 'Pt': 1.77,
    'Au': 1.66, 'Hg': 1.51, 'Tl': 1.86, 'Pb': 1.87, 'Bi': 1.85, 'Po': 1.85,
    'At': 1.85, 'Rn': 1.95
}

# Regex patterns for CIF parsing
_CIF_PATTERN_CELL_PARAMS = re.compile(
    r'_cell_length_a\s+([\d\.eE+-]+)\s*'
    r'_cell_length_b\s+([\d\.eE+-]+)\s*'
    r'_cell_length_c\s+([\d\.eE+-]+)\s*'
    r'_cell_angle_alpha\s+([\d\.eE+-]+)\s*'
    r'_cell_angle_beta\s+([\d\.eE+-]+)\s*'
    r'_cell_angle_gamma\s+([\d\.eE+-]+)',
    re.IGNORECASE
)

_CIF_PATTERN_SPACE_GROUP = re.compile(
    r'_space_group_name_H-M[\'"]?\s+\'?([^\s\']+)\'?',
    re.IGNORECASE
)

_CIF_PATTERN_ATOM_SITE = re.compile(
    r'_atom_site_label\s+([^\n]+)\n'
    r'_atom_site_type_symbol\s+([^\n]+)\n'
    r'_atom_site_fract_x\s+([^\n]+)\n'
    r'_atom_site_fract_y\s+([^\n]+)\n'
    r'_atom_site_fract_z\s+([^\n]+)',
    re.IGNORECASE | re.MULTILINE
)

def parse_cif_file(cif_path: str) -> Dict[str, Any]:
    """
    Parse a single CIF file and extract structural data.
    
    Args:
        cif_path: Path to the CIF file.
        
    Returns:
        Dictionary containing:
            - 'cell_params': Tuple of (a, b, c, alpha, beta, gamma)
            - 'space_group': Space group string
            - 'atoms': List of dicts with 'label', 'symbol', 'fract_coords'
            - 'raw_content': Full file content
            - 'source_file': Filename
            
    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If required fields are missing.
    """
    if not os.path.exists(cif_path):
        raise FileNotFoundError(f"CIF file not found: {cif_path}")
        
    with open(cif_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # Extract cell parameters
    cell_match = _CIF_PATTERN_CELL_PARAMS.search(content)
    if not cell_match:
        logger.warning(f"Cell parameters not found in {cif_path}")
        # Try to extract individual parameters
        a = float(re.search(r'_cell_length_a\s+([\d\.eE+-]+)', content, re.I).group(1) or 0)
        b = float(re.search(r'_cell_length_b\s+([\d\.eE+-]+)', content, re.I).group(1) or 0)
        c = float(re.search(r'_cell_length_c\s+([\d\.eE+-]+)', content, re.I).group(1) or 0)
        alpha = float(re.search(r'_cell_angle_alpha\s+([\d\.eE+-]+)', content, re.I).group(1) or 90)
        beta = float(re.search(r'_cell_angle_beta\s+([\d\.eE+-]+)', content, re.I).group(1) or 90)
        gamma = float(re.search(r'_cell_angle_gamma\s+([\d\.eE+-]+)', content, re.I).group(1) or 90)
    else:
        a, b, c, alpha, beta, gamma = map(float, cell_match.groups())
        
    # Extract space group
    spg_match = _CIF_PATTERN_SPACE_GROUP.search(content)
    space_group = spg_match.group(1) if spg_match else "Unknown"
    
    # Extract atom sites
    atoms = []
    atom_matches = _CIF_PATTERN_ATOM_SITE.findall(content)
    for match in atom_matches:
        label = match[0].strip()
        symbol = match[1].strip()
        x = float(match[2].strip())
        y = float(match[3].strip())
        z = float(match[4].strip())
        atoms.append({
            'label': label,
            'symbol': symbol,
            'fract_coords': (x, y, z)
        })
        
    if not atoms:
        # Fallback: try loop_ format
        loop_atoms = parse_cif_loop_atoms(content)
        atoms = loop_atoms
        
    if not atoms:
        raise ValueError(f"No atoms found in {cif_path}")
        
    return {
        'cell_params': (a, b, c, alpha, beta, gamma),
        'space_group': space_group,
        'atoms': atoms,
        'raw_content': content,
        'source_file': os.path.basename(cif_path)
    }

def parse_cif_loop_atoms(content: str) -> List[Dict[str, Any]]:
    """
    Fallback parser for loop_ formatted atom sites.
    
    Args:
        content: Full CIF content.
        
    Returns:
        List of atom dictionaries.
    """
    atoms = []
    
    # Find loop_ block for atom_site
    loop_pattern = re.compile(
        r'loop_\s*'
        r'_atom_site_label\s+([^\n]+)\s*'
        r'_atom_site_type_symbol\s+([^\n]+)\s*'
        r'_atom_site_fract_x\s+([^\n]+)\s*'
        r'_atom_site_fract_y\s+([^\n]+)\s*'
        r'_atom_site_fract_z\s+([^\n]+)\s*',
        re.IGNORECASE
    )
    
    loop_match = loop_pattern.search(content)
    if not loop_match:
        return atoms
        
    # Extract column headers and data
    lines = content.split('\n')
    in_atom_loop = False
    atom_data = []
    
    for line in lines:
        if 'loop_' in line.lower() and '_atom_site_label' in content[content.find(line):content.find(line)+500]:
            in_atom_loop = True
            continue
            
        if in_atom_loop:
            if line.strip().startswith('_') or line.strip() == '':
                if atom_data:
                    break
                continue
                
            parts = line.split()
            if len(parts) >= 5:
                atom_data.append(parts)
                
    # Parse data
    for row in atom_data:
        if len(row) >= 5:
            atoms.append({
                'label': row[0],
                'symbol': row[1],
                'fract_coords': (float(row[2]), float(row[3]), float(row[4]))
            })
            
    return atoms

def fractional_to_cartesian(
    frac_coords: Tuple[float, float, float],
    cell_params: Tuple[float, float, float, float, float, float]
) -> np.ndarray:
    """
    Convert fractional coordinates to Cartesian coordinates.
    
    Args:
        frac_coords: Tuple (x, y, z) fractional coordinates.
        cell_params: Tuple (a, b, c, alpha, beta, gamma) in Angstroms and degrees.
        
    Returns:
        NumPy array of Cartesian coordinates (x, y, z).
    """
    a, b, c, alpha, beta, gamma = cell_params
    
    # Convert angles to radians
    alpha_rad = np.radians(alpha)
    beta_rad = np.radians(beta)
    gamma_rad = np.radians(gamma)
    
    # Calculate metric tensor elements
    cos_alpha = np.cos(alpha_rad)
    cos_beta = np.cos(beta_rad)
    cos_gamma = np.cos(gamma_rad)
    sin_gamma = np.sin(gamma_rad)
    
    # Calculate Cartesian components
    x = frac_coords[0] * a
    y = frac_coords[1] * b * cos_gamma + frac_coords[0] * a * 0  # Simplified
    z = frac_coords[2] * c * cos_beta + frac_coords[1] * b * (cos_alpha - cos_beta * cos_gamma) / sin_gamma + frac_coords[0] * a * 0
    
    # More accurate conversion using transformation matrix
    # x_cart = a * x + b * cos(gamma) * y + c * cos(beta) * z
    # y_cart = b * sin(gamma) * y + c * (cos(alpha) - cos(beta)*cos(gamma))/sin(gamma) * z
    # z_cart = c * sqrt(1 - cos^2(alpha) - cos^2(beta) - cos^2(gamma) + 2*cos(alpha)*cos(beta)*cos(gamma)) / sin(gamma) * z
    
    volume_factor = np.sqrt(
        1 - cos_alpha**2 - cos_beta**2 - cos_gamma**2 + 
        2 * cos_alpha * cos_beta * cos_gamma
    )
    
    cart_x = a * frac_coords[0] + b * cos_gamma * frac_coords[1] + c * cos_beta * frac_coords[2]
    cart_y = b * sin_gamma * frac_coords[1] + c * (cos_alpha - cos_beta * cos_gamma) / sin_gamma * frac_coords[2]
    cart_z = c * volume_factor / sin_gamma * frac_coords[2]
    
    return np.array([cart_x, cart_y, cart_z])

def generate_smiles_from_cif_data(
    cif_data: Dict[str, Any],
    remove_h: bool = True
) -> Optional[str]:
    """
    Generate a SMILES string from parsed CIF data.
    
    Args:
        cif_data: Dictionary from parse_cif_file.
        remove_h: If True, remove hydrogen atoms before SMILES generation.
        
    Returns:
        SMILES string or None if generation fails.
    """
    atoms = cif_data.get('atoms', [])
    if not atoms:
        logger.warning("No atoms to generate SMILES from")
        return None
        
    # Build RDKit molecule from coordinates
    mol = Chem.RWMol()
    atom_map = {}
    
    for atom in atoms:
        symbol = atom['symbol']
        x, y, z = atom['fract_coords']
        cart = fractional_to_cartesian((x, y, z), cif_data['cell_params'])
        
        rdkit_atom = Chem.Atom(symbol)
        idx = mol.AddAtom(rdkit_atom)
        atom_map[atom['label']] = idx
        
        # Set position
        mol.GetConformer().SetAtomPosition(idx, cart)
        
    # If removing hydrogens, do so now
    if remove_h:
        mol = Chem.RemoveHs(mol)
        
    # Sanitize and generate SMILES
    try:
        Chem.SanitizeMol(mol)
        # Add bonds based on distance
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        mol = Chem.RemoveHs(mol)
        
        smiles = Chem.MolToSmiles(mol)
        return smiles
    except Exception as e:
        logger.warning(f"SMILES generation failed: {e}")
        return None

def load_cif_batch(
    cif_dir: str,
    max_files: Optional[int] = None,
    extensions: List[str] = ['.cif']
) -> Iterator[Dict[str, Any]]:
    """
    Load multiple CIF files from a directory.
    
    Args:
        cif_dir: Directory containing CIF files.
        max_files: Maximum number of files to load (None for all).
        extensions: List of file extensions to consider.
        
    Yields:
        Parsed CIF data dictionaries.
    """
    count = 0
    for filename in sorted(os.listdir(cif_dir)):
        if max_files and count >= max_files:
            break
            
        if any(filename.endswith(ext) for ext in extensions):
            filepath = os.path.join(cif_dir, filename)
            try:
                data = parse_cif_file(filepath)
                yield data
                count += 1
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
                continue

def create_dataset_dataframe(
    cif_data_list: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Assemble parsed CIF data into a pandas DataFrame.
    
    Args:
        cif_data_list: List of parsed CIF dictionaries.
        
    Returns:
        DataFrame with columns:
            - source_file
            - a, b, c, alpha, beta, gamma
            - space_group
            - atom_count
            - smiles (if generated)
    """
    records = []
    for data in cif_data_list:
        a, b, c, alpha, beta, gamma = data['cell_params']
        smiles = generate_smiles_from_cif_data(data)
        
        records.append({
            'source_file': data['source_file'],
            'a': a,
            'b': b,
            'c': c,
            'alpha': alpha,
            'beta': beta,
            'gamma': gamma,
            'space_group': data['space_group'],
            'atom_count': len(data['atoms']),
            'smiles': smiles
        })
        
    return pd.DataFrame(records)
