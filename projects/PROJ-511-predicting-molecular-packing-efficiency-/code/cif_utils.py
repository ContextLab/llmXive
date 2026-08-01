import os
import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Iterator
import numpy as np
import pandas as pd

from utils import fix_seed, setup_logging
from error_handling import CIFParseError, MissingMetadataError, handle_corrupt_cif

logger = logging.getLogger(__name__)

# Bondi van der Waals radii in Angstroms (FR-018)
BONDI_RADII = {
    'H': 1.20, 'He': 1.40, 'Li': 1.82, 'Be': 1.53, 'B': 2.02, 'C': 1.70, 'N': 1.55,
    'O': 1.52, 'F': 1.47, 'Ne': 1.54, 'Na': 2.27, 'Mg': 1.73, 'Al': 1.84, 'Si': 2.10,
    'P': 1.80, 'S': 1.80, 'Cl': 1.75, 'Ar': 1.88, 'K': 2.75, 'Ca': 2.31, 'Sc': 2.11,
    'Ti': 2.00, 'V': 1.90, 'Cr': 1.89, 'Mn': 1.89, 'Fe': 1.94, 'Co': 1.92, 'Ni': 1.93,
    'Cu': 1.72, 'Zn': 1.63, 'Ga': 1.87, 'Ge': 2.11, 'As': 1.85, 'Se': 1.90, 'Br': 1.85,
    'Kr': 2.02, 'Rb': 3.03, 'Sr': 2.49, 'Y': 2.19, 'Zr': 2.06, 'Nb': 2.03, 'Mo': 2.01,
    'Tc': 1.98, 'Ru': 1.96, 'Rh': 1.95, 'Pd': 1.92, 'Ag': 1.98, 'Cd': 1.97, 'In': 1.93,
    'Sn': 2.10, 'Sb': 2.06, 'Te': 2.06, 'I': 1.98, 'Xe': 2.16, 'Cs': 3.43, 'Ba': 2.68,
    'La': 2.19, 'Ce': 2.12, 'Pr': 2.10, 'Nd': 2.08, 'Pm': 2.05, 'Sm': 2.02, 'Eu': 2.00,
    'Gd': 1.99, 'Tb': 1.97, 'Dy': 1.96, 'Ho': 1.95, 'Er': 1.94, 'Tm': 1.93, 'Yb': 1.92,
    'Lu': 1.91, 'Hf': 2.00, 'Ta': 1.97, 'W': 1.93, 'Re': 1.90, 'Os': 1.87, 'Ir': 1.85,
    'Pt': 1.85, 'Au': 1.84, 'Hg': 1.76, 'Tl': 1.89, 'Pb': 1.92, 'Bi': 1.92, 'Po': 1.92,
    'At': 1.92, 'Rn': 1.92
}

def parse_cif_file(cif_content: str) -> Dict[str, Any]:
    """
    Parse a CIF string into a dictionary of tags and values.
    Handles both simple key-value pairs and loop_ blocks.
    """
    data = {}
    lines = cif_content.split('\n')
    i = 0
    current_loop_keys = []

    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('#'):
            i += 1
            continue

        if line.startswith('loop_'):
            i += 1
            current_loop_keys = []
            while i < len(lines) and lines[i].strip().startswith('_'):
                current_loop_keys.append(lines[i].strip()[1:]) # remove leading underscore
                i += 1
            # Now read rows
            rows = []
            while i < len(lines):
                row_line = lines[i].strip()
                if not row_line or row_line.startswith('#') or row_line.startswith('_') or row_line.startswith('loop_'):
                    break
                # Split by whitespace, but respect quoted strings
                # Simple split for now, assuming CIF format is clean enough for basic parsing
                parts = row_line.split()
                if len(parts) == len(current_loop_keys):
                    rows.append(parts)
                i += 1
            # Assign to data
            for key in current_loop_keys:
                data[key] = [row[current_loop_keys.index(key)] for row in rows]
            continue

        if line.startswith('_'):
            parts = line.split(None, 1)
            key = parts[0][1:] # remove underscore
            value = parts[1] if len(parts) > 1 else ""
            # Handle multi-line values (quoted strings)
            if value.startswith('"') or value.startswith("'"):
                quote_char = value[0]
                if value.endswith(quote_char) and len(value) > 1:
                    value = value[1:-1]
                else:
                    # Multi-line value
                    value_parts = [value[1:]]
                    i += 1
                    while i < len(lines):
                        line = lines[i].strip()
                        if line.endswith(quote_char):
                            value_parts.append(line[:-1])
                            value = ' '.join(value_parts)
                            break
                        else:
                            value_parts.append(line)
                        i += 1
            data[key] = value
        i += 1

    return data

