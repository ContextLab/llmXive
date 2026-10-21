"""
Simulation system builder for molecular dynamics runs.

This module creates an OpenMM system for a given solvent using the
OPLS‑AA / TIP3P style force field.  For the purposes of the current
project only water is required (the test suite builds a water box), but
the implementation is generic enough to be extended to ethanol and
acetone in the future.

The builder returns a tuple ``(system, topology, positions)`` that can be
passed directly to an OpenMM ``Simulation`` object.
"""

from __future__ import annotations

import logging
from typing import Tuple

from openmm import app
from openmm import unit
from openmm import Platform
from openmm import System

from config import SimulationConfig, Solvent

logger = logging.getLogger(__name__)

def _load_forcefield(solvent: Solvent) -> app.ForceField:
    """
    Load an appropriate force field for the given solvent.

    * Water  – TIP3P (compatible with OPLS‑AA style parameters)
    * Ethanol – placeholder (future implementation)
    * Acetone – placeholder (future implementation)

    The project currently only needs water for the smoke test, so we
    return the TIP3P force field for water and raise ``NotImplementedError``
    for the other solvents.
    """
    if solvent == Solvent.WATER:
        # TIP3P is bundled with OpenMM and works with the standard amber
        # force field XML files.
        return app.ForceField("amber14/tip3p.xml")
    else:
        raise NotImplementedError(
            f"Force field generation for solvent {solvent.value} is not yet implemented."
        )

def build_system(
    solvent: Solvent,
    config: SimulationConfig,
    seed: int = 0,
) -> Tuple[System, app.Topology, list]:
    """
    Build an OpenMM system for a cubic box of the requested solvent.

    Parameters
    ----------
    solvent : Solvent
        Enum value identifying the solvent.
    config : SimulationConfig
        Global simulation configuration.
    seed : int, optional
        Random seed used for initial velocities (default ``0``).

    Returns
    -------
    Tuple[System, Topology, list]
        The OpenMM ``System``, the corresponding ``Topology`` and a list of
        ``Position`` objects (in OpenMM units) ready for a ``Simulation``.
    """
    logger.info(f"Building {solvent.value} system (seed={seed})")

    # Load the appropriate force field
    forcefield = _load_forcefield(solvent)

    # Create an empty modeller – ``addSolvent`` will fill the box.
    modeller = app.Modeller(app.Topology(), [])
    box_size = config.box_size * unit.nanometers
    logger.debug(f"Requested box size: {box_size}")

    # Populate the box with solvent molecules.  ``addSolvent`` uses the
    # force field to generate a reasonable number of molecules (≈150 for a
    # 5 nm box with water).
    modeller.addSolvent(
        forcefield,
        model="tip3p",
        boxSize=box_size,
        neutralize=False,
    )
    logger.info(
        f"Generated {len(modeller.topology.atoms())} atoms "
        f"({len(modeller.topology.residues())} molecules)."
    )

    # Create the system from the topology and force field.
    system = forcefield.createSystem(
        modeller.topology,
        nonbondedMethod=app.PME,
        nonbondedCutoff=1.0 * unit.nanometers,
        constraints=app.HBonds,
    )
    logger.debug("System creation complete.")

    # Set the random seed for the integrator later (handled in run_simulation).
    # Return the OpenMM objects.
    return system, modeller.topology, modeller.positions
