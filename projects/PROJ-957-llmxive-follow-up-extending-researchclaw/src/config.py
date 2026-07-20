"""
Configuration module for the llmXive project.

This module defines the Config class which serves as the single source of truth
for experiment parameters. It loads values from environment variables or falls back
to defaults.
"""
import os
from typing import Optional

class Config:
    """
    Configuration class for experiment parameters.
    
    Attributes:
        RESEARCHCLAWBENCH_DATASET_ID (str): The Hugging Face dataset ID.
        SCIENTIFIC_CORE_MARGIN (int): Margin for scientific core equivalence test.
        MAX_CONCURRENCY (int): Maximum number of concurrent agent runs.
        TIMEOUT_PER_RUN (int): Timeout in seconds for a single agent run.
        TOTAL_WALL_CLOCK_BUDGET (int): Total time budget in seconds (24 hours).
    """
    
    # Default values
    RESEARCHCLAWBENCH_DATASET_ID: str = "researchclawbench/v1"
    SCIENTIFIC_CORE_MARGIN: int = 5
    MAX_CONCURRENCY: int = 7
    TIMEOUT_PER_RUN: int = 3600
    TOTAL_WALL_CLOCK_BUDGET: int = 86400  # 24 hours in seconds

    def __init__(
        self,
        researchclawbench_dataset_id: Optional[str] = None,
        scientific_core_margin: Optional[int] = None,
        max_concurrency: Optional[int] = None,
        timeout_per_run: Optional[int] = None,
        total_wall_clock_budget: Optional[int] = None,
    ):
        """
        Initialize Config with values from environment variables or defaults.
        
        Args:
            researchclawbench_dataset_id: Override for dataset ID.
            scientific_core_margin: Override for margin.
            max_concurrency: Override for concurrency limit.
            timeout_per_run: Override for timeout.
            total_wall_clock_budget: Override for total budget.
        """
        self.RESEARCHCLAWBENCH_DATASET_ID = (
            researchclawbench_dataset_id
            or os.getenv("RESEARCHCLAWBENCH_DATASET_ID", self.RESEARCHCLAWBENCH_DATASET_ID)
        )
        self.SCIENTIFIC_CORE_MARGIN = (
            scientific_core_margin
            or int(os.getenv("SCIENTIFIC_CORE_MARGIN", self.SCIENTIFIC_CORE_MARGIN))
        )
        self.MAX_CONCURRENCY = (
            max_concurrency
            or int(os.getenv("MAX_CONCURRENCY", self.MAX_CONCURRENCY))
        )
        self.TIMEOUT_PER_RUN = (
            timeout_per_run
            or int(os.getenv("TIMEOUT_PER_RUN", self.TIMEOUT_PER_RUN))
        )
        self.TOTAL_WALL_CLOCK_BUDGET = (
            total_wall_clock_budget
            or int(os.getenv("TOTAL_WALL_CLOCK_BUDGET", self.TOTAL_WALL_CLOCK_BUDGET))
        )

    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from environment variables.
        
        Returns:
            Config: A new Config instance with values from environment or defaults.
        """
        return cls()

    def __repr__(self) -> str:
        return (
            f"Config("
            f"RESEARCHCLAWBENCH_DATASET_ID={self.RESEARCHCLAWBENCH_DATASET_ID}, "
            f"SCIENTIFIC_CORE_MARGIN={self.SCIENTIFIC_CORE_MARGIN}, "
            f"MAX_CONCURRENCY={self.MAX_CONCURRENCY}, "
            f"TIMEOUT_PER_RUN={self.TIMEOUT_PER_RUN}, "
            f"TOTAL_WALL_CLOCK_BUDGET={self.TOTAL_WALL_CLOCK_BUDGET}"
            f")"
        )

# Export the Config class at module level
__all__ = ["Config"]
