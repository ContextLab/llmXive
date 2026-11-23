"""
Data models and entities for the Statistical Discrepancies project.

Defines the core data structures (Jurisdiction, Discrepancy) and the
standardized output schema for downstream analysis tasks.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import pandas as pd


class DiscrepancyType(Enum):
    """Enumeration of discrepancy types based on direction."""
    NORMAL = "normal"
    DIRECTIONAL_ANOMALY = "directional_anomaly"  # precinct_sum > county_reported
    MISSING_DATA = "missing_data"


@dataclass
class Jurisdiction:
    """
    Represents a geographic jurisdiction (e.g., County, State) containing
    election data.
    """
    name: str
    state: str
    election_year: int
    level: str = "county"  # e.g., 'county', 'state', 'precinct'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.name, self.state, self.election_year))


@dataclass
class Discrepancy:
    """
    Represents a single discrepancy record between precinct-level sums
    and county-reported totals.

    This class enforces the output schema required for downstream tasks:
    - precinct_sum (float/int)
    - county_reported (float/int)
    - discrepancy_abs (float)
    - discrepancy_pct (float)
    - missing_data (bool)
    """
    jurisdiction: Jurisdiction
    precinct_sum: float
    county_reported: float
    discrepancy_abs: float
    discrepancy_pct: float
    missing_data: bool = False
    discrepancy_type: DiscrepancyType = DiscrepancyType.NORMAL
    raw_row_id: Optional[str] = None  # For traceability

    def __post_init__(self):
        # Ensure discrepancy_abs is always positive magnitude
        if self.precinct_sum > self.county_reported:
            self.discrepancy_type = DiscrepancyType.DIRECTIONAL_ANOMALY
        elif self.missing_data:
            self.discrepancy_type = DiscrepancyType.MISSING_DATA

        # Recalculate discrepancy_abs if not provided or inconsistent
        if self.precinct_sum is not None and self.county_reported is not None:
            self.discrepancy_abs = abs(self.precinct_sum - self.county_reported)
            if self.county_reported != 0:
                self.discrepancy_pct = (self.discrepancy_abs / self.county_reported) * 100
            else:
                self.discrepancy_pct = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any], jurisdiction: Jurisdiction) -> 'Discrepancy':
        """
        Factory method to create a Discrepancy instance from a dictionary
        matching the expected schema.
        """
        return cls(
            jurisdiction=jurisdiction,
            precinct_sum=float(data.get('precinct_sum', 0)),
            county_reported=float(data.get('county_reported', 0)),
            discrepancy_abs=float(data.get('discrepancy_abs', 0.0)),
            discrepancy_pct=float(data.get('discrepancy_pct', 0.0)),
            missing_data=bool(data.get('missing_data', False)),
            raw_row_id=data.get('raw_row_id')
        )


def create_discrepancy_record(
    precinct_sum: float,
    county_reported: float,
    jurisdiction: Jurisdiction,
    missing_data: bool = False
) -> Discrepancy:
    """
    Helper function to create a Discrepancy record with calculated fields.

    Args:
        precinct_sum: Sum of votes from all precincts in the jurisdiction.
        county_reported: Total votes reported by the county.
        jurisdiction: The parent Jurisdiction object.
        missing_data: Flag indicating if data was imputed or missing.

    Returns:
        A fully populated Discrepancy object.
    """
    if missing_data:
        # If missing, we might not have valid sums, but we still create the record
        return Discrepancy(
            jurisdiction=jurisdiction,
            precinct_sum=precinct_sum,
            county_reported=county_reported,
            discrepancy_abs=0.0,
            discrepancy_pct=0.0,
            missing_data=True
        )

    return Discrepancy(
        jurisdiction=jurisdiction,
        precinct_sum=precinct_sum,
        county_reported=county_reported,
        discrepancy_abs=abs(precinct_sum - county_reported),
        discrepancy_pct=(abs(precinct_sum - county_reported) / county_reported * 100) if county_reported != 0 else 0.0,
        missing_data=False
    )


# Schema Definition Constants
# These define the exact column names expected in processed DataFrames
SCHEMA_COLUMNS = [
    'precinct_sum',
    'county_reported',
    'discrepancy_abs',
    'discrepancy_pct',
    'missing_data'
]

SCHEMA_DTYPE_MAP = {
    'precinct_sum': 'float64',
    'county_reported': 'float64',
    'discrepancy_abs': 'float64',
    'discrepancy_pct': 'float64',
    'missing_data': 'boolean'
}

def validate_output_schema(df: pd.DataFrame) -> bool:
    """
    Validates that a DataFrame contains the required schema columns.

    Args:
        df: The DataFrame to validate.

    Returns:
        True if all required columns are present.
    """
    required_cols = set(SCHEMA_COLUMNS)
    actual_cols = set(df.columns)
    return required_cols.issubset(actual_cols)