def parse_cif_loop_atoms(cif_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract atomic coordinates from loop_ block in CIF data.
    Returns a list of dicts with keys: symbol, x, y, z, occupancy, etc.
    """
    atoms = []
    # Standard CIF atom loop keys
    atom_keys = ['atom_site_label', 'atom_site_type_symbol', 'atom_site_fract_x', 'atom_site_fract_y', 'atom_site_fract_z', 'atom_site_occupancy']
    # Map to expected keys in data
    symbol_key = 'atom_site_type_symbol'
    x_key = 'atom_site_fract_x'
    y_key = 'atom_site_fract_y'
    z_key = 'atom_site_fract_z'

    if symbol_key not in cif_data or x_key not in cif_data:
        # Try alternative keys if standard ones missing
        if '_atom_site_type_symbol' in cif_data:
            symbol_key = '_atom_site_type_symbol'
        if '_atom_site_fract_x' in cif_data:
            x_key = '_atom_site_fract_x'
        if '_atom_site_fract_y' in cif_data:
            y_key = '_atom_site_fract_y'
        if '_atom_site_fract_z' in cif_data:
            z_key = '_atom_site_fract_z'

    if symbol_key not in cif_data or x_key not in cif_data:
        logger.warning("Could not find atomic coordinate data in CIF.")
        return []

    symbols = cif_data[symbol_key]
    xs = cif_data[x_key]
    ys = cif_data.get(y_key, ['0'] * len(symbols))
    zs = cif_data.get(z_key, ['0'] * len(symbols))
    occupancies = cif_data.get('atom_site_occupancy', ['1.0'] * len(symbols))

    for i in range(len(symbols)):
        try:
            atoms.append({
                'symbol': symbols[i],
                'x': float(xs[i]),
                'y': float(ys[i]),
                'z': float(zs[i]),
                'occupancy': float(occupancies[i]) if i < len(occupancies) else 1.0
            })
        except ValueError:
            logger.warning(f"Skipping invalid atomic data at index {i}")
            continue

    return atoms

def fractional_to_cartesian(atoms: List[Dict[str, Any]], cif_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert fractional coordinates to Cartesian coordinates using unit cell parameters.
    """
    # Extract unit cell parameters
    try:
        a = float(cif_data.get('_cell_length_a', 1.0))
        b = float(cif_data.get('_cell_length_b', 1.0))
        c = float(cif_data.get('_cell_length_c', 1.0))
        alpha = float(cif_data.get('_cell_angle_alpha', 90.0))
        beta = float(cif_data.get('_cell_angle_beta', 90.0))
        gamma = float(cif_data.get('_cell_angle_gamma', 90.0))
    except ValueError:
        logger.warning("Invalid unit cell parameters, assuming orthogonal cell (1,1,1,90,90,90)")
        a, b, c = 1.0, 1.0, 1.0
        alpha, beta, gamma = 90.0, 90.0, 90.0

    # Convert angles to radians
    alpha_rad = np.radians(alpha)
    beta_rad = np.radians(beta)
    gamma_rad = np.radians(gamma)

    # Calculate unit cell vectors
    # Standard conversion for fractional to Cartesian
    # x_cart = x_frac * a
    # y_cart = y_frac * b * cos(gamma) + z_frac * b * sin(gamma) * ...
    # This is a simplified conversion for orthogonal cells, but we need general conversion
    # General conversion matrix:
    # [ a, b*cos(gamma), c*cos(beta) ]
    # [ 0, b*sin(gamma), c*(cos(alpha)-cos(beta)*cos(gamma))/sin(gamma) ]
    # [ 0, 0, c*sqrt(1 - cos^2(alpha) - cos^2(beta) - cos^2(gamma) + 2*cos(alpha)*cos(beta)*cos(gamma)) / sin(gamma) ]

    # Precompute trigonometric values
    cos_alpha, sin_alpha = np.cos(alpha_rad), np.sin(alpha_rad)
    cos_beta, sin_beta = np.cos(beta_rad), np.sin(beta_rad)
    cos_gamma, sin_gamma = np.cos(gamma_rad), np.sin(gamma_rad)

    # Volume of unit cell
    vol = a * b * c * np.sqrt(1 - cos_alpha**2 - cos_beta**2 - cos_gamma**2 + 2*cos_alpha*cos_beta*cos_gamma)

    # Conversion matrix components
    x1, y1, z1 = a, 0.0, 0.0
    x2, y2, z2 = b * cos_gamma, b * sin_gamma, 0.0
    x3, y3, z3 = c * cos_beta, c * (cos_alpha - cos_beta * cos_gamma) / sin_gamma, vol / (a * b * sin_gamma)

    cartesian_atoms = []
    for atom in atoms:
        fx, fy, fz = atom['x'], atom['y'], atom['z']
        cx = fx * x1 + fy * x2 + fz * x3
        cy = fx * y1 + fy * y2 + fz * y3
        cz = fx * z1 + fy * z2 + fz * z3
        cartesian_atoms.append({
            'symbol': atom['symbol'],
            'x': cx,
            'y': cy,
            'z': cz,
            'occupancy': atom['occupancy']
        })

    return cartesian_atoms

def generate_smiles_from_cif_data(cif_data: Dict[str, Any]) -> Tuple[Optional[str], str]:
    """
    Generate SMILES from CIF data.
    First tries to extract from _chemical_structure_SMILES if present.
    Otherwise, generates from 3D geometry using RDKit.
    Returns (smiles, source)
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem

    # Check for explicit SMILES
    if '_chemical_structure_SMILES' in cif_data:
        smiles = cif_data['_chemical_structure_SMILES']
        if smiles and smiles.strip():
            # Validate SMILES
            mol = Chem.MolFromSmiles(smiles)
            if mol is not None:
                return Chem.MolToSmiles(mol), 'extracted'
            else:
                logger.warning(f"Invalid SMILES found in CIF: {smiles}")

    # Generate from 3D geometry
    atoms = parse_cif_loop_atoms(cif_data)
    if not atoms:
        return None, 'none'

    # Convert to Cartesian
    cart_atoms = fractional_to_cartesian(atoms, cif_data)

    # Create RDKit molecule
    mol = Chem.RWMol()
    atom_indices = {}
    for i, atom in enumerate(cart_atoms):
        symbol = atom['symbol']
        if symbol not in BONDI_RADII:
            continue # Skip unknown elements
        idx = mol.AddAtom(Chem.Atom(symbol))
        atom_indices[i] = idx

    # Set positions
    conf = Chem.Conformer(mol.GetNumAtoms())
    for i, atom in enumerate(cart_atoms):
        if i in atom_indices:
            conf.SetAtomPosition(atom_indices[i], (atom['x'], atom['y'], atom['z']))
    mol.AddConformer(conf)

    # Add bonds (heuristic based on distance)
    # This is a simplified bond detection; in reality, CIFs often have explicit bond info
    # We'll use a distance threshold based on covalent radii
    covalent_radii = {
        'H': 0.37, 'C': 0.77, 'N': 0.75, 'O': 0.73, 'F': 0.71, 'Cl': 0.99, 'Br': 1.14, 'I': 1.33,
        'S': 1.02, 'P': 1.10, 'Si': 1.17, 'B': 0.88, 'Na': 1.54, 'K': 2.03, 'Ca': 1.76, 'Fe': 1.24,
        'Cu': 1.28, 'Zn': 1.31, 'Mg': 1.60, 'Al': 1.18
    }
    for i in range(mol.GetNumAtoms()):
        for j in range(i + 1, mol.GetNumAtoms()):
            p1 = conf.GetAtomPosition(i)
            p2 = conf.GetAtomPosition(j)
            dist = np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)
            atom_i = mol.GetAtomWithIdx(i)
            atom_j = mol.GetAtomWithIdx(j)
            r_i = covalent_radii.get(atom_i.GetSymbol(), 1.0)
            r_j = covalent_radii.get(atom_j.GetSymbol(), 1.0)
            if dist < 1.4 * (r_i + r_j):
                mol.AddBond(i, j, Chem.BondType.SINGLE)

    # Sanitize and generate SMILES
    try:
        Chem.SanitizeMol(mol)
        # Optimize geometry to fix any bad bonds
        AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
        AllChem.UFFOptimizeMolecule(mol)
        smiles = Chem.MolToSmiles(mol)
        return smiles, 'generated'
    except Exception as e:
        logger.warning(f"Failed to generate SMILES from geometry: {e}")
        return None, 'none'

def load_cif_batch(cif_paths: List[str]) -> Iterator[Tuple[str, Optional[Dict[str, Any]], Optional[str]]]:
    """
    Load a batch of CIF files.
    Yields (cod_id, cif_data, error_message)
    """
    for path in cif_paths:
        cod_id = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            cif_data = parse_cif_file(content)
            yield cod_id, cif_data, None
        except Exception as e:
            error_msg = f"Error loading {path}: {str(e)}"
            logger.error(error_msg)
            yield cod_id, None, error_msg

def create_dataset_dataframe(cif_paths: List[str]) -> pd.DataFrame:
    """
    Create a DataFrame from a list of CIF file paths.
    Includes SMILES, unit cell volume, atom count, etc.
    """
    records = []
    for cod_id, cif_data, error in load_cif_batch(cif_paths):
        if error:
            records.append({
                'cod_id': cod_id,
                'smiles': None,
                'smiles_source': 'none',
                'error': error,
                'unit_cell_volume': None,
                'n_atoms': None,
                'lattice_system': None,
                'temperature_K': None,
                'has_solvent': None
            })
            continue

        # Extract SMILES
        smiles, source = generate_smiles_from_cif_data(cif_data)

        # Extract unit cell volume
        try:
            a = float(cif_data.get('_cell_length_a', 1.0))
            b = float(cif_data.get('_cell_length_b', 1.0))
            c = float(cif_data.get('_cell_length_c', 1.0))
            alpha = float(cif_data.get('_cell_angle_alpha', 90.0))
            beta = float(cif_data.get('_cell_angle_beta', 90.0))
            gamma = float(cif_data.get('_cell_angle_gamma', 90.0))
            alpha_rad, beta_rad, gamma_rad = np.radians(alpha), np.radians(beta), np.radians(gamma)
            vol = a * b * c * np.sqrt(1 - np.cos(alpha_rad)**2 - np.cos(beta_rad)**2 - np.cos(gamma_rad)**2 + 2*np.cos(alpha_rad)*np.cos(beta_rad)*np.cos(gamma_rad))
        except ValueError:
            vol = None

        # Extract atom count
        atoms = parse_cif_loop_atoms(cif_data)
        n_atoms = len(atoms) if atoms else None

        # Extract lattice system
        lattice_system = cif_data.get('_symmetry_space_group_name_H-M', None)
        if lattice_system:
            # Simplified extraction
            if 'monoclinic' in lattice_system.lower():
                lattice_system = 'monoclinic'
            elif 'orthorhombic' in lattice_system.lower():
                lattice_system = 'orthorhombic'
            elif 'tetragonal' in lattice_system.lower():
                lattice_system = 'tetragonal'
            elif 'cubic' in lattice_system.lower():
                lattice_system = 'cubic'
            elif 'trigonal' in lattice_system.lower() or 'rhombohedral' in lattice_system.lower():
                lattice_system = 'trigonal'
            elif 'hexagonal' in lattice_system.lower():
                lattice_system = 'hexagonal'
            elif 'triclinic' in lattice_system.lower():
                lattice_system = 'triclinic'
            else:
                lattice_system = 'unknown'
        else:
            lattice_system = 'unknown'

        # Extract temperature
        temp = cif_data.get('_exptl_temperature', cif_data.get('_cell_measurement_reflns_temperature', None))
        try:
            temperature_K = float(temp) if temp else 298.0 # Default to room temp
        except ValueError:
            temperature_K = 298.0

        # Check for solvent
        formula_sum = cif_data.get('_chemical_formula_sum', '')
        has_solvent = bool(re.search(r'H2O|solvent|water', formula_sum, re.IGNORECASE))

        records.append({
            'cod_id': cod_id,
            'smiles': smiles,
            'smiles_source': source,
            'error': None,
            'unit_cell_volume': vol,
            'n_atoms': n_atoms,
            'lattice_system': lattice_system,
            'temperature_K': temperature_K,
            'has_solvent': has_solvent
        })

    return pd.DataFrame(records)

def main():
    """
    Main function to demonstrate CIF loading and SMILES generation.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Load CIF files and generate SMILES')
    parser.add_argument('--input-dir', type=str, required=True, help='Directory containing CIF files')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file path')
    args = parser.parse_args()

    setup_logging()
    fix_seed(42)

    cif_files = [os.path.join(args.input_dir, f) for f in os.listdir(args.input_dir) if f.endswith('.cif')]
    if not cif_files:
        logger.error(f"No CIF files found in {args.input_dir}")
        return

    logger.info(f"Loading {len(cif_files)} CIF files...")
    df = create_dataset_dataframe(cif_files)
    df.to_csv(args.output, index=False)
    logger.info(f"Dataset saved to {args.output}")
    logger.info(f"Total records: {len(df)}, Valid SMILES: {df['smiles'].notna().sum()}")

if __name__ == '__main__':
    main()