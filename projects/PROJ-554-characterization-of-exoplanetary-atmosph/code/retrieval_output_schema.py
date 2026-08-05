"""
Retrieval Output Schema Definition.

This module defines the schema for the output of the atmospheric retrieval process.
It maps the results from petitRADTRANS to a standardized format including:
- log10 water mixing ratio
- Standard deviation (uncertainty)
- Upper limit flag (for censored data/low S/N)

This schema is used by `retrieval_output.py` to serialize results to CSV.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class RetrievalOutputSchema:
    """
    Schema for a single retrieval result row.

    Fields:
        planet_id: Unique identifier for the exoplanet (string).
        log10_water_mixing_ratio: The derived log10 of the water vapor mixing ratio.
            If the value is an upper limit, this contains the limit value.
        std_dev: The 1-sigma standard deviation of the derived parameter.
            For upper limits, this represents the uncertainty in the limit.
        is_upper_limit: Boolean flag. True if the retrieval resulted in an upper limit
            (censored data) due to low S/N or non-convergence, False otherwise.
        snr: Signal-to-Noise ratio of the input spectrum used for this retrieval.
        resolution: Spectral resolution (R) of the input spectrum.
        status: String status code (e.g., "CONVERGED", "UPPER_LIMIT", "FAILED").
    """
    planet_id: str
    log10_water_mixing_ratio: float
    std_dev: float
    is_upper_limit: bool
    snr: float
    resolution: float
    status: str

def map_retrieval_result_to_schema(
    planet_id: str,
    water_mixing_ratio: float,
    std_dev: float,
    is_upper_limit: bool,
    snr: float,
    resolution: float,
    status: str = "CONVERGED"
) -> Dict[str, Any]:
    """
    Maps raw retrieval values to the standardized output schema dictionary.

    Args:
        planet_id: Exoplanet identifier.
        water_mixing_ratio: The log10 water mixing ratio value.
        std_dev: The standard deviation of the value.
        is_upper_limit: Boolean indicating if this is a censored upper limit.
        snr: Signal-to-Noise ratio.
        resolution: Spectral resolution.
        status: Status string.

    Returns:
        Dictionary matching the RetrievalOutputSchema structure.
    """
    if not isinstance(planet_id, str):
        raise ValueError(f"planet_id must be a string, got {type(planet_id)}")
    
    # Ensure numeric types
    try:
        log10_val = float(water_mixing_ratio)
        std_val = float(std_dev)
        snr_val = float(snr)
        res_val = float(resolution)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to convert numeric fields for planet {planet_id}: {e}")
        raise

    return {
        "planet_id": planet_id,
        "log10_water_mixing_ratio": log10_val,
        "std_dev": std_val,
        "is_upper_limit": bool(is_upper_limit),
        "snr": snr_val,
        "resolution": res_val,
        "status": str(status)
    }

def get_schema_columns() -> List[str]:
    """
    Returns the list of column names in the order they should appear in the CSV.
    """
    return [
        "planet_id",
        "log10_water_mixing_ratio",
        "std_dev",
        "is_upper_limit",
        "snr",
        "resolution",
        "status"
    ]

def validate_schema_row(row: Dict[str, Any]) -> bool:
    """
    Validates that a dictionary row conforms to the expected schema types.
    """
    required_fields = get_schema_columns()
    for field in required_fields:
        if field not in row:
            logger.error(f"Missing required field: {field}")
            return False
    
    if not isinstance(row["planet_id"], str):
        return False
    if not isinstance(row["is_upper_limit"], bool):
        return False
    # Numeric checks
    try:
        float(row["log10_water_mixing_ratio"])
        float(row["std_dev"])
        float(row["snr"])
        float(row["resolution"])
    except (TypeError, ValueError):
        return False
        
    return True

# Usage example for documentation
if __name__ == "__main__":
    # Example of creating a valid output row
    sample = map_retrieval_result_to_schema(
        planet_id="HD_209458_b",
        water_mixing_ratio=-4.5,
        std_dev=0.3,
        is_upper_limit=False,
        snr=25.0,
        resolution=100.0,
        status="CONVERGED"
    )
    print("Sample Output Row:", sample)
    
    # Example of an upper limit
    sample_limit = map_retrieval_result_to_schema(
        planet_id="WASP_12_b",
        water_mixing_ratio=-6.0,
        std_dev=0.5,
        is_upper_limit=True,
        snr=5.0,
        resolution=50.0,
        status="UPPER_LIMIT"
    )
    print("Sample Upper Limit Row:", sample_limit)
