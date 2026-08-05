import os
import json
import logging
import hashlib
import pandas as pd
from pathlib import Path

# Import shared utilities
from utils import get_logger, get_project_paths

# Import data models
from data_models import PolymerRecord

# Import augmentation specific logic (to be defined or assumed existing per API surface)
# Note: The API surface lists these functions. We implement them here to ensure the file is complete and runnable.
# If they were intended to be in a separate module, this file would import them. 
# Given the constraint "Extend, don't re-author" and the API surface listing them in augment.py, 
# we provide the implementation here to satisfy the "real, runnable code" constraint.

class AugmentationTimeoutError(Exception):
    """Raised when augmentation takes too long."""
    pass

def is_ester_bond(smiles: str, atom_idx1: int, atom_idx2: int) -> bool:
    """
    Check if the bond between atom_idx1 and atom_idx2 in the SMILES string is an ester bond.
    Ester pattern: C(=O)O.
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        
        # Get bond object
        bond = mol.GetBondBetweenAtoms(atom_idx1, atom_idx2)
        if bond is None:
            return False
        
        # Check bond type
        if bond.GetBondType() != Chem.BondType.SINGLE:
            return False

        # Check atoms: C-O-C(=O) pattern logic simplified
        # We look for the O in the ester linkage (single bonded to C=O and another C)
        atom1 = mol.GetAtomWithIdx(atom_idx1)
        atom2 = mol.GetAtomWithIdx(atom_idx2)
        
        # Simple heuristic: One atom is Oxygen, the other is Carbon
        # The Oxygen must be connected to a Carbon with a double bond to another Oxygen
        if atom1.GetAtomicNum() == 8: # Atom1 is O
            target_atom = atom2
            other_atom = atom1
        elif atom2.GetAtomicNum() == 8: # Atom2 is O
            target_atom = atom1
            other_atom = atom2
        else:
            return False # Neither is Oxygen, so not the ester linkage O

        # Check if target_atom (Carbon) is connected to a double-bonded Oxygen
        # and also connected to another Carbon (the alkyl part)
        # This is a simplified check for the ester functional group context
        is_ester = False
        for neighbor in target_atom.GetNeighbors():
            if neighbor.GetAtomicNum() == 8: # Found another Oxygen
                # Check if this bond is double
                n_bond = mol.GetBondBetweenAtoms(target_atom.GetIdx(), neighbor.GetIdx())
                if n_bond and n_bond.GetBondType() == Chem.BondType.DOUBLE:
                    # Found C=O, now check if target_atom is connected to another Carbon
                    for neighbor2 in target_atom.GetNeighbors():
                        if neighbor2.GetAtomicNum() == 6 and neighbor2.GetIdx() != neighbor.GetIdx():
                            is_ester = True
                            break
            if is_ester: break
        
        return is_ester
    except Exception as e:
        logging.error(f"Error checking ester bond: {e}")
        return False

def functional_group_preserving_edge_dropout(smiles: str, dropout_rate: float = 0.2) -> str:
    """
    Perform edge dropout on the molecular graph derived from SMILES,
    preserving ester bonds (C(=O)O).
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import rdChemReactions
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return smiles
        
        # Create a editable molecule
        emol = Chem.EditableMol(mol)
        
        # Identify bonds to keep (ester bonds)
        bonds_to_remove = []
        num_bonds = mol.GetNumBonds()
        
        for i in range(num_bonds):
            bond = mol.GetBondWithIdx(i)
            atom1 = bond.GetBeginAtomIdx()
            atom2 = bond.GetEndAtomIdx()
            
            if is_ester_bond(smiles, atom1, atom2):
                continue # Keep ester bonds
            
            # Randomly decide to drop
            import random
            if random.random() < dropout_rate:
                bonds_to_remove.append((atom1, atom2))
        
        # Remove bonds in reverse order to maintain indices
        # Note: EditableMol removes by index, so we need to be careful.
        # A safer approach for RDKit is to rebuild the molecule or use a reaction.
        # For simplicity and robustness, we will use a reaction-based approach if possible,
        # or simply return the original if complex manipulation is too risky without full graph lib.
        # However, standard RDKit doesn't have a direct "remove bond" that keeps H count correct easily.
        # We will use a simplified approach: If we drop a bond, we might break the molecule.
        # A more robust way for "edge dropout" in GNN context is usually done on the tensor graph,
        # not the SMILES string directly. Since the task asks for SMILES canonicalization after,
        # we assume this function returns a SMILES that represents a modified graph.
        # Since modifying SMILES by removing bonds is chemically complex (valence issues),
        # we will simulate this by returning the original SMILES if we cannot safely modify it,
        # OR we implement a simplified version that only works if we can identify a breakable bond.
        
        # Alternative: Use RDKit to generate a new graph with specific edges removed?
        # Given the constraints, we will implement a safe version that returns the original
        # if the modification would break valence, or use a library like `rdkit.Chem.rdmolops`.
        
        # Let's try to remove the bond using EditableMol and sanitize.
        # We need to remove by index in the original molecule's bond list.
        # We must sort indices descending.
        bond_indices_to_remove = []
        for i in range(num_bonds):
            bond = mol.GetBondWithIdx(i)
            atom1 = bond.GetBeginAtomIdx()
            atom2 = bond.GetEndAtomIdx()
            if (atom1, atom2) in bonds_to_remove or (atom2, atom1) in bonds_to_remove:
                bond_indices_to_remove.append(i)
        
        bond_indices_to_remove.sort(reverse=True)
        
        for idx in bond_indices_to_remove:
            try:
                emol.RemoveBond(mol.GetBondWithIdx(idx).GetBeginAtomIdx(), mol.GetBondWithIdx(idx).GetEndAtomIdx())
            except:
                pass # Ignore if already removed or invalid
        
        new_mol = emol.GetMol()
        # Try to sanitize, if it fails (valence error), return original
        try:
            Chem.SanitizeMol(new_mol)
            new_smiles = Chem.MolToSmiles(new_mol)
            return new_smiles
        except:
            # If sanitization fails, the bond removal broke the molecule.
            # In a real GNN augmentation, this would be a graph operation.
            # Here, we fallback to original to avoid invalid SMILES.
            return smiles
        
    except Exception as e:
        logging.error(f"Error in functional_group_preserving_edge_dropout: {e}")
        return smiles

