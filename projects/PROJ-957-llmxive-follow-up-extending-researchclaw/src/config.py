"""
Configuration module for llmXive project.
Single source of truth for experiment parameters.
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """
    Central configuration class for the experiment.
    Loads from environment variables or uses defaults.
    """
    # Dataset configuration
    RESEARCHCLAWBENCH_DATASET_ID: str = "researchclawbench/v1"
    
    # Scientific parameters
    SCIENTIFIC_CORE_MARGIN: int = 5
    
    # Execution limits
    MAX_CONCURRENCY: int = 7
    TIMEOUT_PER_RUN: int = 3600
    TOTAL_WALL_CLOCK_BUDGET: int = 86400
    
    # Expected checksum for data integrity verification (T007b)
    # This is the SHA-256 hash of the canonical ResearchClawBench dataset
    # obtained from the verified source. If the loaded dataset's checksum
    # does not match this value, the Verified Accuracy Gate will fail.
    EXPECTED_DATASET_CHECKSUM: str = (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )

    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from environment variables or return defaults.
        
        Returns:
            Config instance with values from env or defaults.
        """
        config = cls()
        
        # Override with environment variables if present
        if os.getenv("RESEARCHCLAWBENCH_DATASET_ID"):
            config.RESEARCHCLAWBENCH_DATASET_ID = os.getenv("RESEARCHCLAWBENCH_DATASET_ID")
        
        if os.getenv("SCIENTIFIC_CORE_MARGIN"):
            try:
                config.SCIENTIFIC_CORE_MARGIN = int(os.getenv("SCIENTIFIC_CORE_MARGIN"))
            except ValueError:
                pass
        
        if os.getenv("MAX_CONCURRENCY"):
            try:
                config.MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY"))
            except ValueError:
                pass
        
        if os.getenv("TIMEOUT_PER_RUN"):
            try:
                config.TIMEOUT_PER_RUN = int(os.getenv("TIMEOUT_PER_RUN"))
            except ValueError:
                pass
        
        if os.getenv("TOTAL_WALL_CLOCK_BUDGET"):
            try:
                config.TOTAL_WALL_CLOCK_BUDGET = int(os.getenv("TOTAL_WALL_CLOCK_BUDGET"))
            except ValueError:
                pass
        
        if os.getenv("EXPECTED_DATASET_CHECKSUM"):
            config.EXPECTED_DATASET_CHECKSUM = os.getenv("EXPECTED_DATASET_CHECKSUM")
        
        return config


# Module-level instance for convenience
config = Config.load()
