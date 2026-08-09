"""
McLean Isotherm Model Implementation for Grain Boundary Segregation.

This module implements the McLean equilibrium segregation model to calculate
grain boundary concentrations from segregation energies and bulk compositions.
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from errors import ConfigurationError, ValidationError

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class McLeanResult:
    """
    Container for McLean isotherm calculation results.

    Attributes:
        bulk_composition: Bulk atomic fraction of solute.
        gb_concentration: Calculated grain boundary atomic fraction of solute.
        segregation_energy: Input segregation energy in eV.
        temperature: Input temperature in Kelvin.
        is_saturated: Boolean flag indicating if GB concentration reached saturation (1.0).
        saturation_level: The theoretical maximum concentration (usually 1.0 or site fraction).
    """
    bulk_composition: float
    gb_concentration: float
    segregation_energy: float
    temperature: float
    is_saturated: bool = False
    saturation_level: float = 1.0
    warning_messages: List[str] = field(default_factory=list)

def calculate_mclean_concentration(
    bulk_composition: float,
    segregation_energy: float,
    temperature: float,
    gas_constant: float = 8.314462618,
    max_concentration: float = 1.0
) -> McLeanResult:
    """
    Calculate equilibrium grain boundary concentration using the McLean isotherm.

    The McLean equation relates bulk concentration (X_bulk), grain boundary concentration
    (X_gb), segregation energy (Delta_E_seg), and temperature (T):

        X_gb / (1 - X_gb) = (X_bulk / (1 - X_bulk)) * exp(-Delta_E_seg / (R * T))

    Where:
        - Delta_E_seg is in eV (converted to J/mol for calculation) or consistent units.
        - R is the gas constant (8.314 J/(mol*K)).
        - T is temperature in Kelvin.

    Args:
        bulk_composition: Bulk atomic fraction of the solute (0.0 to 1.0).
        segregation_energy: Segregation energy in eV. Negative values indicate
                            favorable segregation.
        temperature: Temperature in Kelvin.
        gas_constant: Gas constant R in J/(mol*K).
        max_concentration: Maximum possible concentration at the boundary (default 1.0).

    Returns:
        McLeanResult object containing the calculated values and status flags.

    Raises:
        ConfigurationError: If inputs are physically invalid (e.g., T <= 0, X_bulk < 0).
        ValidationError: If calculation results in NaN or invalid states.
    """
    # Input Validation
    if temperature <= 0:
        raise ConfigurationError(f"Temperature must be positive, got {temperature} K")

    if not (0.0 <= bulk_composition <= 1.0):
        raise ConfigurationError(
            f"Bulk composition must be between 0 and 1, got {bulk_composition}"
        )

    if bulk_composition <= 0:
        # If bulk composition is 0, GB concentration should be 0 (no solute to segregate)
        logger.debug(f"Bulk composition is zero. Setting GB concentration to 0.")
        return McLeanResult(
            bulk_composition=0.0,
            gb_concentration=0.0,
            segregation_energy=segregation_energy,
            temperature=temperature
        )

    if bulk_composition >= 1.0:
        # If bulk is pure solute, GB is pure solute
        logger.debug(f"Bulk composition is 1.0. Setting GB concentration to 1.0.")
        return McLeanResult(
            bulk_composition=1.0,
            gb_concentration=1.0,
            segregation_energy=segregation_energy,
            temperature=temperature
        )

    # Constants
    # 1 eV = 96.485 kJ/mol = 96485 J/mol
    eV_to_J_per_mol = 96485.33212
    delta_g = segregation_energy * eV_to_J_per_mol  # J/mol

    # Calculate the exponential term: exp(-Delta_E_seg / (R * T))
    # Note: In McLean's original formulation, if E_seg is negative (favorable),
    # the exponent becomes positive, increasing the ratio.
    try:
        exponent_arg = -delta_g / (gas_constant * temperature)
        # Handle potential overflow for large negative energies at low T
        if exponent_arg > 700:
            logger.warning(f"Exponent overflow risk: {exponent_arg}. Capping to prevent overflow.")
            exp_term = np.exp(700)
        elif exponent_arg < -700:
            exp_term = 0.0
        else:
            exp_term = math.exp(exponent_arg)
    except OverflowError:
        logger.error(f"Overflow in exponential calculation for E_seg={segregation_energy}, T={temperature}")
        raise ConfigurationError("Exponential overflow in McLean calculation.")

    # McLean Equation:
    # X_gb / (1 - X_gb) = (X_bulk / (1 - X_bulk)) * K
    # Let K_eq = (X_bulk / (1 - X_bulk)) * exp_term
    # X_gb = K_eq / (1 + K_eq)

    bulk_ratio = bulk_composition / (1.0 - bulk_composition)
    k_eq = bulk_ratio * exp_term

    # Solve for X_gb
    if k_eq <= 0:
        gb_concentration = 0.0
    else:
        gb_concentration = k_eq / (1.0 + k_eq)

    # Validation: Check for NaN or Inf
    if math.isnan(gb_concentration) or math.isinf(gb_concentration):
        raise ValidationError(f"Invalid concentration calculated: {gb_concentration}")

    # Saturation Logic (T016 requirement)
    # Cap at max_concentration and flag saturation
    is_saturated = False
    warning_messages = []

    if gb_concentration > max_concentration:
        warning_msg = f"Calculated GB concentration ({gb_concentration:.4f}) exceeds max ({max_concentration}). Capping at {max_concentration}."
        logger.warning(warning_msg)
        gb_concentration = max_concentration
        is_saturated = True
        warning_messages.append(warning_msg)

    # Log specific saturation event if applicable
    if is_saturated:
        logger.info(f"Saturation detected for E_seg={segregation_energy:.3f} eV at T={temperature} K. "
                    f"Concentration capped at {max_concentration}.")

    return McLeanResult(
        bulk_composition=bulk_composition,
        gb_concentration=gb_concentration,
        segregation_energy=segregation_energy,
        temperature=temperature,
        is_saturated=is_saturated,
        saturation_level=max_concentration,
        warning_messages=warning_messages
    )

def calculate_mclean_profile(
    bulk_compositions: List[float],
    segregation_energy: float,
    temperature: float,
    max_concentration: float = 1.0
) -> List[McLeanResult]:
    """
    Calculate McLean concentrations for a range of bulk compositions.

    Args:
        bulk_compositions: List of bulk atomic fractions.
        segregation_energy: Segregation energy in eV.
        temperature: Temperature in Kelvin.
        max_concentration: Maximum possible concentration at the boundary.

    Returns:
        List of McLeanResult objects.
    """
    results = []
    for x_bulk in bulk_compositions:
        try:
            result = calculate_mclean_concentration(
                bulk_composition=x_bulk,
                segregation_energy=segregation_energy,
                temperature=temperature,
                max_concentration=max_concentration
            )
            results.append(result)
        except (ConfigurationError, ValidationError) as e:
            logger.error(f"Failed to calculate for bulk_composition={x_bulk}: {e}")
            # Optionally append a failed result or skip
            # For this implementation, we skip invalid points to maintain list integrity
            # or could return a specific error marker.
            continue
    return results

def validate_mclean_inputs(
    bulk_composition: float,
    segregation_energy: float,
    temperature: float
) -> Tuple[bool, List[str]]:
    """
    Validate inputs for McLean calculation before execution.

    Returns:
        Tuple of (is_valid, list_of_warnings).
    """
    warnings = []
    is_valid = True

    if not (0.0 <= bulk_composition <= 1.0):
        is_valid = False
        warnings.append(f"Invalid bulk composition: {bulk_composition}")

    if temperature <= 0:
        is_valid = False
        warnings.append(f"Invalid temperature: {temperature}")

    # Log warnings for extreme energies that might indicate data issues
    if abs(segregation_energy) > 5.0:
        warnings.append(f"Large segregation energy magnitude: {segregation_energy} eV. "
                        "Check source data for validity.")

    return is_valid, warnings

# Example usage / simple CLI for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running McLean Model Self-Test...")

    # Test Case 1: Standard Fe-Cr scenario (approx)
    # E_seg ~ -0.5 eV (favorable), T=900K, X_bulk=0.1
    res1 = calculate_mclean_concentration(
        bulk_composition=0.1,
        segregation_energy=-0.5,
        temperature=900.0
    )
    logger.info(f"Test 1 (Fe-Cr approx): X_bulk=0.1, E_seg=-0.5eV, T=900K -> X_gb={res1.gb_concentration:.4f}")

    # Test Case 2: Saturation check
    # Very favorable energy
    res2 = calculate_mclean_concentration(
        bulk_composition=0.01,
        segregation_energy=-2.0,
        temperature=300.0
    )
    logger.info(f"Test 2 (Saturation check): X_bulk=0.01, E_seg=-2.0eV, T=300K -> X_gb={res2.gb_concentration:.4f}, Saturated={res2.is_saturated}")

    # Test Case 3: Unfavorable segregation
    res3 = calculate_mclean_concentration(
        bulk_composition=0.1,
        segregation_energy=0.5,
        temperature=900.0
    )
    logger.info(f"Test 3 (Unfavorable): X_bulk=0.1, E_seg=0.5eV, T=900K -> X_gb={res3.gb_concentration:.4f}")

    logger.info("McLean Model Self-Test Complete.")
