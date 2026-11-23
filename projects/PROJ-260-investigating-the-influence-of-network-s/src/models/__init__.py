"""
Models Package.

Contains data classes and graph representations for atomic simulations:
- SimulationBox: Atomic positions, velocities, and metadata.
- BondNetwork: Graph representation of atomic bonds.
- VibrationalSpectrum: VDOS and participation ratio data.
"""
from src.models.simulation_box import SimulationBox
from src.models.bond_network import BondNetwork
from src.models.vibrational_spectrum import VibrationalSpectrum

__all__ = ["SimulationBox", "BondNetwork", "VibrationalSpectrum"]
