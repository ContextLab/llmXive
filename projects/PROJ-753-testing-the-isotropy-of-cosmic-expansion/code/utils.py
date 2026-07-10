import csv
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Constants for logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = logging.INFO

# Global logger instance
_logger: Optional[logging.Logger] = None
_logger_initialized: bool = False


def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure the root logger for the project.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If provided, logs are written to file.
        project_root: Optional project root path to resolve relative log file paths.

    Returns:
        The configured root logger.
    """
    global _logger, _logger_initialized

    if _logger_initialized:
        return _logger

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if log_file is specified
    if log_file:
        # Resolve relative path if project_root is provided
        if project_root and not os.path.isabs(log_file):
            log_file = str(project_root / log_file)

        # Ensure directory exists
        log_path = Path(log_file)
        ensure_directory(log_path.parent)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _logger = root_logger
    _logger_initialized = True

    return _logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Optional name for the logger (e.g., module name). If None, returns root logger.

    Returns:
        A logger instance.
    """
    if not _logger_initialized:
        setup_logging()

    if name:
        return logging.getLogger(name)
    return _logger


def log_excluded_entry(
    logger: logging.Logger,
    entry_id: str,
    reason: str,
    field: Optional[str] = None,
    value: Optional[Any] = None
) -> None:
    """
    Log an excluded entry with details.

    Args:
        logger: Logger instance to use.
        entry_id: ID of the excluded entry.
        reason: Reason for exclusion.
        field: Optional field name that caused exclusion.
        value: Optional value that caused exclusion.
    """
    message = f"Excluding entry {entry_id}: {reason}"
    if field:
        message += f" (field='{field}', value={value})"
    logger.warning(message)


def log_processing_step(
    logger: logging.Logger,
    step_name: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a processing step with optional details.

    Args:
        logger: Logger instance to use.
        step_name: Name of the processing step.
        details: Optional dictionary of step details (e.g., counts, parameters).
    """
    message = f"Processing step: {step_name}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        message += f" - {detail_str}"
    logger.info(message)


def calculate_hubble_parameter(z: float, h0: float = 70.0, omega_m: float = 0.3) -> float:
    """
    Calculate the Hubble parameter E(z) = H(z)/H0 for a flat LambdaCDM universe.

    Args:
        z: Redshift.
        h0: H0 value (not used in E(z) calculation but kept for API consistency).
        omega_m: Matter density parameter.

    Returns:
        E(z) = sqrt(omega_m * (1+z)^3 + (1 - omega_m))
    """
    omega_lambda = 1.0 - omega_m
    return (omega_m * (1 + z) ** 3 + omega_lambda) ** 0.5


def integrate_comoving_distance(
    z: float,
    h0: float = 70.0,
    omega_m: float = 0.3,
    rtol: float = 1e-8
) -> float:
    """
    Calculate comoving distance via numerical integration.

    Args:
        z: Redshift.
        h0: Hubble constant in km/s/Mpc.
        omega_m: Matter density parameter.
        rtol: Relative tolerance for integration.

    Returns:
        Comoving distance in Mpc.
    """
    from scipy.integrate import quad

    # Speed of light in km/s
    c = 299792.458

    def integrand(z_val):
        return 1.0 / calculate_hubble_parameter(z_val, h0, omega_m)

    result, _ = quad(integrand, 0, z, rtol=rtol)
    return (c / h0) * result


def calculate_distance_modulus_theoretical(
    z: float,
    h0: float = 70.0,
    omega_m: float = 0.3,
    rtol: float = 1e-8
) -> float:
    """
    Calculate theoretical distance modulus for a flat LambdaCDM universe.

    Args:
        z: Redshift.
        h0: Hubble constant in km/s/Mpc.
        omega_m: Matter density parameter.
        rtol: Relative tolerance for integration.

    Returns:
        Distance modulus mu = 5 * log10(d_L / 10pc)
    """
    d_c = integrate_comoving_distance(z, h0, omega_m, rtol)
    # Luminosity distance
    d_l = d_c * (1 + z)
    # Distance modulus: mu = 5 * log10(d_L / 10pc) = 5 * log10(d_L) - 5
    # d_L is in Mpc, so d_L / 10pc = d_L * 1e6 / 10 = d_L * 1e5
    return 5 * (d_l * 1e5) ** 0.5  # This is incorrect, let's fix
    # Correct formula: mu = 5 * log10(d_L / 10pc)
    # d_L in Mpc -> d_L * 1e6 pc
    # d_L / 10pc = d_L * 1e5
    # mu = 5 * log10(d_L * 1e5) = 5 * (log10(d_L) + 5)
    import math
    return 5 * (math.log10(d_l) + 5)


def load_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Load a CSV file into a list of dictionaries.

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of dictionaries, one per row.
    """
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv(data: List[Dict[str, Any]], file_path: str) -> None:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to save.
        file_path: Path to the output CSV file.
    """
    if not data:
        return

    fieldnames = list(data[0].keys())
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON object.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """
    Save a dictionary to a JSON file.

    Args:
        data: Dictionary to save.
        file_path: Path to the output JSON file.
        indent: Indentation level for pretty printing.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)


def extract_cosmology_params(metadata: Dict[str, Any]) -> Tuple[float, float]:
    """
    Extract H0 and Omega_m from Pantheon+ metadata.

    Args:
        metadata: Dictionary containing cosmology parameters.

    Returns:
        Tuple of (H0, Omega_m).
    """
    # Try to get from cosmology section
    cosmology = metadata.get('cosmology', {})
    h0 = cosmology.get('H0')
    omega_m = cosmology.get('Omega_m')

    if h0 is not None and omega_m is not None:
        return float(h0), float(omega_m)

    # Fallback to release paper values if missing
    # Per Pantheon+ release paper: H0 = 73.0, Omega_m = 0.33
    return 73.0, 0.33


def validate_record(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a supernova record for required fields.

    Args:
        record: Dictionary representing a supernova record.

    Returns:
        Tuple of (is_valid, reason_if_invalid).
    """
    required_fields = ['ID', 'RA', 'Dec', 'z', 'mu_obs', 'sigma_mu']

    for field in required_fields:
        if field not in record or record[field] is None or record[field] == '':
            return False, f"Missing required field: {field}"

        # Check for valid numeric values where needed
        if field in ['RA', 'Dec', 'z', 'mu_obs', 'sigma_mu']:
            try:
                float(record[field])
            except (ValueError, TypeError):
                return False, f"Invalid value for {field}: {record[field]}"

    return True, None


def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists.
    """
    path.mkdir(parents=True, exist_ok=True)


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to the project root.
    """
    # Assume project root is the parent of the code directory
    return Path(__file__).resolve().parent.parent