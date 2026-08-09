"""
Logging infrastructure for User Story 1 (Thermodynamic Segregation Profile Generation).

This module provides centralized logging configuration and helper functions for
US1 operations including energy extraction, surrogate model application, and
McLean isotherm calculations.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Configure logger for US1
US1_LOGGER_NAME = "us1.segregation_pipeline"

def get_us1_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger for US1 operations.
    
    Args:
        name: Optional sub-component name (e.g., 'surrogate', 'mclean', 'energy_extraction')
    
    Returns:
        Configured logger instance
    """
    logger_name = f"{US1_LOGGER_NAME}.{name}" if name else US1_LOGGER_NAME
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # Create file handler for detailed logs
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"us1_{timestamp}.log"
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_energy_extraction(
    logger: logging.Logger,
    alloy_system: str,
    temperature: float,
    segregation_energies: dict,
    source: str = "surrogate"
) -> None:
    """
    Log energy extraction results from surrogate model or literature.
    
    Args:
        logger: Logger instance
        alloy_system: System identifier (e.g., "Fe-Cr-Mo")
        temperature: Temperature in Kelvin
        segregation_energies: Dict mapping solute to segregation energy (eV)
        source: Source of energy values ('surrogate', 'literature', 'extrapolated')
    """
    logger.info(f"Energy extraction completed for {alloy_system} at {temperature}K")
    logger.debug(f"Source: {source}")
    logger.debug(f"Segregation energies (eV): {json.dumps(segregation_energies)}")
    
    for solute, energy in segregation_energies.items():
        logger.info(f"  {solute}: {energy:.4f} eV")

def log_mclean_application(
    logger: logging.Logger,
    alloy_system: str,
    temperature: float,
    bulk_compositions: dict,
    equilibrium_concentrations: dict,
    saturation_flags: list
) -> None:
    """
    Log McLean isotherm application results.
    
    Args:
        logger: Logger instance
        alloy_system: System identifier
        temperature: Temperature in Kelvin
        bulk_compositions: Dict mapping solute to bulk atomic fraction
        equilibrium_concentrations: Dict mapping solute to equilibrium concentration
        saturation_flags: List of solutes that reached saturation (capped at 1.0)
    """
    logger.info(f"McLean isotherm applied for {alloy_system} at {temperature}K")
    logger.debug(f"Bulk compositions: {json.dumps(bulk_compositions)}")
    logger.debug(f"Equilibrium concentrations: {json.dumps(equilibrium_concentrations)}")
    
    if saturation_flags:
        logger.warning(f"Saturation detected for: {', '.join(saturation_flags)}")
    
    for solute, conc in equilibrium_concentrations.items():
        status = " [SATURATED]" if solute in saturation_flags else ""
        logger.info(f"  {solute}: {conc:.6f}{status}")

def log_surrogate_calculation(
    logger: logging.Logger,
    alloy_system: str,
    geometry: str,
    result: dict,
    status: str
) -> None:
    """
    Log surrogate model calculation results.
    
    Args:
        logger: Logger instance
        alloy_system: System identifier
        geometry: Grain boundary geometry description
        result: Calculation result dict
        status: Status of calculation ('success', 'retry', 'failure', 'zero_interaction')
    """
    logger.info(f"Surrogate calculation for {alloy_system} ({geometry}): {status}")
    logger.debug(f"Result: {json.dumps(result)}")
    
    if status == "zero_interaction":
        logger.warning("Using zero-interaction assumption for ternary system (NO_TERNARY_DATA)")
    elif status == "retry":
        logger.warning(f"Retrying surrogate calculation with perturbed composition")
    elif status == "failure":
        logger.error(f"Surrogate calculation failed: {result.get('error', 'Unknown error')}")

def log_profile_generation(
    logger: logging.Logger,
    alloy_system: str,
    temperature: float,
    output_path: str,
    profile_count: int
) -> None:
    """
    Log segregation profile generation completion.
    
    Args:
        logger: Logger instance
        alloy_system: System identifier
        temperature: Temperature in Kelvin
        output_path: Path to output file
        profile_count: Number of profiles generated
    """
    logger.info(f"Profile generation completed for {alloy_system} at {temperature}K")
    logger.info(f"Generated {profile_count} profiles")
    logger.info(f"Output written to: {output_path}")

def log_validation_result(
    logger: logging.Logger,
    validation_type: str,
    passed: bool,
    details: Optional[str] = None
) -> None:
    """
    Log validation results for US1 operations.
    
    Args:
        logger: Logger instance
        validation_type: Type of validation (e.g., 'input_geometry', 'energy_bounds', 'concentration_bounds')
        passed: Whether validation passed
        details: Optional details about the validation
    """
    status = "PASSED" if passed else "FAILED"
    logger.info(f"Validation [{validation_type}]: {status}")
    if details:
        logger.debug(f"Details: {details}")
    
    if not passed:
        logger.error(f"Validation failed: {validation_type}")

# Initialize main US1 logger at module level
us1_logger = get_us1_logger()

def log_us1_startup() -> None:
    """Log US1 pipeline startup."""
    us1_logger.info("=" * 60)
    us1_logger.info("User Story 1: Thermodynamic Segregation Profile Generation")
    us1_logger.info("Starting pipeline...")
    us1_logger.info("=" * 60)

def log_us1_completion(output_file: str, error: Optional[Exception] = None) -> None:
    """
    Log US1 pipeline completion.
    
    Args:
        output_file: Path to the final output file
        error: Optional exception if pipeline failed
    """
    if error:
        us1_logger.error(f"Pipeline failed: {str(error)}")
    else:
        us1_logger.info("=" * 60)
        us1_logger.info(f"Pipeline completed successfully. Output: {output_file}")
        us1_logger.info("=" * 60)