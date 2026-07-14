"""
Data Cleaning Pipeline for Sustainable Agriculture Survey Data.

This script performs the following steps:
1. Load raw data from data/raw/survey_data.csv
2. Validate required variables
3. Handle missing values (impute or drop)
4. Normalize categorical codes
5. Perform power analysis check
6. Export cleaned data to data/processed/cleaned_data.csv
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Import from local modules
from config import Config, get_config, set_random_seed
from logging_config import update_log_section, initialize_modeling_log, log_operation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('clean_data')

# Required variables for the analysis
REQUIRED_VARIABLES = [
    'age', 'education', 'farm_size', 'credit', 'adoption', 'engagement_items'
]

# Column aliases for flexible matching
COLUMN_ALIASES = {
    'age': ['age', 'respondent_age', 'years_old'],
    'education': ['education', 'years_education', 'edu_level'],
    'farm_size': ['farm_size', 'farm_area', 'land_size', 'hectares'],
    'credit': ['credit', 'access_credit', 'credit_access'],
    'adoption': ['adoption', 'sustainable_practices', 'practice_adoption'],
    'engagement_items': ['engagement_items', 'community_engagement', 'engagement']
}

def load_config() -> Config:
    """Load configuration from YAML file."""
    return get_config()

def load_raw_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """Load raw data from CSV file."""
    if input_path is None:
        config = get_config()
        base_dir = Path(config.get("project_root", "."))
        raw_dir = base_dir / config.get("raw_data_path", "data/raw")
        input_path = raw_dir / "survey_data.csv"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading raw data from: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
    return df

def map_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Map column names to standard names using aliases."""
    mapping = {}
    for standard_name, aliases in COLUMN_ALIASES.items():
        for col in df.columns:
            if col.lower() in [a.lower() for a in aliases]:
                mapping[col] = standard_name
                break

    if mapping:
        logger.info(f"Mapping columns: {mapping}")
        df = df.rename(columns=mapping)

    return df

def validate_variables(df: pd.DataFrame) -> List[str]:
    """Validate that required variables are present in the dataframe."""
    missing = []
    for var in REQUIRED_VARIABLES:
        if var not in df.columns:
            missing.append(var)

    if missing:
        logger.warning(f"Missing required variables: {missing}")
        # Log gaps as per FR-002
        update_log_section("variable_validation", {
            "status": "warning",
            "missing_variables": missing,
            "timestamp": datetime.utcnow().isoformat()
        })
    else:
        logger.info("All required variables present")
        update_log_section("variable_validation", {
            "status": "passed",
            "missing_variables": [],
            "timestamp": datetime.utcnow().isoformat()
        })

    return missing