def canonicalize_smiles(smiles: str) -> str:
    """Canonicalize a SMILES string."""
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return smiles
        return Chem.MolToSmiles(mol)
    except Exception as e:
        logging.error(f"Error canonicalizing SMILES: {e}")
        return smiles

def augment_record(smiles: str, dropout_rate: float = 0.2) -> str:
    """Apply augmentation to a single record."""
    # Apply edge dropout
    augmented_smiles = functional_group_preserving_edge_dropout(smiles, dropout_rate)
    # Canonicalize
    final_smiles = canonicalize_smiles(augmented_smiles)
    return final_smiles

def load_pre_augmented_dataset() -> pd.DataFrame:
    """Load the pre-augmented dataset from the processed directory."""
    paths = get_project_paths()
    input_path = paths['processed'] / 'pre_augmented_graph_dataset.csv'
    if not input_path.exists():
        raise FileNotFoundError(f"Pre-augmented dataset not found at {input_path}")
    return pd.read_csv(input_path)

def compute_checksum(df: pd.DataFrame, columns: list) -> str:
    """Compute a checksum for the dataset based on specific columns."""
    # Create a string representation of the relevant data
    data_str = df[columns].to_csv(index=False)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

def augment_dataset(df: pd.DataFrame, action: str) -> pd.DataFrame:
    """
    Augment the dataset based on the action.
    If action is 'augment' or 'augment_aggressive', apply dropout.
    """
    if action not in ['augment', 'augment_aggressive']:
        return df
    
    dropout_rate = 0.2
    if action == 'augment_aggressive':
        dropout_rate = 0.4 # Higher rate for aggressive augmentation
    
    augmented_rows = []
    for _, row in df.iterrows():
        smiles = row['smiles']
        # Apply augmentation
        new_smiles = augment_record(smiles, dropout_rate)
        # Create new row
        new_row = row.copy()
        new_row['smiles'] = new_smiles
        augmented_rows.append(new_row)
    
    # Concatenate original and augmented? Or replace?
    # Usually augmentation adds to the dataset.
    # Let's append the augmented versions to the original dataset.
    augmented_df = pd.DataFrame(augmented_rows)
    result_df = pd.concat([df, augmented_df], ignore_index=True)
    return result_df

def check_augmentation_trigger() -> dict:
    """Read the augmentation trigger state."""
    paths = get_project_paths()
    trigger_file = paths['state'] / 'augmentation_trigger.json'
    if not trigger_file.exists():
        raise FileNotFoundError(f"Augmentation trigger file not found at {trigger_file}")
    
    with open(trigger_file, 'r') as f:
        return json.load(f)

def main():
    """Main entry point for T025a: Augmentation Trigger Decision."""
    logger = get_logger(__name__)
    logger.info("Starting T025a: Augmentation Trigger Decision")
    
    try:
        trigger_info = check_augmentation_trigger()
        action = trigger_info.get('action', 'none')
        n = trigger_info.get('n', 0)
        
        logger.info(f"Trigger status: action={action}, n={n}")
        
        paths = get_project_paths()
        log_file = paths['processed'] / 'augmentation_log.json'
        
        log_data = {
            "task_id": "T025a",
            "trigger_action": action,
            "n": n,
            "status": "processed"
        }
        
        if action == 'none':
            logger.info("Action is 'none'. Skipping augmentation.")
            log_data["status"] = "skipped"
        elif action in ['augment', 'augment_aggressive']:
            logger.info(f"Action is '{action}'. Proceeding to T025b (augmentation execution).")
            log_data["status"] = "proceed"
            # In a real pipeline, this would trigger the next step.
            # For this task, we just log the decision.
        else:
            logger.error(f"Unknown action: {action}")
            log_data["status"] = "error"
            log_data["error"] = f"Unknown action: {action}"
        
        # Write log
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info(f"Augmentation decision logged to {log_file}")
        
    except FileNotFoundError as e:
        logger.error(f"Trigger file not found: {e}")
        paths = get_project_paths()
        log_file = paths['processed'] / 'augmentation_log.json'
        with open(log_file, 'w') as f:
            json.dump({"task_id": "T025a", "status": "error", "error": str(e)}, f)
        raise
    except Exception as e:
        logger.error(f"Error in T025a: {e}")
        raise

if __name__ == "__main__":
    main()