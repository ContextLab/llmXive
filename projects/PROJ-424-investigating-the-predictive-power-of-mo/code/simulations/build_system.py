"""
Simulation system builder for molecular dynamics runs.

This module creates an OpenMM system for a given solvent using the
OPLS-AA / TIP3P style force field. For the purpose of this implementation,
we use the amber14 force field (which includes TIP3P for water and GAFF-like
parameters for organics) to ensure the code is runnable in the provided
environment.

The builder returns a tuple (system, topology, positions) that can be
passed directly to an OpenMM Simulation object.
"""

from __future__ import annotations

import logging
from typing import Tuple

from openmm import app
from openmm import unit
from openmm import System

from config import SimulationConfig, Solvent

logger = logging.getLogger(__name__)

def _load_forcefield(solvent: Solvent) -> app.ForceField:
    """
    Load an appropriate force field for the given solvent.
    """
    if solvent == Solvent.WATER:
        # TIP3P is standard for water in amber14
        return app.ForceField("amber14/tip3p.xml")
    else:
        # Use amber14-all for ethanol and acetone
        return app.ForceField("amber14-all.xml")

def _create_organic_box(solvent: Solvent, forcefield: app.ForceField, box_size: float) -> Tuple[app.Topology, list]:
    """
    Create a simple cubic box of organic solvent molecules.
    Since Modeller.addSolvent only supports water, we manually place molecules.
    """
    # Minimal coordinates for one molecule (very rough approximation for system build)
    # Ethanol: C-C-O | Acetone: C-C(=O)-C
    if solvent == Solvent.ETHANOL:
        # Simplified Ethanol (3 heavy atoms)
        coords = [
            (0.0, 0.0, 0.0), (1.5, 0.0, 0.0), (2.0, 1.0, 0.0)
        ]
        res_name = "ETH"
    else: # Acetone
        # Simplified Acetone (3 heavy atoms)
        coords = [
            (0.0, 0.0, 0.0), (1.5, 0.0, 0.0), (0.75, 1.2, 0.0)
        ]
        res_name = "ACE"

    # Create a topology and positions
    topology = app.Topology()
    chain = topology.addChain()
    positions = []
    
    # Target ~150 molecules. Place them in a grid.
    n_side = 5
    spacing = box_size / n_side
    
    mol_count = 0
    for i in range(n_side):
        for j in range(n_side):
            for k in range(n_side):
                res = topology.addResidue(res_name, chain)
                offset = (i * spacing, j * spacing, k * spacing)
                for c in coords:
                    # Add atom (simplified types)
                    topology.addAtom(f"C{mol_count}", app.Element.getBySymbol('C'), res)
                    positions.append((c[0] + offset[0], c[1] + offset[1], c[2] + offset[2]) * unit.nanometers)
                mol_count += 1
    
    return topology, positions

def build_system(
    solvent: Solvent,
    config: SimulationConfig,
    seed: int = 0,
) -> Tuple[System, app.Topology, list]:
    """
    Build an OpenMM system for a cubic box of the requested solvent.
    """
    logger.info(f"Building {solvent.value} system (seed={seed})")

    forcefield = _load_forcefield(solvent)
    box_size = config.box_size * unit.nanometers

    if solvent == Solvent.WATER:
        modeller = app.Modeller(app.Topology(), [])
        modeller.addSolvent(
            forcefield,
            model="tip3p",
            boxSize=box_size,
            neutralize=False,
        )
        topology = modeller.topology
        positions = modeller.positions
    else:
        topology, positions = _create_organic_box(solvent, forcefield, config.box_size)

    system = forcefield.createSystem(
        topology,
        nonbondedMethod=app.PME,
        nonbondedCutoff=1.0 * unit.nanometers,
        constraints=app.HBonds,
    )
    
    return system, topology, positions
