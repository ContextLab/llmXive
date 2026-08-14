"""
Schema definition and mapping logic for retrieval output data.

This module defines the strict output schema for atmospheric retrieval results,
ensuring consistent formatting for downstream statistical analysis (US3).
It maps raw RetrievalResult objects (from data_models) to a standardized
dictionary format suitable for CSV serialization and pandas DataFrames.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

from data_models import RetrievalResult, CensorshipStatus

logger = logging.getLogger(__name__)


@dataclass
class RetrievalOutputSchema:
    """
    Strict schema for the retrieval results output (data/processed/retrieval_results.csv).

    Fields:
        planet_name: Unique identifier for the exoplanet.
        equilibrium_temperature: Equilibrium temperature in Kelvin (from metadata).
        metallicity: Host star metallicity [Fe/H].
        snr: Signal-to-noise ratio of the spectrum.
        resolution: Spectral resolution (R).
        log10_water_mixing_ratio: Base-10 logarithm of the water vapor mixing ratio.
            For censored data (upper limits), this holds the limit value.
        water_std_dev: Standard deviation of the retrieved mixing ratio (uncertainty).
            For censored data, this holds the uncertainty of the limit.
        is_upper_limit: Boolean flag. True if the value is a censored upper limit
            (derived from low SNR), False if it is a direct detection.
        retrieval_status: String status of the retrieval run (e.g., 'converged', 'failed', 'upper_limit_derived').
        planet_category: Classification (e.g., 'Hot Jupiter', 'Super Earth').
    """
    planet_name: str
    equilibrium_temperature: float
    metallicity: float
    snr: float
    resolution: float
    log10_water_mixing_ratio: float
    water_std_dev: float
    is_upper_limit: bool
    retrieval_status: str
    planet_category: str


def map_retrieval_result_to_schema(result: RetrievalResult) -> Dict[str, Any]:
    """
    Maps a RetrievalResult dataclass instance to the RetrievalOutputSchema dictionary.

    This function ensures that all fields required for the final CSV output are present
    and correctly typed. It handles the conversion of the CensorshipStatus enum to a
    boolean flag and ensures numerical fields are floats.

    Args:
        result: The raw RetrievalResult object from the retrieval process.

    Returns:
        A dictionary conforming to RetrievalOutputSchema.
    """
    # Determine censorship status
    is_upper_limit = result.censorship_status == CensorshipStatus.UPPER_LIMIT

    # Map the log10 water mixing ratio.
    # If the retrieval failed to converge and we derived an upper limit,
    # result.log10_water_mixing_ratio should already contain the limit value.
    # If it's a direct detection, it contains the retrieved value.
    log10_water = float(result.log10_water_mixing_ratio)
    std_dev = float(result.std_dev)

    # Ensure status string is consistent
    status = result.status or "unknown"

    schema_row = {
        "planet_name": result.planet_name,
        "equilibrium_temperature": float(result.equilibrium_temperature),
        "metallicity": float(result.metallicity),
        "snr": float(result.snr),
        "resolution": float(result.resolution),
        "log10_water_mixing_ratio": log10_water,
        "water_std_dev": std_dev,
        "is_upper_limit": is_upper_limit,
        "retrieval_status": status,
        "planet_category": result.planet_category
    }

    # Validation check to ensure no nulls in critical numeric fields
    for key, value in schema_row.items():
        if key not in ["is_upper_limit", "retrieval_status"]:
            if value is None:
                raise ValueError(f"Schema validation failed: {key} is None for planet {result.planet_name}")

    logger.debug(f"Mapped retrieval result for {result.planet_name} to schema. "
                 f"Upper Limit: {is_upper_limit}, Status: {status}")

    return schema_row


def get_schema_columns() -> List[str]:
    """
    Returns the ordered list of column names expected in the output CSV.

    This ensures the CSV header is consistent across all runs.

    Returns:
        List of column names.
    """
    return [
        "planet_name",
        "equilibrium_temperature",
        "metallicity",
        "snr",
        "resolution",
        "log10_water_mixing_ratio",
        "water_std_dev",
        "is_upper_limit",
        "retrieval_status",
        "planet_category"
    ]


def validate_schema_row(row: Dict[str, Any]) -> bool:
    """
    Validates a dictionary row against the expected schema types.

    Args:
        row: A dictionary representing a row of data.

    Returns:
        True if valid, raises ValueError if invalid.
    """
    required_fields = get_schema_columns()
    missing = [f for f in required_fields if f not in row]
    if missing:
        raise ValueError(f"Schema validation failed: Missing fields {missing}")

    # Type checks
    if not isinstance(row["is_upper_limit"], bool):
        raise ValueError("is_upper_limit must be boolean")

    numeric_fields = [
        "equilibrium_temperature", "metallicity", "snr", "resolution",
        "log10_water_mixing_ratio", "water_std_dev"
    ]
    for field in numeric_fields:
        if not isinstance(row[field], (int, float)):
            raise ValueError(f"Field {field} must be numeric, got {type(row[field])}")

    return True