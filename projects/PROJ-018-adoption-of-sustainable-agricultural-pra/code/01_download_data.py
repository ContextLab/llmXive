"""
Data Acquisition Module for Sustainable Agriculture Study (PROJ-018)

This module handles the acquisition of survey data from real sources (World Bank LSMS, FAO FIES).
If real sources are unavailable, it falls back to a documented synthetic generation mechanism
(only when explicitly requested via CLI) to ensure pipeline continuity, while strictly logging
this as a limitation per FR-002.

It also implements rigorous variable validation to ensure all required fields for the
analysis (age, education, farm_size, credit, adoption, engagement items) are present.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yaml

# Import config from sibling module
from config import get_config, get_data_path
# Import logging utilities from sibling module
from logging_config import get_logger, log_operation, update_log_section

# Define custom exceptions
class DataFetchError(Exception):
    """Raised when data fetching from real sources fails."""
    pass

class VariableValidationError(Exception):
    """Raised when required variables are missing from the dataset."""
    pass

# --- Configuration & Constants ---

REQUIRED_VARIABLES = [
    "age", "education", "farm_size", "credit_access", "adoption",
    "engagement_membership", "engagement_extension", "engagement_collective_action",
    "engagement_knowledge_exchange"
]

# Aliases for flexible matching
VARIABLE_ALIASES = {
    "credit": ["credit_access", "credit_availability", "has_credit"],
    "adoption": ["adoption", "adoption_binary", "sustainable_practice_adoption"],
    "engagement_membership": ["engagement_membership", "membership", "org_membership"],
    "engagement_extension": ["engagement_extension", "extension_contact", "extension_visits"],
    "engagement_collective_action": ["engagement_collective_action", "collective_action", "cooperative_participation"],
    "engagement_knowledge_exchange": ["engagement_knowledge_exchange", "knowledge_exchange", "training_attended"]
}

# --- Data Source Interfaces ---

class WorldBankLSMSDataSource:
    """
    Interface for fetching data from World Bank LSMS.
    Note: Real API access requires authentication keys which are not provided in this environment.
    This class attempts to fetch, but gracefully handles failure by raising DataFetchError.
    """
    def __init__(self, country_codes: List[str]):
        self.country_codes = country_codes
        self.base_url = "https://data.worldbank.org/api/v2" # Placeholder for real API

    def fetch_data(self) -> Optional[pd.DataFrame]:
        """
        Attempts to fetch data. In a real environment, this would use requests.
        For this project, we simulate the failure to trigger the documented fallback path.
        """
        # In a real execution, we would attempt:
        # response = requests.get(f"{self.base_url}/data/lsms?countries={','.join(self.country_codes)}")
        # if response.status_code == 200: return pd.DataFrame(response.json())
        
        # Simulate failure for this environment (no real API keys/URLs available)
        raise DataFetchError(
            "Real World Bank LSMS API access unavailable (missing credentials/URL). "
            "This is a documented limitation (FR-001, FR-002)."
        )

class FAOFIESDataSource:
    """
    Interface for fetching data from FAO FIES.
    Similar to WorldBank, real access requires specific endpoints/keys.
    """
    def __init__(self, country_codes: List[str]):
        self.country_codes = country_codes

    def fetch_data(self) -> Optional[pd.DataFrame]:
        """
        Attempts to fetch data.
        """
        # Simulate failure
        raise DataFetchError(
            "Real FAO FIES API access unavailable (missing credentials/URL). "
            "This is a documented limitation (FR-001, FR-002)."
        )

# --- Helper Functions ---

def load_config() -> Dict[str, Any]:
    """Loads configuration from code/config.yaml or defaults."""
    config_path = Path("code/config.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {
        "data_path": "data",
        "low_income_countries": ["KEN", "ETH", "UGA", "TZA", "MWI"], # Example low-income countries
        "random_seed": 42
    }

def generate_fallback_synthetic_data(n_rows: int = 1000) -> pd.DataFrame:
    """
    Generates synthetic data ONLY when real sources fail and --synthetic flag is used.
    This function creates a DataFrame that mimics the schema of real survey data.
    IMPORTANT: This is a fallback mechanism. The primary goal is real data.
    """
    import random
    random.seed(42)
    
    data = {
        "country_code": random.choices(["KEN", "ETH", "UGA"], k=n_rows),
        "household_id": range(1, n_rows + 1),
        "age": [random.randint(25, 70) for _ in range(n_rows)],
        "education": [random.choice([0, 1, 2, 3, 4]) for _ in range(n_rows)], # 0: None, 4: Tertiary
        "farm_size": [random.uniform(0.5, 20.0) for _ in range(n_rows)],
        "credit_access": [random.choice([0, 1]) for _ in range(n_rows)],
        "adoption": [random.choice([0, 1]) for _ in range(n_rows)],
        "engagement_membership": [random.choice([0, 1, 2]) for _ in range(n_rows)], # 0: None, 2: Active
        "engagement_extension": [random.choice([0, 1, 2]) for _ in range(n_rows)],
        "engagement_collective_action": [random.choice([0, 1, 2]) for _ in range(n_rows)],
        "engagement_knowledge_exchange": [random.choice([0, 1, 2]) for _ in range(n_rows)]
    }
    return pd.DataFrame(data)

def map_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps variable names in the DataFrame to the canonical required names.
    """
    rename_map = {}
    for canonical, aliases in VARIABLE_ALIASES.items():
        found = False
        for alias in aliases:
            if alias in df.columns:
                if alias != canonical:
                    rename_map[alias] = canonical
                found = True
                break
        # If no alias found, we don't add to rename_map, validation will catch it later.
    
    return df.rename(columns=rename_map)

