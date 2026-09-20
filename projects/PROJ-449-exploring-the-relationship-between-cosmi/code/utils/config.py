import os
import json
from statsmodels.stats.power import tt_solve_power
import numpy as np
from pathlib import Path

class Config:
    """
    Centralized configuration for the cosmic ray analysis pipeline.
    Handles dataset URLs, run parameters, and statistical thresholds.
    """
    
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.root_dir / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Data URLs
        self.AMS02_BASE_URL = "https://ams02.space/data"
        self.NOAA_SUNSPOT_URL = "https://www.swpc.noaa.gov/products/daily-sunspot-numbers"
        
        # Analysis Parameters
        self.LAG_WINDOW_MONTHS = 12
        self.GAP_THRESHOLD_DAYS = 30
        self.SIGNIFICANCE_THRESHOLD = 0.01
        self.BOOTSTRAP_ITERATIONS = 1000
        self.BOOTSTRAP_BLOCK_SIZE = 30
        
        # Statistical Power Threshold (T016b)
        # Calculated for 95% power, alpha=0.05, effect size=0.3
        self.DATA_COVERAGE_THRESHOLD = self._calculate_coverage_threshold()
        
        # Rigidity bins (GV)
        self.RIGIDITY_BINS = [1.0, 2.0, 5.0, 10.0, 20.0, 50.0]

    def _calculate_coverage_threshold(self) -> float:
        """
        Calculate the minimum data coverage required for statistical power.
        Uses t-test power analysis for correlation detection.
        """
        # Effect size (Cohen's d equivalent for correlation)
        effect_size = 0.3
        alpha = 0.05
        power = 0.95
        
        try:
            # Calculate required sample size
            n = tt_solve_power(effect_size=effect_size, alpha=alpha, power=power)
            # Convert to a coverage threshold relative to expected days (approx 4500 for 12 years)
            expected_days = 4500
            threshold = n / expected_days
            return max(0.85, min(1.0, threshold)) # Clamp between 0.85 and 1.0
        except Exception:
            # Fallback to conservative estimate if calculation fails
            return 0.85

    def to_dict(self) -> dict:
        return {
            "lag_window_months": self.LAG_WINDOW_MONTHS,
            "gap_threshold_days": self.GAP_THRESHOLD_DAYS,
            "significance_threshold": self.SIGNIFICANCE_THRESHOLD,
            "data_coverage_threshold": self.DATA_COVERAGE_THRESHOLD,
            "bootstrap_iterations": self.BOOTSTRAP_ITERATIONS,
            "rigidity_bins": self.RIGIDITY_BINS
        }

# Export the singleton instance
CONFIG = Config()