def calculate_missingness(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate missingness percentage for each column."""
    missingness = {}
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missingness[col] = (missing_count / len(df)) * 100
    return missingness

def handle_missing_values(df: pd.DataFrame, threshold: float = 30.0) -> pd.DataFrame:
    """
    Handle missing values:
    - Drop rows with > threshold% missing values
    - Impute remaining missing values with mean (numeric) or mode (categorical)
    """
    logger.info(f"Handling missing values with threshold: {threshold}%")

    # Calculate missingness per row
    row_missingness = df.isna().sum(axis=1) / len(df.columns) * 100

    # Drop rows with high missingness
    before_drop = len(df)
    df = df[row_missingness <= threshold]
    after_drop = len(df)
    logger.info(f"Dropped {before_drop - after_drop} rows with >{threshold}% missing values")

    # Impute remaining missing values
    for col in df.columns:
        if df[col].isna().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                # Impute numeric with mean
                mean_val = df[col].mean()
                df[col] = df[col].fillna(mean_val)
                logger.info(f"Imputed {col} with mean: {mean_val:.2f}")
            else:
                # Impute categorical with mode
                mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
                df[col] = df[col].fillna(mode_val)
                logger.info(f"Imputed {col} with mode: {mode_val}")

    return df

def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize categorical codes to standard values."""
    logger.info("Normalizing categorical codes")

    # Example normalizations (extend as needed based on data)
    categorical_mappings = {
        'education': {
            'primary': 1, 'secondary': 2, 'tertiary': 3,
            'none': 0, 'illiterate': 0
        },
        'credit': {
            'yes': 1, 'no': 0, 'Y': 1, 'N': 0,
            'true': 1, 'false': 0
        },
        'adoption': {
            'yes': 1, 'no': 0, 'Y': 1, 'N': 0,
            'true': 1, 'false': 0
        }
    }

    for col, mapping in categorical_mappings.items():
        if col in df.columns:
            # Apply mapping where applicable
            for old_val, new_val in mapping.items():
                df.loc[df[col] == old_val, col] = new_val

    return df

def calculate_power_analysis(df: pd.DataFrame, num_predictors: int = 5) -> Dict[str, Any]:
    """
    Calculate power analysis check.

    effective_N_events / num_predictors
    - effective_N_events: count of positive outcomes in adoption_binary
    - If adoption_binary not available, estimate a non-negligible proportion of N

    Returns dict with 'ratio' and 'shortfall' status.
    """
    logger.info("Performing power analysis check")

    # Check if adoption_binary exists (created in later stages, but may be present)
    if 'adoption_binary' in df.columns:
        effective_n_events = df['adoption_binary'].sum()
    else:
        # Estimate: assume a non-negligible proportion (e.g., 20%) of N are events
        # This is a conservative estimate for planning purposes
        estimated_proportion = 0.20
        effective_n_events = int(len(df) * estimated_proportion)
        logger.warning(f"adoption_binary not found. Estimated effective_N_events as {estimated_proportion*100}% of N ({effective_n_events})")

    ratio = effective_n_events / num_predictors if num_predictors > 0 else float('inf')

    result = {
        'effective_N_events': effective_n_events,
        'num_predictors': num_predictors,
        'ratio': ratio,
        'shortfall': ratio < 10
    }

    if result['shortfall']:
        logger.warning(f"Power analysis shortfall: ratio={ratio:.2f} < 10.0")
        logger.warning("This may limit statistical power for detecting effects.")
    else:
        logger.info(f"Power analysis passed: ratio={ratio:.2f} >= 10.0")

    return result

def update_modeling_log_with_power_analysis(power_result: Dict[str, Any], log_path: Optional[Path] = None) -> None:
    """Update modeling_log.yaml with power analysis results."""
    if log_path is None:
        config = get_config()
        base_dir = Path(config.get("project_root", "."))
        log_path = base_dir / config.get("modeling_log_path", "modeling_log.yaml")

    # Load existing log
    if log_path.exists():
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    else:
        log_data = {}

    # Update with power analysis
    log_data['power_analysis'] = power_result

    # Write back
    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated power analysis in modeling log: {log_path}")

def export_cleaned_data(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """Export cleaned data to CSV."""
    if output_path is None:
        config = get_config()
        base_dir = Path(config.get("project_root", "."))
        proc_dir = base_dir / config.get("processed_data_path", "data/processed")
        output_path = proc_dir / "cleaned_data.csv"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Exported cleaned data to: {output_path} ({len(df)} records)")

class CustomDataError(Exception):
    """Custom exception for data-related errors."""
    pass

@log_operation("clean_data_pipeline")
def main(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> pd.DataFrame:
    """Main function to run the data cleaning pipeline."""
    try:
        # Initialize modeling log
        initialize_modeling_log()

        # Set random seed for reproducibility
        config = get_config()
        set_random_seed(config.get("random_seed", 42))

        logger.info("Starting data cleaning pipeline.")

        # Load raw data
        df = load_raw_data(input_path)

        # Map column aliases
        df = map_aliases(df)

        # Validate variables
        missing_vars = validate_variables(df)
        if missing_vars:
            logger.warning(f"Some required variables are missing: {missing_vars}")
            # Continue with available variables, but log the issue

        # Calculate and log missingness
        missingness = calculate_missingness(df)
        logger.info(f"Missingness per column: {missingness}")

        # Handle missing values
        df = handle_missing_values(df)

        # Normalize categorical codes
        df = normalize_categorical_codes(df)

        # Perform power analysis check
        # Estimate number of predictors (will be refined in modeling stage)
        num_predictors = 5  # Default estimate: engagement_score + age + education + farm_size + credit
        power_result = calculate_power_analysis(df, num_predictors)

        # Update modeling log with power analysis
        update_modeling_log_with_power_analysis(power_result)

        # Export cleaned data
        export_cleaned_data(df, output_path)

        logger.info("Data cleaning pipeline completed successfully.")
        update_log_section("data_cleaning", {
            "status": "completed",
            "records_processed": len(df),
            "timestamp": datetime.utcnow().isoformat()
        })

        return df

    except Exception as e:
        logger.error(f"Data cleaning pipeline failed: {str(e)}")
        update_log_section("data_cleaning", {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        raise CustomDataError(f"Data cleaning failed: {str(e)}") from e

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Cleaning Pipeline")
    parser.add_argument("--input", type=str, help="Path to input CSV file")
    parser.add_argument("--output", type=str, help="Path to output CSV file")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None

    main(input_path, output_path)