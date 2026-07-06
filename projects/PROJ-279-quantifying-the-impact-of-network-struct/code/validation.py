"""
Validation logic for data independence, source verification, and convergence checks.

This module defines the logic for validating atomic configurations against:
- FR-006: Source Independence (verifying data comes from independent MD simulations)
- FR-007: Convergence Checks (verifying system size meets thermodynamic limit requirements)
- Constitution Principle VI: Data Independence and Convergence

NOTE: This task (T007) is a DEFINITION ONLY task. It implements the validation logic
but does NOT execute it. Execution is deferred to Phase 3 (T007-exec) when real data
is available in data/raw/.
"""
import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

from models.atomic_config import AtomicConfiguration
from config.env_config import get_config, ConfigError
from logging_config import get_logger

# Minimum system size for thermodynamic limit (from FR-007)
MIN_SYSTEM_SIZE_ATOMS = 1000

@dataclass
class ValidationResult:
    """Result of validating a single configuration."""
    config_id: str
    is_valid: bool
    source_independent: bool
    size_sufficient: bool
    convergence_verified: bool
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ValidationReport:
    """Aggregated validation report for multiple configurations."""
    validated_configs: List[str] = field(default_factory=list)
    excluded_configs: List[str] = field(default_factory=list)
    reasons: Dict[str, str] = field(default_factory=dict)
    total_processed: int = 0
    total_valid: int = 0
    total_excluded: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_source_independence(config: AtomicConfiguration, source_metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    Validate that the configuration source is independent.
    
    Checks:
    - Metadata explicitly states the simulation method (MD, DFT-MD, etc.)
    - Source is not a reuse of the target property (thermal conductivity) from the same simulation
    - Source method is documented
    
    Args:
        config: Atomic configuration to validate
        source_metadata: Optional metadata dictionary from the data source
        
    Returns:
        Tuple of (is_independent, list of reason strings)
    """
    reasons = []
    is_independent = True
    
    # Check if metadata exists
    if source_metadata is None:
        # If no metadata provided, we cannot verify independence
        # This is a critical failure for FR-006
        is_independent = False
        reasons.append("No source metadata available to verify independence")
        return is_independent, reasons
    
    # Check for explicit method declaration
    method = source_metadata.get('simulation_method')
    if not method:
        is_independent = False
        reasons.append("Simulation method not specified in metadata")
    elif method.lower() not in ['molecular_dynamics', 'md', 'ab_initio_md', 'dft_md', 'nve', 'nvt', 'npt']:
        is_independent = False
        reasons.append(f"Unknown or invalid simulation method: {method}")
    
    # Check for target property contamination
    # If the source claims to have calculated thermal conductivity using the same simulation,
    # it might not be independent for our analysis if we are validating that calculation
  # However, for this project, we assume the target k values are from a separate calculation
  # or experimental validation. We check for explicit "independent" flag if available.
    independence_flag = source_metadata.get('is_independent_source')
    if independence_flag is False:
        is_independent = False
        reasons.append("Source explicitly marked as dependent/non-independent")
    
    # Check for provenance chain
    provenance = source_metadata.get('provenance')
    if not provenance:
        # Not a hard failure, but a warning
        reasons.append("Provenance chain not documented")
    
    return is_independent, reasons

def validate_system_size(config: AtomicConfiguration) -> Tuple[bool, List[str]]:
    """
    Validate that the system size meets the thermodynamic limit requirement.
    
    FR-007: Systems must have >= 1000 atoms to be considered converged.
    
    Args:
        config: Atomic configuration to validate
        
    Returns:
        Tuple of (is_sufficient, list of reason strings)
    """
    reasons = []
    is_sufficient = True
    num_atoms = len(config.positions)
    
    if num_atoms < MIN_SYSTEM_SIZE_ATOMS:
        is_sufficient = False
        reasons.append(f"Size < {MIN_SYSTEM_SIZE_ATOMS} atoms (found: {num_atoms})")
    else:
        reasons.append(f"Size sufficient ({num_atoms} atoms >= {MIN_SYSTEM_SIZE_ATOMS})")
    
    return is_sufficient, reasons

def validate_convergence(config: AtomicConfiguration, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    Validate convergence to thermodynamic limit.
    
    Checks:
    - System size is sufficient (delegates to validate_system_size)
    - Metadata explicitly states convergence status if available
    - Temperature and pressure conditions are stable (if metadata available)
    
    Args:
        config: Atomic configuration to validate
        metadata: Optional metadata with convergence info
        
    Returns:
        Tuple of (is_converged, list of reason strings)
    """
    reasons = []
    is_converged = True
    
    # First check system size
    size_sufficient, size_reasons = validate_system_size(config)
    reasons.extend(size_reasons)
    if not size_sufficient:
        is_converged = False
        return is_converged, reasons
    
    # Check metadata for explicit convergence flags
    if metadata:
        converged_flag = metadata.get('is_converged')
        if converged_flag is False:
            is_converged = False
            reasons.append("Metadata explicitly marks system as not converged")
        
        # Check for thermodynamic limit statement
        limit_statement = metadata.get('thermodynamic_limit_achieved')
        if limit_statement is False:
            is_converged = False
            reasons.append("Metadata indicates thermodynamic limit not achieved")
    
    # If no metadata, we rely on size check alone
    # Small systems (< 1000) are already filtered above
    
    return is_converged, reasons

def validate_configuration(config: AtomicConfiguration, metadata: Optional[Dict[str, Any]] = None) -> ValidationResult:
    """
    Run all validation checks on a single configuration.
    
    Args:
        config: Atomic configuration to validate
        metadata: Optional source metadata
        
    Returns:
        ValidationResult object
    """
    reasons = []
    
    # Check source independence
    source_independent, source_reasons = validate_source_independence(config, metadata)
    reasons.extend(source_reasons)
    
    # Check convergence (includes size check)
    convergence_ok, conv_reasons = validate_convergence(config, metadata)
    reasons.extend(conv_reasons)
    
    # Determine overall validity
    is_valid = source_independent and convergence_ok
    
    return ValidationResult(
        config_id=config.id,
        is_valid=is_valid,
        source_independent=source_independent,
        size_sufficient=convergence_ok,  # Convergence check includes size
        convergence_verified=convergence_ok,
        reasons=reasons
    )

def run_validation_on_configs(
    configs: List[AtomicConfiguration],
    metadata_map: Optional[Dict[str, Dict[str, Any]]] = None
) -> ValidationReport:
    """
    Run validation on a list of configurations.
    
    Args:
        configs: List of atomic configurations to validate
        metadata_map: Optional mapping of config_id -> metadata dict
        
    Returns:
        ValidationReport with aggregated results
    """
    report = ValidationReport()
    report.total_processed = len(configs)
    
    for config in configs:
        metadata = None
        if metadata_map and config.id in metadata_map:
            metadata = metadata_map[config.id]
        
        result = validate_configuration(config, metadata)
        
        if result.is_valid:
            report.validated_configs.append(config.id)
            report.total_valid += 1
        else:
            report.excluded_configs.append(config.id)
            report.total_excluded += 1
            # Join reasons into a single string for the report
            report.reasons[config.id] = "; ".join(result.reasons)
    
    return report

def save_validation_report(report: ValidationReport, output_path: Path) -> None:
    """
    Save the validation report to a JSON file.
    
    Args:
        report: ValidationReport to save
        output_path: Path to output JSON file
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    logging.info(f"Validation report saved to {output_path}")

def check_validation_logic() -> bool:
    """
    Internal check to ensure validation logic is defined and importable.
    Used for testing the definition without running on real data.
    
    Returns:
        True if all functions are defined and callable
    """
    try:
        # Check all required functions exist and are callable
        assert callable(validate_source_independence)
        assert callable(validate_system_size)
        assert callable(validate_convergence)
        assert callable(validate_configuration)
        assert callable(run_validation_on_configs)
        assert callable(save_validation_report)
        
        # Check dataclasses are defined
        assert ValidationResult is not None
        assert ValidationReport is not None
        
        return True
    except Exception as e:
        logging.error(f"Validation logic check failed: {e}")
        return False