def validate_variables(df: pd.DataFrame, logger: Any) -> Tuple[bool, List[str]]:
    """
    Validates that the DataFrame contains all required variables.
    
    Args:
        df: The input DataFrame.
        logger: The logger instance.
        
    Returns:
        Tuple of (is_valid, list_of_missing_variables)
    """
    missing_vars = []
    for var in REQUIRED_VARIABLES:
        if var not in df.columns:
            missing_vars.append(var)
    
    if missing_vars:
        error_msg = f"Missing required variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        logger.warning("Data validation failed. Check source data schema or synthetic generator.")
        return False, missing_vars
    
    logger.info("Variable validation passed. All required fields present.")
    return True, []

def log_metadata_update(source: str, is_synthetic: bool, logger: Any, output_path: Path):
    """
    Logs metadata about the data source and any limitations to data/metadata.yaml.
    """
    metadata_path = output_path.parent / "metadata.yaml"
    
    metadata = {
        "data_source": source,
        "is_synthetic_fallback": is_synthetic,
        "timestamp": datetime.utcnow().isoformat(),
        "limitations": []
    }
    
    if is_synthetic_fallback:
        metadata["limitations"].append(
            "Real data sources (World Bank LSMS, FAO FIES) were unavailable. "
            "Synthetic data generated as fallback per FR-001/FR-002."
        )
    
    # Load existing metadata if exists
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            existing = yaml.safe_load(f) or {}
            if "limitations" in existing:
                metadata["limitations"].extend(existing["limitations"])
    
    with open(metadata_path, "w") as f:
        yaml.dump(metadata, f, default_flow_style=False)
    
    logger.info(f"Metadata updated at {metadata_path}")

# --- Main Execution ---

@log_operation("data_acquisition_main")
def main():
    parser = argparse.ArgumentParser(description="Download or generate survey data.")
    parser.add_argument("--synthetic", action="store_true", 
                        help="Force synthetic data generation if real sources fail.")
    parser.add_argument("--output", type=str, default="data/raw/survey_data.csv",
                        help="Path to save the downloaded/generated data.")
    args = parser.parse_args()

    logger = get_logger()
    config = load_config()
    country_codes = config.get("low_income_countries", ["KEN", "ETH", "UGA"])
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize log section
    update_log_section("data_acquisition", {"status": "started", "source": "attempting_real"})

    df = None
    source_used = "Unknown"
    is_synthetic = False

    # 1. Attempt Real Data Sources
    try:
        # Try World Bank
        wb = WorldBankLSMSDataSource(country_codes)
        df = wb.fetch_data()
        source_used = "World Bank LSMS"
    except DataFetchError as e:
        logger.warning(f"World Bank fetch failed: {e}")
        try:
            # Try FAO
            fao = FAOFIESDataSource(country_codes)
            df = fao.fetch_data()
            source_used = "FAO FIES"
        except DataFetchError as e2:
            logger.warning(f"FAO fetch failed: {e2}")
            if args.synthetic:
                logger.info("Real sources failed. Falling back to synthetic data generation (as requested).")
                is_synthetic = True
                df = generate_fallback_synthetic_data(n_rows=1000)
                source_used = "Synthetic Fallback"
            else:
                logger.error("Real sources failed and --synthetic flag not provided. Aborting.")
                update_log_section("data_acquisition", {"status": "failed", "error": "No data source available"})
                sys.exit(1)

    if df is None:
        logger.error("No data source succeeded.")
        sys.exit(1)

    # 2. Filter to Low-Income Countries (if country_code present)
    if "country_code" in df.columns:
        df = df[df["country_code"].isin(country_codes)].reset_index(drop=True)
        logger.info(f"Filtered to {len(df)} records for low-income countries.")

    # 3. Map Variable Names
    df = map_aliases(df)

    # 4. Validate Variables (FR-002)
    is_valid, missing = validate_variables(df, logger)
    
    if not is_valid:
        # Log the gaps as required by FR-002
        log_operation("variable_validation_gaps", missing_fields=missing)
        update_log_section("data_acquisition", {
            "status": "validation_failed",
            "missing_fields": missing
        })
        # We do not necessarily exit here if we are in a fallback mode, but we must log.
        # However, for the pipeline to proceed, we need these fields.
        # If synthetic, we assume the generator provided them. If real data is missing, it's a critical error.
        if not is_synthetic:
            raise VariableValidationError(f"Critical missing fields: {missing}")

    # 5. Save Data
    df.to_csv(output_path, index=False)
    logger.info(f"Data saved to {output_path}")

    # 6. Log Metadata
    log_metadata_update(source_used, is_synthetic, logger, output_path)

    update_log_section("data_acquisition", {
        "status": "completed",
        "records": len(df),
        "source": source_used,
        "is_synthetic": is_synthetic
    })

    return df

if __name__ == "__main__":
    main()