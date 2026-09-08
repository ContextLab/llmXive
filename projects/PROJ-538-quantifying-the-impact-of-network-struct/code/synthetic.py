import numpy as np
import ase
from ase.build import fcc111
from ase.md.verlet import VelocityVerlet
from ase.md.nvt import NVT
from ase.units import fs, eV, K, Bohr
from typing import List, Dict, Any, Optional, Tuple
import json
from pathlib import Path
from .models import AtomicSnapshot
from .utils import get_logger, DataAvailabilityError

logger = get_logger(__name__)

class ThermalConductivityEstimator:
    """
    Estimates thermal conductivity using the Callaway phonon-scattering model.
    
    This model calculates conductivity based on intrinsic phonon properties and
    scattering mechanisms (point defects, grain boundaries, etc.), strictly
    avoiding any dependence on the defect network graph metrics to prevent
    tautological correlation.
    
    The Callaway model (simplified):
    k = (k_B / (2 * pi^2 * v)) * (k_B * T / h)^3 * integral(
        (tau * x^4 * e^x) / (e^x - 1)^2 dx
    )
    where x = h*omega / (k_B * T)
    
    For this implementation, we use a simplified analytical approximation
    based on defect density and mass difference scattering rates.
    """
    
    def __init__(self, 
                 temperature: float = 300.0, 
                 velocity_sound: float = 3000.0,  # m/s
                 specific_heat: float = 3.0 * 1.38e-23,  # J/K/atom (Dulong-Petit approx)
                 Debye_temperature: float = 300.0):
        """
        Initialize the estimator with physical parameters.
        
        Args:
            temperature: Temperature in Kelvin
            velocity_sound: Speed of sound in the material (m/s)
            specific_heat: Specific heat per atom (J/K)
            Debye_temperature: Debye temperature for the material (K)
        """
        self.temperature = temperature
        self.velocity_sound = velocity_sound
        self.specific_heat = specific_heat
        self.Debye_temperature = Debye_temperature
        
        # Physical constants
        self.k_B = 1.380649e-23  # Boltzmann constant (J/K)
        self.h = 6.62607015e-34  # Planck constant (J*s)
        self.hbar = self.h / (2 * np.pi)
        
        # Scattering parameters (to be set based on snapshot)
        self.point_defect_scattering_rate = 0.0
        self.grain_boundary_scattering_rate = 0.0
        self.umklapp_scattering_rate = 0.0
        
    def calculate_mass_difference_scattering(self, 
                                             snapshot: AtomicSnapshot,
                                             isotope_factor: float = 1.0) -> float:
        """
        Calculate the scattering rate due to mass difference (point defects).
        
        Based on Klemens' theory for isotopic/point defect scattering:
        Gamma = sum_i (f_i * (1 - M_i/M_avg)^2)
        where f_i is the fraction of species i, M_i is its mass, M_avg is average mass.
        
        Args:
            snapshot: The atomic snapshot containing species and positions
            isotope_factor: Factor to scale the scattering (default 1.0)
            
        Returns:
            Scattering rate parameter (s^-1)
        """
        if not snapshot.species or len(snapshot.species) == 0:
            logger.warning("Empty species list in snapshot")
            return 0.0
            
        # Atomic masses in kg (approximate values for Cu, Ni, Au, Ag)
        masses = {
            'Cu': 63.546 * 1.660539e-27,
            'Ni': 58.693 * 1.660539e-27,
            'Au': 196.967 * 1.660539e-27,
            'Ag': 107.868 * 1.660539e-27
        }
        
        # Calculate average mass
        total_mass = 0.0
        species_counts = {}
        for sp in snapshot.species:
            mass = masses.get(sp, 50.0 * 1.660539e-27)  # fallback mass
            total_mass += mass
            species_counts[sp] = species_counts.get(sp, 0) + 1
            
        n_atoms = len(snapshot.species)
        avg_mass = total_mass / n_atoms if n_atoms > 0 else 1.0
        
        # Calculate Gamma parameter (mass variance)
        gamma = 0.0
        for sp, count in species_counts.items():
            mass = masses.get(sp, 50.0 * 1.660539e-27)
            fraction = count / n_atoms
            gamma += fraction * ((1 - mass / avg_mass) ** 2)
        
        # Scattering rate: tau^-1 = Gamma * omega^4
        # We use a representative frequency (Debye frequency)
        omega_D = self.k_B * self.Debye_temperature / self.hbar
        scattering_rate = isotope_factor * gamma * (omega_D ** 4) * (1e-40)  # scaling factor
        
        logger.debug(f"Mass difference scattering rate: {scattering_rate:.2e} s^-1")
        return scattering_rate
        
    def calculate_defect_density_scattering(self, 
                                            snapshot: AtomicSnapshot,
                                            defect_area: float = 1e-12) -> float:
        """
        Calculate scattering rate due to defect density (grain boundaries).
        
        Uses a simplified model where scattering rate is proportional to
        defect density and inverse of mean free path.
        
        Args:
            snapshot: The atomic snapshot
            defect_area: Average defect cross-section area (m^2)
            
        Returns:
            Scattering rate parameter (s^-1)
        """
        # Estimate defect density from snapshot (simplified)
        # In a real implementation, this would come from the DefectGraph
        # Here we use a proxy based on species disorder
        if not snapshot.species or len(snapshot.species) < 2:
            return 0.0
            
        # Simple disorder metric: fraction of minority species
        species_counts = {}
        for sp in snapshot.species:
            species_counts[sp] = species_counts.get(sp, 0) + 1
        
        n_atoms = len(snapshot.species)
        max_count = max(species_counts.values())
        disorder_metric = 1.0 - (max_count / n_atoms)
        
        # Scattering rate proportional to disorder and defect area
        # tau^-1 = v / l, where l ~ 1/(n_defect * sigma)
        defect_density = disorder_metric * n_atoms / (snapshot.volume * 1e-30)  # m^-3
        mean_free_path = 1.0 / (defect_density * defect_area) if defect_density > 0 else 1e9
        
        scattering_rate = self.velocity_sound / mean_free_path
        
        logger.debug(f"Defect density scattering rate: {scattering_rate:.2e} s^-1")
        return scattering_rate
        
    def calculate_umklapp_scattering(self) -> float:
        """
        Calculate Umklapp phonon-phonon scattering rate.
        
        Uses a simplified temperature-dependent model:
        tau_U^-1 = A * T * exp(-Theta_D / bT)
        
        Returns:
            Scattering rate parameter (s^-1)
        """
        A = 1e-18  # Material-dependent constant
        b = 3.0    # Typical value
        
        if self.temperature <= 0:
            return 0.0
            
        scattering_rate = A * self.temperature * np.exp(-self.Debye_temperature / (b * self.temperature))
        
        logger.debug(f"Umklapp scattering rate: {scattering_rate:.2e} s^-1")
        return scattering_rate
        
    def estimate_conductivity(self, snapshot: AtomicSnapshot) -> float:
        """
        Estimate thermal conductivity using the Callaway model.
        
        This method combines all scattering mechanisms and computes the
        effective thermal conductivity without using any graph metrics.
        
        Args:
            snapshot: The atomic snapshot containing species and coordinates
            
        Returns:
            Estimated thermal conductivity in W/(m*K)
        """
        # Calculate individual scattering rates
        mass_scatter = self.calculate_mass_difference_scattering(snapshot)
        defect_scatter = self.calculate_defect_density_scattering(snapshot)
        umklapp_scatter = self.calculate_umklapp_scattering()
        
        # Total scattering rate (Matthiessen's rule)
        total_scatter = mass_scatter + defect_scatter + umklapp_scatter
        
        if total_scatter <= 0:
            logger.warning("Zero or negative total scattering rate, using fallback")
            total_scatter = 1e10  # Fallback to avoid division by zero
            
        # Calculate mean free path
        mean_free_path = self.velocity_sound / total_scatter
        
        # Limit mean free path to system size
        if snapshot.volume > 0:
            system_size = (snapshot.volume * 1e-30) ** (1/3)
            mean_free_path = min(mean_free_path, system_size)
        
        # Calculate thermal conductivity using kinetic theory
        # k = (1/3) * C * v * l
        # where C is heat capacity per unit volume
        n_atoms = len(snapshot.species) if snapshot.species else 0
        volume_m3 = snapshot.volume * 1e-30 if snapshot.volume > 0 else 1e-30
        
        if volume_m3 <= 0 or n_atoms <= 0:
            logger.error("Invalid volume or atom count")
            return 0.0
            
        heat_capacity_per_volume = (n_atoms * self.specific_heat) / volume_m3
        
        conductivity = (1/3) * heat_capacity_per_volume * self.velocity_sound * mean_free_path
        
        # Clamp to physically reasonable values (0.1 - 1000 W/mK)
        conductivity = max(0.1, min(1000.0, conductivity))
        
        logger.info(f"Estimated conductivity: {conductivity:.3f} W/(m*K)")
        return conductivity
        
    def estimate_conductivity_batch(self, snapshots: List[AtomicSnapshot]) -> List[float]:
        """
        Estimate conductivity for a batch of snapshots.
        
        Args:
            snapshots: List of atomic snapshots
            
        Returns:
            List of estimated conductivities
        """
        results = []
        for i, snapshot in enumerate(snapshots):
            try:
                k = self.estimate_conductivity(snapshot)
                results.append(k)
                logger.info(f"Snapshot {i}: k = {k:.3f} W/(m*K)")
            except Exception as e:
                logger.error(f"Failed to estimate conductivity for snapshot {i}: {e}")
                results.append(np.nan)
                
        return results

