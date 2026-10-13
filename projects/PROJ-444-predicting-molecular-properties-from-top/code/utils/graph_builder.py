"""
utils/graph_builder.py
----------------------
Helper utilities to construct a molecular graph from a SMILES string
using RDKit and to perform minimal validation required by the TDA
computation pipeline.

The public API matches the imports used in ``code/02_tda_computation.py``:
    - ``build_graph(smiles: str) -> Optional[Graph]``
    - ``validate_graph(graph: Graph) -> bool``
    - ``Graph`` (type alias for ``networkx.Graph``)

Only the functionality needed for the baseline TDA feature computation
is implemented – building an undirected graph where nodes correspond to
atom indices and edges correspond to bonds.  Validation simply checks
that the graph contains at least one node; more sophisticated checks
(e.g., connectivity) are unnecessary for the current workflow.
"""

from __future__ import annotations

import logging
from typing import Optional

import networkx as nx
from rdkit import Chem

# Type alias for clarity – the rest of the code expects this name.
Graph = nx.Graph

_log = logging.getLogger(__name__)

def build_graph(smiles: str) -> Optional[Graph]:
    """
    Construct an undirected ``networkx.Graph`` from a SMILES string.

    Parameters
    ----------
    smiles: str
        The SMILES representation of the molecule.

    Returns
    -------
    Optional[Graph]
        A NetworkX graph with atom indices as nodes and bonds as edges,
        or ``None`` if the SMILES cannot be parsed by RDKit.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        _log.debug("RDKit failed to parse SMILES: %s", smiles)
        return None

    G = nx.Graph()
    # Add nodes for each atom (using the atom index as the node identifier)
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx())

    # Add edges for each bond
    for bond in mol.GetBonds():
        begin_idx = bond.GetBeginAtomIdx()
        end_idx = bond.GetEndAtomIdx()
        G.add_edge(begin_idx, end_idx)

    return G

def validate_graph(graph: Graph) -> bool:
    """
    Perform a lightweight validation of the constructed graph.

    The pipeline only requires that the graph is non‑empty; additional
    checks (e.g., connectivity, aromaticity) are handled elsewhere
    or are not necessary for the baseline persistence‑image computation.

    Parameters
    ----------
    graph: Graph
        The NetworkX graph to validate.

    Returns
    -------
    bool
        ``True`` if the graph contains at least one node, ``False`` otherwise.
    """
    if graph is None:
        return False
    if graph.number_of_nodes() == 0:
        _log.debug("Graph validation failed: graph has no nodes.")
        return False
    return True
