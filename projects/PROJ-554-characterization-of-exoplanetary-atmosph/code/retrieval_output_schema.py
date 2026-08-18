"""
Schema definition and mapping functions for retrieval output.
Implements T018c: Define output schema mapping for retrieval results.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging
from data_models import RetrievalResult, CensorshipStatus

logger = logging.getLogger(__name__)


@dataclass
class RetrievalOutputSchema:
    """
    Schema for retrieval output as defined in T020.
    
    Columns:
    - planet_name: Name of the exoplanet
    - water_mixing_ratio: log10 water mixing ratio (or None for upper limits)
    - uncertainty: 1-sigma uncertainty interval (or None for upper limits)
    - is_upper_limit: Boolean flag indicating if value is an upper limit
    - detection_limit: The detection limit value in mixing ratio units
    - min_detectable_concentration: Minimum detectable concentration (MDC)
    """
    planet_name: str
    water_mixing_ratio: Optional[float]
    uncertainty: Optional[float]
    is_upper_limit: bool
    detection_limit: Optional[float]
    min_detectable_concentration: Optional[float]


def map_retrieval_result_to_schema(result: RetrievalResult) -> Dict[str, Any]:
    """
    Map a RetrievalResult object to the RetrievalOutputSchema format.
    
    Args:
        result: RetrievalResult object from the retrieval pipeline
        
    Returns:
        Dictionary matching the RetrievalOutputSchema structure
    """
    # Determine if this is an upper limit based on censorship status
    is_upper_limit = result.censorship_status == CensorshipStatus.UPPER_LIMIT
    
    # For upper limits, water_mixing_ratio and uncertainty should be None
    # The detection_limit and min_detectable_concentration are always present
    water_mixing_ratio = None if is_upper_limit else result.water_mixing_ratio
    uncertainty = None if is_upper_limit else result.uncertainty
    
    return {
        'planet_name': result.planet_name,
        'water_mixing_ratio': water_mixing_ratio,
        'uncertainty': uncertainty,
        'is_upper_limit': is_upper_limit,
        'detection_limit': result.detection_limit,
        'min_detectable_concentration': result.min_detectable_concentration
    }


def get_schema_columns() -> List[str]:
    """
    Get the list of column names for the retrieval output CSV.
    
    Returns:
        List of column names in the order they should appear in the CSV
    """
    return [
        'planet_name',
        'water_mixing_ratio',
        'uncertainty',
        'is_upper_limit',
        'detection_limit',
        'min_detectable_concentration'
    ]


def validate_schema_row(row: Dict[str, Any]) -> bool:
    """
    Validate that a row conforms to the retrieval output schema.
    
    Args:
        row: Dictionary representing a single row of data
        
    Returns:
        True if the row is valid, False otherwise
    """
    required_fields = get_schema_columns()
    
    # Check all required fields are present
    for field in required_fields:
        if field not in row:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate data types
    if not isinstance(row['planet_name'], str):
        logger.error("planet_name must be a string")
        return False
    
    if not isinstance(row['is_upper_limit'], bool):
        logger.error("is_upper_limit must be a boolean")
        return False
    
    # Validate numeric fields (allow None for upper limits)
    numeric_fields = ['water_mixing_ratio', 'uncertainty', 'detection_limit', 'min_detectable_concentration']
    for field in numeric_fields:
        if row[field] is not None and not isinstance(row[field], (int, float)):
            logger.error(f"{field} must be a number or None")
            return False
    
    # Consistency check: if is_upper_limit is True, water_mixing_ratio and uncertainty should be None
    if row['is_upper_limit']:
        if row['water_mixing_ratio'] is not None or row['uncertainty'] is not None:
            logger.error("Upper limit rows should have None for water_mixing_ratio and uncertainty")
            return False
    
    return True
