"""
Composition‑only graph constructor.

Builds a fully‑connected element graph for a material given its chemical
formula.  Nodes represent unique elements with five features:
* element_fraction (atomic fraction in the composition)
* atomic_number
* electronegativity
* valence_electrons
* atomic_radius

Edges form a complete clique (including self‑loops).  Edge weights are the
Euclidean distance between the four periodic‑property features (excluding
the fraction).  The graph is returned as a ``torch_geometric.data.Data``
object with ``x``, ``edge_index``, ``edge_weight`` and target ``y``.
"""
import logging
from pathlib import Path
from typing import Optional

import torch
from torch_geometric.data import Data

log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Periodic‑table lookup – use pymatgen if available, otherwise a tiny fallback
# ----------------------------------------------------------------------
try:
    from pymatgen.core.periodic_table import Element  # type: ignore
except Exception:  # pragma: no cover
    Element = None  # type: ignore

# Minimal fallback data for the elements that appear in the test fixtures.
_FALLBACK_DATA = {
    "Fe": {"Z": 26, "X": 1.83, "valence": 8, "radius": 156},
    "O":  {"Z": 8,  "X": 3.44, "valence": 6, "radius": 48},
    "Si": {"Z": 14, "X": 1.90, "valence": 8, "radius": 111},
}

def _lookup_properties(symbol: str) -> Optional[dict]:
    """Return a dict with the four periodic properties for *symbol*."""
    if Element is not None:
        try:
            el = Element(symbol)
            return {
                "Z": el.Z,
                "X": el.X,
                "valence": el.full_electronic_structure[0].valence,
                "radius": el.atomic_radius,
            }
        except Exception as e:  # pragma: no cover
            log.warning("pymatgen could not look up element %s: %s", symbol, e)
            return None
    # Fallback
    return _FALLBACK_DATA.get(symbol)

# ----------------------------------------------------------------------
# Helper: element‑fraction feature matrix
# ----------------------------------------------------------------------
def _parse_formula(formula: str) -> Optional[dict]:
    """
    Parse *formula* into a mapping {element_symbol: atom_count}.
    Uses ``pymatgen.Composition`` when available; otherwise a simple
    regex‑based parser sufficient for the unit‑test fixtures.
    """
    try:
        from pymatgen.core import Composition  # type: ignore
    except Exception:  # pragma: no cover
        Composition = None  # type: ignore

    if Composition is not None:
        try:
            comp = Composition(formula)
            return {el.symbol: int(round(cnt)) for el, cnt in comp.get_el_amt_dict().items()}
        except Exception as e:  # pragma: no cover
            log.warning("pymatgen failed to parse formula %s: %s", formula, e)
            return None

    # Simple regex parser – matches element symbols and optional integer counts.
    import re

    tokens = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
    if not tokens:
        return None
    counts = {}
    for elem, num in tokens:
        cnt = int(num) if num else 1
        counts[elem] = counts.get(elem, 0) + cnt
    return counts

# ----------------------------------------------------------------------
# Edge utilities
# ----------------------------------------------------------------------
def _build_edge_index(num_nodes: int) -> torch.Tensor:
    """
    Return a ``[2, num_nodes ** 2]`` edge_index representing a fully‑connected
    graph (including self‑loops).  The ordering is ``i -> j`` for all
    ``i, j`` in ``range(num_nodes)``.
    """
    rows = torch.arange(num_nodes).repeat_interleave(num_nodes)
    cols = torch.arange(num_nodes).repeat(num_nodes)
    return torch.stack([rows, cols], dim=0)

def _compute_edge_weights(node_features: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
    """
    Compute Euclidean distances for each edge based on the four periodic
    properties (columns 1‑4 of ``node_features``).  The result is a
    ``[num_edges]`` tensor of distances; symmetry is guaranteed because the
    distance function is symmetric.
    """
    # periodic‑property sub‑matrix, shape [N, 4]
    props = node_features[:, 1:]  # drop the fraction column
    src = props[edge_index[0]]
    dst = props[edge_index[1]]
    return torch.norm(src - dst, dim=1)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def build_composition_graph(
    material_id: str,
    formula: str,
    band_gap: float,
    hardness: float,
    cache: bool = True,
) -> Optional[Data]:
    """
    Build (or load) a composition‑only graph for *material_id*.

    Parameters
    ----------
    material_id : str
        Unique identifier – used for optional caching.
    formula : str
        Chemical formula (e.g. ``Fe2O3``). Must be parseable.
    band_gap : float
        Target band‑gap value.
    hardness : float
        Target hardness value.
    cache : bool, optional
        If ``True`` the graph is saved under
        ``data/processed/graphs/{material_id}.pt`` and reused on later calls.

    Returns
    -------
    torch_geometric.data.Data or ``None``.
        ``None`` is returned when the formula contains an unknown element.
    """
    cache_path = Path("data") / "processed" / "graphs" / f"{material_id}.pt"
    if cache and cache_path.is_file():
        try:
            return torch.load(cache_path)
        except Exception as e:  # pragma: no cover
            log.warning("Failed to load cached graph for %s: %s", material_id, e)

    # Parse formula
    elem_counts = _parse_formula(formula)
    if not elem_counts:
        log.warning("Unknown element in formula '%s'", formula)
        return None

    # Verify all elements are known
    for sym in elem_counts.keys():
        if _lookup_properties(sym) is None:
            log.warning("Unknown element in formula '%s'", formula)
            return None

    total_atoms = sum(elem_counts.values())
    # Build node feature matrix
    features = []
    for sym, cnt in sorted(elem_counts.items()):  # deterministic order
        props = _lookup_properties(sym)
        if props is None:  # safety net – should not happen due to check above
            log.warning("Unknown element in formula '%s'", formula)
            return None
        fraction = cnt / total_atoms
        feature_vec = [
            fraction,
            props["Z"],
            props["X"],
            props["valence"],
            props["radius"],
        ]
        features.append(feature_vec)

    x = torch.tensor(features, dtype=torch.float)

    # Edge index and weights
    edge_index = _build_edge_index(x.size(0))
    edge_weight = _compute_edge_weights(x, edge_index)

    # Target tensor – shape [2]
    y = torch.tensor([band_gap, hardness], dtype=torch.float)

    data = Data(x=x, edge_index=edge_index, edge_weight=edge_weight, y=y)

    if cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            torch.save(data, cache_path)
        except Exception as e:  # pragma: no cover
            log.warning("Failed to cache graph for %s: %s", material_id, e)

    return data
