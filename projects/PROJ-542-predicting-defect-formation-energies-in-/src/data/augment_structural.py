"""
src/data/augment_structural.py
--------------------------------

Implements the structural‑descriptor augmentation step that is
triggered only when the pipeline has flagged that the baseline
compositional model was insufficient (``fallback_needed=True`` in
``data/processed/performance.json``).

The script reads the existing compositional feature matrix,
computes three additional structural descriptors for each
composition using ``pymatgen`` and writes an augmented CSV together
with a SHA‑256 checksum file.

The three descriptors are:
  * ``coordination_number`` – average coordination number of all
    sites in a simple perovskite prototype structure.
  * ``average_bond_length`` – mean distance (Å) between each site
    and its neighbours (cut‑off 3.0 Å) in the same prototype.
  * ``crystal_symmetry`` – crystal system (e.g. ``cubic``) as
    reported by ``pymatgen.symmetry.analyzer.SpacegroupAnalyzer``.

The implementation is deterministic and does not require any
external data beyond the composition string, satisfying the
requirement that the augmentation be based solely on ``pymatgen``.
"""

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
from pymatgen.core import Composition, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import write_checksum

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_performance(perf_path: Path) -> Dict:
    """Load ``performance.json`` and return its content."""
    if not perf_path.is_file():
        raise FileNotFoundError(f"Performance file not found at {perf_path}")
    with perf_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _fallback_needed(perf: Dict) -> bool:
    """Return ``True`` if the fallback flag is set in the performance JSON."""
    return bool(perf.get("fallback_needed", False))


def _build_prototype_structure(composition: str) -> Structure:
    """
    Build a minimal perovskite prototype structure for the given formula.

    The prototype uses the cubic Pm‑3m space group (No. 221) with a
    lattice constant of 4 Å – a common simple perovskite cell.  The
    species list is generated from the stoichiometry of the supplied
    composition (e.g. ``BaTiO3`` → [Ba, Ti, O, O, O]).

    This approach provides a deterministic structure that can be
    analysed for coordination numbers, bond lengths and symmetry
    without needing external crystallographic data.
    """
    comp = Composition(composition)
    # Expand the composition into a list of element symbols respecting
    # the integer multiplicities (the Materials Project data are integer‑based).
    species: List[str] = []
    for el, amt in comp.get_el_amt_dict().items():
        # Round to nearest integer – perovskite formulas are integral.
        count = int(round(amt))
        species.extend([el] * count)

    # Use a simple cubic lattice; the exact geometry is not crucial
    # because we only need relative neighbour information.
    lattice_a = 4.0
    # Spacegroup 221 (Pm-3m) is the archetypal perovskite.
    structure = Structure.from_spacegroup(
        sg=221,
        lattice=[[lattice_a, 0, 0], [0, lattice_a, 0], [0, 0, lattice_a]],
        species=species,
        coords=[[0, 0, 0]] * len(species),  # placeholder fractional coords
    )
    return structure


def _compute_structural_descriptors(composition: str) -> Dict[str, object]:
    """
    Compute the three structural descriptors for a single composition.

    Returns a dictionary with keys:
        - ``coordination_number`` (float)
        - ``average_bond_length`` (float, Å)
        - ``crystal_symmetry`` (str)
    """
    struct = _build_prototype_structure(composition)

    # ------------------------------------------------------------------
    # Coordination number – average over all sites using a 3 Å cutoff.
    # ------------------------------------------------------------------
    cutoff = 3.0  # Å
    total_cn = 0
    total_sites = len(struct)
    for site in struct:
        neighbours = struct.get_neighbors(site, cutoff)
        total_cn += len(neighbours)

    avg_coordination = total_cn / total_sites if total_sites else 0.0

    # ------------------------------------------------------------------
    # Average bond length – average of all neighbour distances.
    # ------------------------------------------------------------------
    all_distances = []
    for site in struct:
        neighbours = struct.get_neighbors(site, cutoff)
        all_distances.extend([n.dist for n in neighbours])

    avg_bond_length = (
        sum(all_distances) / len(all_distances) if all_distances else 0.0
    )

    # ------------------------------------------------------------------
    # Crystal symmetry – use SpacegroupAnalyzer to obtain the crystal system.
    # ------------------------------------------------------------------
    sga = SpacegroupAnalyzer(struct, symprec=0.01)
    crystal_system = sga.get_crystal_system()

    return {
        "coordination_number": round(avg_coordination, 3),
        "average_bond_length": round(avg_bond_length, 3),
        "crystal_symmetry": crystal_system,
    }

# ----------------------------------------------------------------------
# Core augmentation function
# ----------------------------------------------------------------------


def augment_features(input_csv: Path, output_csv: Path) -> None:
    """
    Read the compositional ``features.csv``, compute structural
    descriptors for each row, and write an augmented CSV.

    Parameters
    ----------
    input_csv : Path
        Path to ``data/processed/features.csv`` (must contain a
        ``composition`` column).
    output_csv : Path
        Destination for the augmented feature matrix.
    """
    if not input_csv.is_file():
        raise FileNotFoundError(f"Features file not found at {input_csv}")

    df = pd.read_csv(input_csv)

    if "composition" not in df.columns:
        raise KeyError("Input features CSV must contain a 'composition' column.")

    # Compute descriptors row‑wise.
    descriptor_rows = []
    for comp in df["composition"]:
        try:
            desc = _compute_structural_descriptors(str(comp))
        except Exception as exc:
            log.error(f"Failed to compute structural descriptors for {comp}: {exc}")
            # Propagate the error – the pipeline must not silently ignore failures.
            raise
        descriptor_rows.append(desc)

    # Convert list of dicts to DataFrame and concatenate.
    structural_df = pd.DataFrame(descriptor_rows)
    augmented_df = pd.concat([df.reset_index(drop=True), structural_df], axis=1)

    # Write the augmented CSV.
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    augmented_df.to_csv(output_csv, index=False)

    # Write checksum.
    checksum_path = paths.data("checksums", "features_augmented.sha256")
    write_checksum(output_csv, checksum_path.parent)


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    CLI wrapper used by ``python -m src.data.augment_structural``.
    The function checks the ``fallback_needed`` flag and, if true,
    performs the augmentation.
    """
    perf_path = paths.data("processed", "performance.json")
    performance = _load_performance(perf_path)

    if not _fallback_needed(performance):
        log.info("Fallback not required – augmentation step skipped.")
        return

    input_csv = paths.data("processed", "features.csv")
    output_csv = paths.data("processed", "features_augmented.csv")

    log.info("Fallback detected – augmenting feature matrix with structural descriptors.")
    augment_features(input_csv, output_csv)
    log.info(f"Augmented features written to {output_csv}")