def run_synthetic_generation():
    """
    Main function to run synthetic data generation and conductivity estimation.
    
    This function:
    1. Generates synthetic snapshots using SyntheticDataGenerator
    2. Estimates thermal conductivity for each snapshot using Callaway model
    3. Saves results to data/processed/synthetic_conductivity.json
    
    Returns:
        Dict containing generation results and conductivity estimates
    """
    from .synthetic import SyntheticDataGenerator
    
    logger.info("Starting synthetic generation and conductivity estimation")
    
    # Generate synthetic data
    generator = SyntheticDataGenerator()
    snapshots = generator.generate_snapshots(n_snapshots=50, seed_start=0)
    
    if not snapshots:
        raise DataAvailabilityError("Failed to generate synthetic snapshots")
        
    logger.info(f"Generated {len(snapshots)} snapshots")
    
    # Estimate conductivity
    estimator = ThermalConductivityEstimator()
    conductivities = estimator.estimate_conductivity_batch(snapshots)
    
    # Prepare results
    results = {
        "n_snapshots": len(snapshots),
        "conductivities": conductivities,
        "temperature_K": estimator.temperature,
        "Debye_temperature_K": estimator.Debye_temperature,
        "velocity_sound_m_s": estimator.velocity_sound
    }
    
    # Save results
    output_path = Path("data/processed/synthetic_conductivity.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {output_path}")
    return results

if __name__ == "__main__":
    run_synthetic_generation()