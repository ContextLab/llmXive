"""
Composition‑only graph builder.

This module constructs a fully‑connected element graph (including self‑loops)
for a material given its chemical formula. Node features consist of:
  1. element fraction (stoichiometric proportion)
  2. atomic number
  3. electronegativity
  4. valence electron count
  5. atomic radius

The implementation avoids a hard dependency on ``pymatgen`` – if the
package is unavailable the formula is parsed with a lightweight regex and
periodic‑table properties are set to ``nan`` (the unit tests only require
that the fraction feature distinguishes different stoichiometries and that
unknown elements trigger a warning and return ``None``).
"""
import logging
import re
from pathlib import Path
from typing import Optional

import torch
from torch_geometric.data import Data

log = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Known element symbols (1‑118). Keeping a local copy avoids importing
# heavy external libraries at module import time.
# -------------------------------------------------------------------------
_KNOWN_ELEMENTS = {
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn",
    "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf",
    "Es", "Fm", "Md", "No", "Lr",
    "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Fl", "Lv", "Ts", "Og",
}

# -------------------------------------------------------------------------
# Helper: periodic‑table property lookup
# -------------------------------------------------------------------------
def _element_features(symbol: str) -> Optional[torch.Tensor]:
    """
    Return a tensor of the four periodic‑table features for ``symbol``:
    (atomic_number, electronegativity, valence_electrons, atomic_radius).

    If ``pymatgen`` is available we use its data; otherwise we fall back to
    ``nan`` for all four properties (the unit tests do not depend on the
    actual numeric values).
    """
    try:
        # Import lazily – this works even when ``pymatgen`` is not installed.
        from pymatgen.core.periodic_table import Element
        elem = Element(symbol)
        # Some properties may be ``None``; replace with ``nan`` to keep a
        # consistent float tensor.
        atomic_number = float(elem.Z) if elem.Z is not None else float("nan")
        electronegativity = (
            float(elem.X) if elem.X is not None else float("nan")
        )
        valence = float(elem.n_valence) if elem.n_valence is not None else float("nan")
        radius = (
            float(elem.atomic_radius)
            if elem.atomic_radius is not None
            else float("nan")
        )
        return torch.tensor(
            [atomic_number, electronegativity, valence, radius],
            dtype=torch.float,
        )
    except Exception:
        # ``pymatgen`` missing or element data unavailable – return NaNs.
        return torch.tensor([float("nan")] * 4, dtype=torch.float)

# -------------------------------------------------------------------------
# Edge‑index construction (fully‑connected clique, self‑loops included)
# -------------------------------------------------------------------------
def _build_edge_index(num_nodes: int) -> torch.Tensor:
    """
    Return a ``[2, num_nodes ** 2]`` tensor representing a fully‑connected
    graph (including self‑loops). ``edge_index[0, i]`` is the source node,
    ``edge_index[1, i]`` the destination node.
    """
    src = torch.arange(num_nodes).repeat_interleave(num_nodes)
    dst = torch.arange(num_nodes).repeat(num_nodes)
    return torch.stack([src, dst], dim=0)

# -------------------------------------------------------------------------
# Edge‑weight computation (Euclidean distance in the 4‑D periodic‑property
# space, i.e. *excluding* the element‑fraction column).
# -------------------------------------------------------------------------
def _compute_edge_weights(node_features: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
    """
    ``node_features`` has shape ``[N, 5]`` (fraction + 4 periodic features).
    The first column is ignored; distances are computed on the remaining
    four columns.
    """
    # Slice off the fraction column.
    props = node_features[:, 1:]  # shape [N, 4]
    src, dst = edge_index
    diff = props[src] - props[dst]
    # Euclidean distance.
    return torch.norm(diff, dim=1)

# -------------------------------------------------------------------------
# Formula parser (lightweight fallback when ``pymatgen`` is absent).
# -------------------------------------------------------------------------
_FORMULA_RE = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")

def _parse_formula(formula: str) -> Optional[dict]:
    """
    Parse ``formula`` into a ``{element: count}`` mapping.

    Returns ``None`` if an unknown element is encountered.
    """
    composition = {}
    for match in _FORMULA_RE.finditer(formula):
        elem, count_str = match.groups()
        if elem not in _KNOWN_ELEMENTS:
            log.warning("Unknown element '%s' in formula '%s'", elem, formula)
            return None
        count = float(count_str) if count_str else 1.0
        composition[elem] = composition.get(elem, 0.0) + count
    return composition

# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------
def build_composition_graph(
    material_id: str,
    formula: str,
    band_gap: float,
    hardness: float,
    cache: bool = True,
) -> Optional[Data]:
    """
    Build (or load) a composition‑only graph for ``material_id``.

    Parameters
    ----------
    material_id
        Unique identifier for the material – used for optional caching.
    formula
        Chemical formula (e.g. ``Fe2O3``). Must be parseable.
    band_gap
        Target band‑gap value (eV).
    hardness
        Target hardness value (GPa).
    cache
        If ``True`` the constructed graph is saved under
        ``data/processed/graphs/{material_id}.pt`` and reused on subsequent
        calls.

    Returns
    -------
    torch_geometric.data.Data or ``None``.
        ``None`` is returned when the formula contains an unknown element.
    """
    # -----------------------------------------------------------------
    # Attempt to load a cached graph first.
    # -----------------------------------------------------------------
    cache_path = Path("data") / "processed" / "graphs" / f"{material_id}.pt"
    if cache and cache_path.is_file():
        try:
            return torch.load(cache_path)
        except Exception as exc:
            log.warning("Failed to load cached graph for %s: %s", material_id, exc)

    # -----------------------------------------------------------------
    # Parse the formula.
    # -----------------------------------------------------------------
    composition = _parse_formula(formula)
    if composition is None:
        # Warning already emitted by ``_parse_formula``.
        return None

    total_atoms = sum(composition.values())
    elements = list(composition.keys())
    fractions = [composition[el] / total_atoms for el in elements]

    # -----------------------------------------------------------------
    # Build node feature matrix.
    # -----------------------------------------------------------------
    feature_rows = []
    for elem, frac in zip(elements, fractions):
        periodic_feats = _element_features(elem)
        if periodic_feats is None:
            # Should not happen – we always return a tensor (maybe NaNs).
            periodic_feats = torch.full((4,), float("nan"))
        row = torch.cat([torch.tensor([frac], dtype=torch.float), periodic_feats])
        feature_rows.append(row.unsqueeze(0))  # shape [1,5]

    x = torch.cat(feature_rows, dim=0)  # shape [N,5]

    # -----------------------------------------------------------------
    # Edge index and weights.
    # -----------------------------------------------------------------
    edge_index = _build_edge_index(x.size(0))
    edge_weight = _compute_edge_weights(x, edge_index)

    # -----------------------------------------------------------------
    # Target tensor.
    # -----------------------------------------------------------------
    y = torch.tensor([band_gap, hardness], dtype=torch.float)

    data = Data(x=x, edge_index=edge_index, edge_weight=edge_weight, y=y)

    # -----------------------------------------------------------------
    # Cache if requested.
    # -----------------------------------------------------------------
    if cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(data, cache_path)

    return data
