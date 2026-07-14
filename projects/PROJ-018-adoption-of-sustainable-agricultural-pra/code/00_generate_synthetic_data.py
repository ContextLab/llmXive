"""
Synthetic Data Generator for Development Fallback (T005)

This module generates synthetic survey data conforming to the project schema
when real data sources (World Bank LSMS, FAO FIES) are unavailable.

NOTE: This script generates synthetic data ONLY when real data fetches fail.
All data is clearly labeled as synthetic in the metadata to prevent
confusion with real-world observations.
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml

# Import from project modules
from config import get_config, set_random_seed
from logging_config import log_operation, update_log_section


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = Path(get_config("config_path", "code/config.yaml"))
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


def generate_survey_response(rng: random.Random, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a single synthetic respondent record conforming to data schema.

    Args:
        rng: Random number generator instance
        config: Configuration dictionary with generation parameters

    Returns:
        Dictionary representing a single survey response
    """
    # Demographics
    age = rng.randint(20, 70)
    education_years = rng.choice([0, 4, 6, 8, 10, 12, 14, 16])
    farm_size_hectares = rng.uniform(0.1, 50.0)
    household_size = rng.randint(1, 10)

    # Economic indicators
    annual_income_usd = rng.uniform(200, 10000)
    has_credit_access = rng.choice([0, 1])
    credit_amount_usd = rng.uniform(0, 5000) if has_credit_access else 0

    # Community engagement proxies (0-4 scale)
    extension_visits = rng.randint(0, 12)
    membership_count = rng.randint(0, 3)
    collective_action_score = rng.randint(0, 4)
    knowledge_exchange_score = rng.randint(0, 4)

    # Sustainable practices (binary: 0/1)
    practices = {
        "organic_fertilizer": rng.choice([0, 1]),
        "crop_rotation": rng.choice([0, 1]),
        "water_conservation": rng.choice([0, 1]),
        "integrated_pest_management": rng.choice([0, 1]),
        "agroforestry": rng.choice([0, 1]),
        "conservation_tillage": rng.choice([0, 1]),
    }

    # Adoption indicator (1 if any practice adopted)
    adoption_binary = 1 if sum(practices.values()) > 0 else 0

    return {
        "respondent_id": f"R{rng.randint(10000, 99999)}",
        "age": age,
        "education_years": education_years,
        "farm_size_hectares": round(farm_size_hectares, 2),
        "household_size": household_size,
        "annual_income_usd": round(annual_income_usd, 2),
        "has_credit_access": has_credit_access,
        "credit_amount_usd": round(credit_amount_usd, 2),
        "extension_visits_12m": extension_visits,
        "membership_count": membership_count,
        "collective_action_score": collective_action_score,
        "knowledge_exchange_score": knowledge_exchange_score,
        **{k: v for k, v in practices.items()},
        "adoption_binary": adoption_binary,
        "data_source": "synthetic",
        "generation_timestamp": datetime.utcnow().isoformat()
    }


def generate_synthetic_dataset(n: int, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate the full synthetic dataset conforming to data schema.

    Args:
        n: Number of records to generate
        config: Configuration dictionary

    Returns:
        Pandas DataFrame with synthetic survey data
    """
    rng = random.Random(config.get("random_seed", 42))
    records = [generate_survey_response(rng, config) for _ in range(n)]
    return pd.DataFrame(records)


@log_operation("synthetic_data_generation_main")
def main() -> None:
    """
    Generate and save synthetic data (FALLBACK ONLY).

    This script creates a CSV file at data/raw/survey_data.csv containing
    synthetic records conforming to the project's data schema.
    """
    parser = argparse.ArgumentParser(description="Generate synthetic survey data")
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/survey_data.csv",
        help="Output file path for synthetic data"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1000,
        help="Number of synthetic records to generate"
    )
    args = parser.parse_args()

    config = load_config()
    n = args.n if args.n else config.get("n_respondents", 1000)
    random_seed = config.get("random_seed", 42)
    set_random_seed(random_seed)

    # Generate data
    print(f"Generating {n} synthetic records with seed {random_seed}...")
    df = generate_synthetic_dataset(n, config)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Saved synthetic data to {output_path}")

    # Update modeling log with metadata
    log_path = Path(get_config("modeling_log_path", "modeling_log.yaml"))
    log_data = {
        "data_source_metadata": {
            "source": "synthetic_fallback",
            "n_records": n,
            "random_seed": random_seed,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "schema_version": "1.0",
            "note": "This is synthetic data used only when real data is unavailable"
        }
    }
    update_log_section("data_source_metadata", log_data, log_path=log_path)
    print(f"Updated modeling log at {log_path}")


if __name__ == "__main__":
    main()
