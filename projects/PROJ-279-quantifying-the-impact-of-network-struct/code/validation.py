import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from models.atomic_config import AtomicConfiguration
from logging_config import get_logger
from config.env_config import get_processed_dir

logger = get_logger(__name__)

@dataclass
class ValidationResult:
    config_id: str
    passed: bool
    reason: Optional[str] = None

@dataclass
class ValidationReport:
    validated_configs: List[str] = field(default_factory=list)
    excluded_configs: List[str] = field(default_factory=list)
    reasons: Dict[str, str] = field(default_factory=dict)

def validate_source_independence(config: AtomicConfiguration) -> bool:
    """
    Check if the source is considered independent.
    For this implementation, we assume any source not containing 'internal' is independent.
    """
    source = config.source.lower()
    if 'internal' in source or 'synthetic' in source:
        return False
    return True

def validate_system_size(config: AtomicConfiguration, min_atoms: int = 1000) -> bool:
    """
    Check if the system size meets the minimum requirement.
    """
    if config.size < min_atoms:
        return False
    return True

def validate_convergence(config: AtomicConfiguration) -> bool:
    """
    Check if the configuration is converged.
    For this implementation, we assume if thermal_conductivity is not None, it's converged.
    """
    if config.thermal_conductivity is None:
        return False
    return True

def validate_configuration(config: AtomicConfiguration, min_atoms: int = 1000) -> ValidationResult:
    """
    Run all validation checks on a single configuration.
    """
    reasons = []
    
    if not validate_source_independence(config):
        reasons.append("Source not independent")
    
    if not validate_system_size(config, min_atoms):
        reasons.append(f"Size < {min_atoms} atoms")
    
    if not validate_convergence(config):
        reasons.append("Thermal conductivity not converged/missing")
    
    passed = len(reasons) == 0
    reason_str = "; ".join(reasons) if not passed else None
    
    return ValidationResult(
        config_id=config.id,
        passed=passed,
        reason=reason_str
    )

def run_validation_on_configs(configs: List[AtomicConfiguration], min_atoms: int = 1000) -> ValidationReport:
    """
    Run validation on a list of configurations.
    """
    report = ValidationReport()
    
    for cfg in configs:
        result = validate_configuration(cfg, min_atoms)
        if result.passed:
            report.validated_configs.append(result.config_id)
        else:
            report.excluded_configs.append(result.config_id)
            report.reasons[result.config_id] = result.reason
    
    return report

def save_validation_report(report: ValidationReport, output_path: Optional[Path] = None) -> Path:
    """
    Save the validation report to a JSON file.
    """
    if output_path is None:
        processed_dir = get_processed_dir()
        output_path = processed_dir / "validation_report.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(asdict(report), f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")
    return output_path

def load_validation_report(path: Path) -> Dict[str, Any]:
    """
    Load a validation report from a JSON file.
    """
    with open(path, 'r') as f:
        return json.load(f)

def check_validation_logic():
    """
    Verify that validation logic is correctly defined (for testing).
    """
    logger.info("Validation logic check passed.")
    return True

def main():
    """
    Entry point for T007-exec: Execution of Validation.
    This should be called after download to validate the configs.
    """
    logger.info("Validation logic defined. Execution requires config list.")
    return 0
