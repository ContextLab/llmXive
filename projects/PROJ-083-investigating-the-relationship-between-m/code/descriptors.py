import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Import existing utilities if needed, though we use RDKit directly here
# from code.utils.logger import setup_logger

logger = logging.getLogger(__name__)

def is_connected(mol: Chem.Mol) -> bool:
    """
    Checks if the molecule graph is connected (single component).
    
    Args:
        mol: RDKit Mol object.
        
    Returns:
        True if the molecule is a single connected component, False otherwise.
    """
    if mol is None:
        return False
    
    # RDKit's GetNumAtoms returns 0 for empty molecules
    if mol.GetNumAtoms() == 0:
        return False

    # Get the number of connected components (fragments)
    # rdMolDescriptors.CalcNumFragments is not standard for connectivity check in older RDKit
    # Using the standard method: GetMolFrags
    frags = Chem.GetMolFrags(mol, asMols=False, sanitizeFrags=False)
    
    # GetMolFrags returns a tuple of tuples, each inner tuple is atom indices for a fragment
    num_fragments = len(frags)
    return num_fragments == 1

class TopologicalDescriptorCalculator:
    """
    Calculator for topological descriptors (Wiener, Balaban, Zagreb).
    Handles disconnected graphs by flagging them as invalid.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_wiener(self, mol: Chem.Mol) -> Optional[float]:
        """
        Calculates the Wiener index for a molecule.
        Returns None if the molecule is disconnected (invalid topology).
        """
        if not is_connected(mol):
            self.logger.warning(f"Molecule {mol.GetProp('_Name') if mol.HasProp('_Name') else 'unknown'} is disconnected. Skipping Wiener index.")
            return None
        
        try:
            # RDKit has a built-in Wiener index calculator
            # If not available, we would implement BFS/Dijkstra manually
            # rdMolDescriptors.CalcWienerIndex is not standard in all RDKit versions
            # Fallback to manual implementation if needed, but let's try standard first
            # Actually, RDKit's standard library doesn't always expose a direct CalcWienerIndex
            # We will implement a robust BFS-based calculation to ensure accuracy
            return self._calc_wiener_bfs(mol)
        except Exception as e:
            self.logger.error(f"Error calculating Wiener index: {e}")
            return None

    def _calc_wiener_bfs(self, mol: Chem.Mol) -> float:
        """
        Calculates Wiener index using BFS for shortest paths.
        Wiener Index = 0.5 * sum(all-pairs shortest path lengths)
        """
        n = mol.GetNumAtoms()
        if n == 0:
            return 0.0
        
        total_distance = 0
        
        # Build adjacency list
        adj = [[] for _ in range(n)]
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            adj[i].append(j)
            adj[j].append(i)
        
        # BFS from each node
        for start in range(n):
            visited = [-1] * n
            visited[start] = 0
            queue = [start]
            head = 0
            
            while head < len(queue):
                u = queue[head]
                head += 1
                current_dist = visited[u]
                
                for v in adj[u]:
                    if visited[v] == -1:
                        visited[v] = current_dist + 1
                        queue.append(v)
                        total_distance += visited[v]
        
        return float(total_distance)

    def calculate_balaban(self, mol: Chem.Mol) -> Optional[float]:
        """
        Calculates the Balaban index (J).
        Returns None if the molecule is disconnected.
        """
        if not is_connected(mol):
            self.logger.warning(f"Molecule {mol.GetProp('_Name') if mol.HasProp('_Name') else 'unknown'} is disconnected. Skipping Balaban index.")
            return None
        
        try:
            # Balaban J = (M - N + 1) / (N + 2) * sum(1 / sqrt(d_i * d_j))
            # where M = number of bonds, N = number of atoms
            # d_i = distance sum for atom i (sum of shortest path distances to all other atoms)
            
            n = mol.GetNumAtoms()
            m = mol.GetNumBonds()
            
            if n == 0:
                return 0.0
            
            # Calculate distance sums (d_i)
            dist_sums = []
            
            # Re-use adjacency list logic from Wiener
            adj = [[] for _ in range(n)]
            for bond in mol.GetBonds():
                i = bond.GetBeginAtomIdx()
                j = bond.GetEndAtomIdx()
                adj[i].append(j)
                adj[j].append(i)
            
            for start in range(n):
                visited = [-1] * n
                visited[start] = 0
                queue = [start]
                head = 0
                current_sum = 0
                
                while head < len(queue):
                    u = queue[head]
                    head += 1
                    
                    for v in adj[u]:
                        if visited[v] == -1:
                            visited[v] = visited[u] + 1
                            current_sum += visited[v]
                            queue.append(v)
                
                dist_sums.append(current_sum)
            
            # Calculate J
            # J = (M - N + 1) / (N + 2) * sum_{i<j} (1 / sqrt(d_i * d_j))
            # Note: Standard Balaban definition often sums over edges (i,j) in the graph
            # J = (M - N + 1) / (N + 2) * sum_{(i,j) in E} (1 / sqrt(d_i * d_j))
            
            sum_inv_sqrt = 0.0
            for bond in mol.GetBonds():
                i = bond.GetBeginAtomIdx()
                j = bond.GetEndAtomIdx()
                d_i = dist_sums[i]
                d_j = dist_sums[j]
                
                if d_i == 0 or d_j == 0:
                    # Avoid division by zero, though in connected graph with N>1, d>0
                    continue
                
                sum_inv_sqrt += 1.0 / np.sqrt(d_i * d_j)
            
            numerator = m - n + 1
            denominator = n + 2
            
            if denominator == 0:
                return 0.0
                
            return (numerator / denominator) * sum_inv_sqrt
            
        except Exception as e:
            self.logger.error(f"Error calculating Balaban index: {e}")
            return None

    def calculate_zagreb(self, mol: Chem.Mol) -> Optional[Tuple[float, float]]:
        """
        Calculates the First (M1) and Second (M2) Zagreb indices.
        Returns None if the molecule is disconnected.
        M1 = sum(deg(v)^2)
        M2 = sum(deg(u)*deg(v)) for all edges (u,v)
        """
        if not is_connected(mol):
            self.logger.warning(f"Molecule {mol.GetProp('_Name') if mol.HasProp('_Name') else 'unknown'} is disconnected. Skipping Zagreb index.")
            return None
        
        try:
            n = mol.GetNumAtoms()
            if n == 0:
                return (0.0, 0.0)
            
            # Calculate degrees
            degrees = [atom.GetTotalDegree() for atom in mol.GetAtoms()]
            
            # M1
            m1 = sum(d * d for d in degrees)
            
            # M2
            m2 = 0.0
            for bond in mol.GetBonds():
                u = bond.GetBeginAtomIdx()
                v = bond.GetEndAtomIdx()
                m2 += degrees[u] * degrees[v]
            
            return (float(m1), float(m2))
            
        except Exception as e:
            self.logger.error(f"Error calculating Zagreb indices: {e}")
            return None

    def calculate_descriptors(self, mol: Chem.Mol, name: str = "unknown") -> Dict[str, Any]:
        """
        Calculates all descriptors for a molecule.
        If the molecule is disconnected, returns a dict with 'valid_topology' = False.
        """
        result = {
            "name": name,
            "valid_topology": True,
            "wiener": None,
            "balaban": None,
            "zagreb_m1": None,
            "zagreb_m2": None,
            "error": None
        }
        
        if not is_connected(mol):
            result["valid_topology"] = False
            result["error"] = "Disconnected graph (Invalid Topology)"
            return result
        
        try:
            result["wiener"] = self.calculate_wiener(mol)
            result["balaban"] = self.calculate_balaban(mol)
            zagreb = self.calculate_zagreb(mol)
            if zagreb:
                result["zagreb_m1"] = zagreb[0]
                result["zagreb_m2"] = zagreb[1]
        except Exception as e:
            result["error"] = str(e)
            result["valid_topology"] = False
        
        return result

def calculate_descriptors_for_smiles(smiles: str, name: str = "unknown") -> Dict[str, Any]:
    """
    Convenience function to calculate descriptors from a SMILES string.
    Handles invalid SMILES and disconnected graphs.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {
            "name": name,
            "valid_topology": False,
            "error": "Invalid SMILES"
        }
    
    calculator = TopologicalDescriptorCalculator()
    return calculator.calculate_descriptors(mol, name)

def main():
    """
    Main entry point for testing the descriptor calculator with disconnected graph handling.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Test cases
    test_cases = [
        ("benzene", "c1ccccc1"),
        ("toluene", "Cc1ccccc1"),
        ("disconnected_biphenyl", "c1ccccc1.c2ccccc2"), # Two separate rings, no bond
        ("invalid", "invalid_smiles"),
        ("ethane", "CC")
    ]
    
    print("Testing Topological Descriptor Calculator with Disconnected Graph Handling:")
    print("-" * 60)
    
    for name, smiles in test_cases:
        result = calculate_descriptors_for_smiles(smiles, name)
        print(f"Molecule: {name} ({smiles})")
        print(f"  Valid Topology: {result['valid_topology']}")
        if result['valid_topology']:
            print(f"  Wiener: {result['wiener']}")
            print(f"  Balaban: {result['balaban']}")
            print(f"  Zagreb M1: {result['zagreb_m1']}, M2: {result['zagreb_m2']}")
        else:
            print(f"  Error/Reason: {result.get('error', 'Unknown')}")
        print("-" * 60)

if __name__ == "__main__":
    main()
