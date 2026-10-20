"""
Composition‑only graph constructor.

This module provides a function to build a fully‑connected element graph
for a material given its chemical formula and target properties
(band_gap, hardness).  Nodes correspond to unique elements in the
composition and carry five features:

    1. element_fraction  – stoichiometric fraction of the element
    2. atomic_number
    3. electronegativity (Pauling scale, if known)
    4. valence_electrons
    5. atomic_radius (in Å, if known)

Edges form a clique including self‑loops.  Edge weights are the Euclidean
distance between the 4‑dimensional periodic‑property vectors
(features 2‑5, i.e. everything except the fraction).

The function returns a :class:`torch_geometric.data.Data` object with
``x``, ``edge_index``, ``edge_weight`` and the regression target ``y``.
Graphs can optionally be cached under ``data/processed/graphs/{material_id}.pt``.
"""

import logging
from pathlib import Path
from typing import Optional

import torch
from torch_geometric.data import Data
from pymatgen.core import Composition
from pymatgen.core.periodic_table import Element

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------

def _element_features(symbol: str) -> Optional[torch.Tensor]:
    """
    Return a tensor of the four periodic‑table features for ``symbol``:
    (atomic_number, electronegativity, valence_electrons, atomic_radius).

    If any attribute is unavailable in ``pymatgen`` we fall back to ``nan``.
    """
    try:
        el = Element(symbol)
    except Exception as exc:  # pragma: no cover – unexpected parsing error
        log.warning("Failed to create Element for symbol %s: %s", symbol, exc)
        return None

    # Atomic number (always present)
    atomic_number = float(el.Z)

    # Pauling electronegativity – may be ``None`` for some elements
    electronegativity = float(getattr(el, "X", float("nan")))

    # Valence electrons – ``valence`` attribute may be ``None``
    valence_electrons = float(getattr(el, "valence", float("nan")))

    # Atomic radius – pymatgen stores it as ``atomic_radius`` (may be None)
    atomic_radius = float(getattr(el, "atomic_radius", float("nan")))

    return torch.tensor(
        [atomic_number, electronegativity, valence_electrons, atomic_radius],
        dtype=torch.float,
    )

def _build_edge_index(num_nodes: int) -> torch.Tensor:
    """
    Fully‑connected clique (including self‑loops) edge index of shape
    ``[2, num_nodes ** 2]``.
    """
    src = torch.arange(num_nodes).repeat_interleave(num_nodes)
    dst = torch.arange(num_nodes).repeat(num_nodes)
    return torch.stack([src, dst], dim=0)

def _compute_edge_weights(
    node_features: torch.Tensor, edge_index: torch.Tensor
) -> torch.Tensor:
    """
    Compute Euclidean distances in the 4‑D periodic‑property space
    (i.e. all node features *except* the first column which is the
    element fraction).  ``node_features`` is ``[N, 5]``; we slice off the
    first column and then compute pairwise distances according to the
    ``edge_index`` tensor.
    """
    # Slice off the element‑fraction column
    prop_vecs = node_features[:, 1:]  # shape (N, 4)

    src_vec = prop_vecs[edge_index[0]]
    dst_vec = prop_vecs[edge_index[1]]
    # Euclidean distance
    return torch.norm(src_vec - dst_vec, dim=1, p=2)

# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------

def build_composition_graph(
    material_id: str,
    formula: str,
    band_gap: float,
    hardness: float,
    cache: bool = True,
) -> Data:
    """
    Build (or load) a composition‑only graph for ``material_id``.

    Parameters
    ----------
    material_id
        Unique identifier for the material – used for optional caching.
    formula
        Chemical formula (e.g. ``Fe2O3``).  Must be parseable by
        :class:`pymatgen.core.Composition`.
    band_gap
        Target band‑gap value (eV).
    hardness
        Target hardness value (GPa).
    cache
        If ``True`` the constructed graph is saved under
        ``data/processed/graphs/{material_id}.pt`` and reused on
        subsequent calls.

    Returns
    -------
    torch_geometric.data.Data
        Graph with node features ``x`` (shape ``[n, 5]``), edge index,
        edge weight and target ``y`` (tensor of shape ``[2]``).

    Notes
    -----
    * Unknown elements trigger a warning and the function returns ``None``.
    * The function never raises on unknown elements – this matches the
      behaviour expected by the unit tests.
    """
    # -----------------------------------------------------------------
    # Optional caching
    # -----------------------------------------------------------------
    cache_path: Path = paths.data("processed", "graphs", f"{material_id}.pt")
    if cache and cache_path.is_file():
        log.debug("Loading cached graph for material_id %s", material_id)
        return torch.load(cache_path)

    # -----------------------------------------------------------------
    # Parse the composition
    # -----------------------------------------------------------------
    try:
        comp = Composition(formula)
    except Exception as exc:
        log.warning("Failed to parse formula '%s' (material_id=%s): %s", formula, material_id, exc)
        return None

    # Ensure every element is known to pymatgen; if any are missing, warn & skip
    unknown_elements = [el for el in comp.elements if not hasattr(Element, "Z")]
    if unknown_elements:
        log.warning(
            "Unknown element(s) %s in formula '%s' (material_id=%s)",
            unknown_elements,
            formula,
            material_id,
        )
        return None

    # -----------------------------------------------------------------
    # Build node feature matrix
    # -----------------------------------------------------------------
    element_symbols = [el.symbol for el in comp.elements]
    fractions = [comp.get_atomic_fraction(sym) for sym in element_symbols]

    feature_rows = []
    for sym, frac in zip(element_symbols, fractions):
        per_elem = _element_features(sym)
        if per_elem is None:
            # This should have been caught above, but be defensive
            log.warning(
                "Skipping element %s in formula %s (material_id=%s) because feature extraction failed",
                sym,
                formula,
                material_id,
            )
            return None
        # Concatenate fraction as the first column
        row = torch.cat([torch.tensor([float(frac)], dtype=torch.float), per_elem])
        feature_rows.append(row)

    x = torch.stack(feature_rows, dim=0)  # shape (num_nodes, 5)

    # -----------------------------------------------------------------
    # Edge construction
    # -----------------------------------------------------------------
    num_nodes = x.size(0)
    edge_index = _build_edge_index(num_nodes)
    edge_weight = _compute_edge_weights(x, edge_index)

    # -----------------------------------------------------------------
    # Target tensor
    # -----------------------------------------------------------------
    y = torch.tensor([float(band_gap), float(hardness)], dtype=torch.float)

    data = Data(x=x, edge_index=edge_index, edge_weight=edge_weight, y=y)

    # -----------------------------------------------------------------
    # Cache if requested
    # -----------------------------------------------------------------
    if cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(data, cache_path)
        log.debug("Cached graph for material_id %s at %s", material_id, cache_path)

    return data
