"""
utils/graph_builder.py
----------------------
Helper functions to construct a NetworkX graph from an RDKit molecule
and to perform basic validation. These utilities are used by the
TDA computation pipeline (code/02_tda_computation.py).
"""

from typing import Optional, Any

import networkx as nx
from rdkit import Chem
from rdkit.Chem import rdmolops

# Type alias for clarity – the TDA pipeline expects a NetworkX Graph
Graph = nx.Graph


def build_graph(smiles: str) -> Optional[Graph]:
    """
    Convert a SMILES string into an undirected NetworkX graph.

    Parameters
    ----------
    smiles: str
        SMILES representation of the molecule.

    Returns
    -------
    Optional[Graph]
        A NetworkX Graph if the SMILES is valid, otherwise ``None``.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    # Ensure the molecule has explicit hydrogens removed (they are not needed for
    # the shortest‑path distance filtration used in this project).
    mol = Chem.RemoveHs(mol)

    # Obtain the adjacency matrix (numpy array) where entry (i, j) == 1
    # if there is a bond between atoms i and j.
    adj = rdmolops.GetAdjacencyMatrix(mol)

    # Create a NetworkX graph from the adjacency matrix.
    G = nx.from_numpy_array(adj)

    # Preserve atom indices as node attributes for potential downstream use.
    for idx, atom in enumerate(mol.GetAtoms()):
        G.nodes[idx]["atom_symbol"] = atom.GetSymbol()
        G.nodes[idx]["atomic_num"] = atom.GetAtomicNum()

    return G


def validate_graph(graph: Graph) -> bool:
    """
    Perform a lightweight validation of the constructed graph.

    The current pipeline only requires that the graph is non‑empty.
    Additional checks (e.g., connectivity) can be added later without
    affecting the existing interface.

    Parameters
    ----------
    graph: Graph
        The NetworkX graph to validate.

    Returns
    -------
    bool
        ``True`` if the graph passes validation, ``False`` otherwise.
    """
    # The graph must contain at least one node.
    if graph is None or graph.number_of_nodes() == 0:
        return False

    # Optionally, ensure the graph is undirected (NetworkX Graph is undirected by default).
    # No further validation is required for the baseline TDA computation.
    return True
