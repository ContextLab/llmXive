"""
Schema definition for NBER Recession Periods.
Defines the structure for start and end dates of economic recessions.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class RecessionPeriod(BaseModel):
    """
    Represents a specific recession period defined by the NBER.
    
    Attributes:
        start_date: Start date of the recession (YYYY-MM-DD)
        end_date: End date of the recession (YYYY-MM-DD)
        source: Reference to the NBER data source
        notes: Optional notes regarding the specific period
    """
    start_date: str = Field(..., description="Start date of the recession (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date of the recession (YYYY-MM-DD)")
    source: str = Field("NBER", description="Data source")
    notes: Optional[str] = Field(None, description="Additional context")

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator('end_date')
    @classmethod
    def validate_date_order(cls, v, info):
        if 'start_date' in info.data:
            start = datetime.strptime(info.data['start_date'], "%Y-%m-%d")
            end = datetime.strptime(v, "%Y-%m-%d")
            if end < start:
                raise ValueError("End date must be after start date")
        return v
    
    def to_range(self) -> tuple:
        """Returns a tuple of datetime objects."""
        return (
            datetime.strptime(self.start_date, "%Y-%m-%d"),
            datetime.strptime(self.end_date, "%Y-%m-%d")
        )
