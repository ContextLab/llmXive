"""
Task T014: McLean Isotherm Model Implementation.

Calculates equilibrium concentrations from segregation energy and bulk composition.
"""
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from code.config import get_logger

logger = get_logger(__name__)

@dataclass
class McLeanResult:
    """Result of a McLean isotherm calculation."""
    equilibrium_concentration: float
    saturation_flag: bool
    profile: List[float]  # Concentrations at different distances (optional/derived)
    
    def to_dict(self) -> Dict:
        return {
            "equilibrium_concentration": self.equilibrium_concentration,
            "saturation_flag": self.saturation_flag,
            "profile": self.profile
        }

def validate_mclean_inputs(
    segregation_energy_eV: float,
    bulk_concentration: float,
    temperature_K: float
) -> None:
    """Validate inputs for McLean calculation."""
    if not isinstance(segregation_energy_eV, (int, float)):
        raise TypeError("segregation_energy_eV must be a number")
    if not (0.0 <= bulk_concentration <= 1.0):
        raise ValueError("bulk_concentration must be between 0.0 and 1.0")
    if temperature_K <= 0:
        raise ValueError("temperature_K must be positive")

def calculate_mclean_concentration(
    segregation_energy_eV: float,
    bulk_concentration: float,
    temperature_K: float,
    k_B: float = 8.617333262e-5  # Boltzmann constant in eV/K
) -> McLeanResult:
    """
    Calculate equilibrium concentration at the grain boundary using the McLean isotherm.
    
    Equation: 
    X_gb = (X_bulk * exp(ΔE / k_B * T)) / (1 - X_bulk + X_bulk * exp(ΔE / k_B * T))
    
    Where:
      X_gb: Grain boundary concentration
      X_bulk: Bulk concentration
      ΔE: Segregation energy (negative for segregation, positive for depletion)
      k_B: Boltzmann constant
      T: Temperature in Kelvin
    
    Note: In many contexts, segregation energy is defined as E_bulk - E_gb.
    If E_gb < E_bulk (favorable segregation), ΔE is positive.
    If the input `segregation_energy_eV` is E_gb - E_bulk (negative for segregation),
    we must use -segregation_energy_eV in the exponent.
    
    Assumption for this pipeline: `segregation_energy_eV` is the energy gain (positive for segregation).
    If the source data provides binding energy (positive), we use it directly.
    """
    validate_mclean_inputs(segregation_energy_eV, bulk_concentration, temperature_K)
    
    # Calculate the exponential term
    # exp(ΔE / k_B * T)
    exponent = (segregation_energy_eV) / (k_B * temperature_K)
    
    # Prevent overflow for very large exponents
    if exponent > 700: # exp(700) is near float max
        logger.warning(f"Exponent too large ({exponent}), capping at saturation.")
        return McLeanResult(
            equilibrium_concentration=1.0,
            saturation_flag=True,
            profile=[1.0]
        )
        
    exp_term = math.exp(exponent)
    
    numerator = bulk_concentration * exp_term
    denominator = (1.0 - bulk_concentration) + numerator
    
    if denominator == 0:
        # Should not happen if bulk_concentration < 1, but handle anyway
        equilibrium_conc = 1.0
        saturation = True
    else:
        equilibrium_conc = numerator / denominator
        saturation = False
        
    # Cap at 1.0 just in case of floating point errors
    if equilibrium_conc > 1.0:
        equilibrium_conc = 1.0
        saturation = True
        
    logger.debug(f"Calculated segregation energy: {segregation_energy_eV} eV")
    logger.debug("Applied McLean isotherm")
    logger.debug(f"Equilibrium concentration: {equilibrium_conc}")
    logger.debug(f"Saturation flag: {saturation}")
    
    # Generate a simple profile (e.g., constant at GB, decaying to bulk)
    # For this task, we just return the equilibrium concentration as the profile value
    # or a simple list representing the GB site.
    profile = [equilibrium_conc] 
    
    return McLeanResult(
        equilibrium_concentration=equilibrium_conc,
        saturation_flag=saturation,
        profile=profile
    )

def calculate_mclean_profile(
    segregation_energy_eV: float,
    bulk_concentration: float,
    temperature_K: float
) -> McLeanResult:
    """
    Wrapper to calculate the profile (concentration at the boundary).
    """
    return calculate_mclean_concentration(segregation_energy_eV, bulk_concentration, temperature_K)