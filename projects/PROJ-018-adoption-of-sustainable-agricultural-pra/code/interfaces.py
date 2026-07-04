"""
Abstract base class interfaces for data sources in the agricultural adoption study.

This module defines the contract that all data source implementations must follow,
ensuring consistent data fetching and validation across different sources
(e.g., World Bank LSMS, FAO FIES, or synthetic generators).
"""
from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class DataSource(ABC):
    """
    Abstract base class for all data sources in the study.
    
    This interface ensures that all data sources provide a consistent way to
    fetch data and validate it against the project's schema requirements.
    """
    
    @abstractmethod
    def fetch_data(self, country_codes: List[str]) -> pd.DataFrame:
        """
        Fetch survey data for the specified list of country codes.
        
        Args:
            country_codes: List of ISO country codes (e.g., ['KEN', 'UGA', 'TZA'])
                           to fetch data for.
                           
        Returns:
            pd.DataFrame: A pandas DataFrame containing the raw survey data.
                          The DataFrame must conform to the project's dataset schema
                          (see specs/018-adoption-sustainable-agriculture/contracts/dataset.schema.yaml).
                          
        Raises:
            ConnectionError: If the data source is unreachable.
            ValueError: If any of the provided country codes are invalid.
            RuntimeError: If the fetch operation fails for other reasons.
        """
        pass
    
    @abstractmethod
    def validate_schema(self, df: pd.DataFrame) -> bool:
        """
        Validate that the provided DataFrame conforms to the expected schema.
        
        Args:
            df: The DataFrame to validate.
                
        Returns:
            bool: True if the DataFrame conforms to the schema, False otherwise.
                  
        Note:
            This method should check for:
            - Presence of required columns (age, education, farm_size, credit, 
              adoption, engagement items)
            - Correct data types for each column
            - Absence of impossible values (e.g., negative farm sizes)
        """
        pass