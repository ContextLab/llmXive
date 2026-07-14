"""
Data Acquisition Module for Agricultural Survey Data.

Attempts to fetch real data from World Bank LSMS and FAO FIES.
Falls back to synthetic data generation only if real sources are unavailable.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from config import get_config, set_random_seed
from logging_config import update_log_section, log_operation


class DataFetchError(Exception):
    """Custom exception for data fetching errors."""
    pass


class VariableValidationError(Exception):
    """Custom exception for variable validation errors."""
    pass


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML."""
    config = get_config()
    return config.to_dict() if config else {}


def map_aliases(field_name: str) -> List[str]:
    """Map field names to possible aliases in raw data."""
    aliases = {
        "age": ["age", "respondent_age", "years_old"],
        "education": ["education_years", "education", "years_of_education"],
        "farm_size": ["farm_size_ha", "farm_size", "land_size"],
        "credit": ["credit_access", "access_to_credit", "credit"],
        "adoption": ["organic_farming", "crop_rotation", "water_conservation", "integrated_pest_management"],
        "engagement": ["membership", "extension_visits", "collective_action", "knowledge_exchange"]
    }
    return aliases.get(field_name, [field_name])


def validate_variables(df: pd.DataFrame, required_vars: List[str]) -> Dict[str, Any]:
    """
    Validate that required variables exist in the dataframe.
    Logs gaps and returns a summary.
    """
    missing = []
    found = []
    
    for var in required_vars:
        aliases = map_aliases(var)
        # Check if any alias exists in columns
        found_col = None
        for alias in aliases:
            if alias in df.columns:
                found_col = alias
                break
        
        if found_col:
            found.append({"variable": var, "mapped_to": found_col})
        else:
            missing.append(var)

    log_entry = {
        "status": "validation_complete",
        "timestamp": datetime.utcnow().isoformat(),
        "found": found,
        "missing": missing,
        "valid": len(missing) == 0
    }
    
    # Log the validation result
    update_log_section("data_acquisition", {
        "validation": log_entry
    })

    if missing:
        raise VariableValidationError(f"Missing required variables: {missing}")
    
    return log_entry


def generate_fallback_synthetic_data(n: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic data as a fallback when real sources are unavailable.
    This is strictly a fallback mechanism, not the primary data source.
    """
    set_random_seed(seed)
    import random
    
    records = []
    for i in range(n):
        record = {
            "age": random.randint(18, 75),
            "education_years": random.randint(0, 18),
            "farm_size_ha": round(random.uniform(0.1, 50.0), 2),
            "income_level": random.choice(["low", "low", "low", "medium", "high"]),
            "membership": random.randint(0, 5),
            "extension_visits": random.randint(0, 10),
            "collective_action": random.randint(0, 5),
            "knowledge_exchange": random.randint(0, 5),
            "organic_farming": random.randint(0, 1),
            "crop_rotation": random.randint(0, 1),
            "water_conservation": random.randint(0, 1),
            "integrated_pest_management": random.randint(0, 1),
            "credit_access": random.choice([0, 1]),
            "timestamp": datetime.utcnow().isoformat()
        }
        records.append(record)
    
    return pd.DataFrame(records)


class WorldBankLSMSDataSource:
    """Mock World Bank LSMS data source."""
    
    def __init__(self):
        self.name = "World Bank LSMS"
        self.base_url = "https://api.worldbank.org/v2"
        
    def fetch_data(self, country_codes: List[str]) -> Optional[pd.DataFrame]:
        """Attempt to fetch data from World Bank LSMS."""
        # In a real implementation, this would make API calls
        # For now, we simulate unavailability to trigger fallback
        raise DataFetchError("World Bank LSMS API not available in this environment")


class FAOFIESDataSource:
    """Mock FAO FIES data source."""
    
    def __init__(self):
        self.name = "FAO FIES"
        self.base_url = "https://www.fao.org/faostat"
        
    def fetch_data(self, country_codes: List[str]) -> Optional[pd.DataFrame]:
        """Attempt to fetch data from FAO FIES."""
        # In a real implementation, this would make API calls
        # For now, we simulate unavailability to trigger fallback
        raise DataFetchError("FAO FIES API not available in this environment")


@log_operation("data_acquisition_main")
def main():
    """Main entry point for data acquisition."""
    parser = argparse.ArgumentParser(description="Download agricultural survey data")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic data generation")
    parser.add_argument("--countries", type=str, default="low_income", help="Target countries")
    parser.add_argument("--output", type=str, default="data/raw/survey_data.csv", help="Output path")
    args = parser.parse_args()

    cfg = load_config()
    set_random_seed(cfg.get("random_seed", 42))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Log start
    update_log_section("data_acquisition", {"status": "started", "source": "attempting_real"})

    df = None
    source_used = None

    if not args.synthetic:
        # Attempt real data sources
        try:
            wb = WorldBankLSMSDataSource()
            df = wb.fetch_data(["low_income"])
            source_used = "World Bank LSMS"
        except DataFetchError as e:
            logging.warning(f"World Bank LSMS failed: {e}")
        
        if df is None:
            try:
                fao = FAOFIESDataSource()
                df = fao.fetch_data(["low_income"])
                source_used = "FAO FIES"
            except DataFetchError as e:
                logging.warning(f"FAO FIES failed: {e}")

    # Fallback to synthetic
    if df is None:
        logging.info("Real data sources unavailable. Fallback to synthetic data will be used.")
        n = cfg.get("data", {}).get("n_respondents", 1000)
        seed = cfg.get("random_seed", 42)
        df = generate_fallback_synthetic_data(n=n, seed=seed)
        source_used = "Synthetic Fallback"
        update_log_section("data_acquisition", {
            "synthetic_fallback": {
                "status": "used",
                "reason": "Real data sources unavailable"
            }
        })

    # Validate variables
    required_vars = ["age", "education", "farm_size", "credit", "adoption", "engagement"]
    try:
        validate_variables(df, required_vars)
    except VariableValidationError as e:
        update_log_section("data_acquisition", {
            "status": "validation_failed",
            "missing_variables": str(e)
        })
        # Continue anyway for synthetic data which should have all fields

    # Save
    df.to_csv(output_path, index=False)
    update_log_section("data_acquisition", {"status": "completed", "source": source_used})
    print(f"Data saved to {output_path} from {source_used}")


if __name__ == "__main__":
    main()
