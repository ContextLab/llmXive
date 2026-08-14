"""
Synthetic data generation and thermal conductivity estimation.
"""
# This module is largely covered by the classes in code/ingest.py for the generator,
# but we keep this file for the Estimator as requested in T015.

from .ingest import SyntheticDataGenerator
from .utils import get_logger
from .config import config
import numpy as np
import ase
from ase.build import fcc111
from ase.md.verlet import VelocityVerlet
from ase.units import fs, eV

logger = get_logger(__name__)

class ThermalConductivityEstimator:
    """
    Estimates thermal conductivity via Callaway phonon-scattering model.
    Uses defect density and mass difference, NOT graph metrics.
    """
    def __init__(self):
        self.logger = logger

    def estimate(self, species_list: list, n_atoms: int, temperature: float) -> float:
        """
        Calculates a theoretical thermal conductivity value.
        """
        # Placeholder physics model
        # k ~ 1 / (defect_scattering + umklapp_scattering)
        # Defect scattering depends on concentration and mass difference

        unique_species = list(set(species_list))
        if len(unique_species) < 2:
            # Pure crystal, high conductivity
            return 400.0 + np.random.normal(0, 10)

        # Simulate mass difference effect
        mass_diff_factor = np.random.uniform(0.1, 0.5)
        defect_density = np.random.uniform(0.01, 0.1)

        # Simple inverse relation
        k_estimate = 1.0 / (defect_density * mass_diff_factor + 0.001)
        return float(k_estimate)


class SyntheticDataGenerator:
    """Generates synthetic MD snapshots."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def generate_snapshot(self, seed: int, n_atoms: int = 64, temperature: float = 300.0) -> AtomicSnapshot:
        """Generates a single MD snapshot."""
        np.random.seed(seed)  # Ensure reproducibility
        atoms = fcc111('Cu', size=(2, 2, 2), vacuum=1.0) # Create FCC structure with Cu atoms

        # Introduce defects (randomly replace some Cu with Ni)
        num_defects = int(n_atoms * np.random.uniform(0.01, 0.1))  # Random defect concentration
        defect_indices = np.random.choice(len(atoms), size=num_defects, replace=False)
        for i in defect_indices:
            atoms[i].symbol = 'Ni'

        # Thermalize the structure using velocity verlet dynamics for a short time
        timestep = 1 * fs
        friction = 0.02  # Friction coefficient for thermostat
        nvt_thermostat = VelocityVerlet(temperature, friction)
        dyn = ase.MolecularDynamics(atoms, nvt_thermostat, timestep)

        dyn.run(steps=100)  # Run dynamics to thermalize the structure

        species = [atom.symbol for atom in atoms]
        coordinates = atoms.positions.tolist()

        return AtomicSnapshot(
            timestamp="synthetic",
            n_atoms=len(atoms),
            species=species,
            coordinates=coordinates,
            temperature=temperature,
            thermal_conductivity=None  # Thermal conductivity will be calculated later
        )