"""
Synthetic Data Generator for Development Fallback (T005)

This module generates synthetic survey data conforming to the project schema
when real data sources (World Bank LSMS, FAO FIES) are unavailable.

The script is invoked via the command line:

    python code/00_generate_synthetic_data.py --output data/raw/survey_data.csv --n 1000

It writes a CSV file with the requested number of records and records metadata
in ``modeling_log.yaml`` using the shared logging utilities.
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

# Project utilities
from config import get_config, set_random_seed
from logging_config import log_operation, update_log_section


def load_config() -> Dict[str, Any]:
    """Load optional configuration overrides from ``code/config.yaml``."""
    config_path = Path(get_config("config_path", "code/config.yaml"))
    if config_path.is_file():
        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def generate_survey_response(rng: random.Random, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a single synthetic respondent record.

    The fields match the schema defined in ``specs/018-adoption-sustainable-agriculture/contracts/dataset.schema.yaml``.
    """
    # Demographics
    age = rng.randint(20, 70)
    education_years = rng.choice([0, 4, 6, 8, 10, 12, 14, 16])
    farm_size_hectares = rng.uniform(0.1, 50.0)
    household_size = rng.randint(1, 10)

    # Economic indicators
    annual_income_usd = rng.uniform(200, 10_000)
    has_credit_access = rng.choice([0, 1])
    credit_amount_usd = rng.uniform(0, 5_000) if has_credit_access else 0.0

    # Community‑engagement proxies (0‑4 scale)
    extension_visits = rng.randint(0, 12)
    membership_count = rng.randint(0, 3)
    collective_action_score = rng.randint(0, 4)
    knowledge_exchange_score = rng.randint(0, 4)

    # Sustainable practice adoption (binary)
    practices = {
        "organic_fertilizer": rng.choice([0, 1]),
        "crop_rotation": rng.choice([0, 1]),
        "water_conservation": rng.choice([0, 1]),
        "integrated_pest_management": rng.choice([0, 1]),
        "agroforestry": rng.choice([0, 1]),
        "conservation_tillage": rng.choice([0, 1]),
    }
    adoption_binary = int(any(practices.values()))

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
        **practices,
        "adoption_binary": adoption_binary,
        "data_source": "synthetic",
        "generation_timestamp": datetime.utcnow().isoformat(),
    }


def generate_synthetic_dataset(n: int, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Assemble a full synthetic dataset with ``n`` respondents.
    """
    rng = random.Random(config.get("random_seed", 42))
    records = [generate_survey_response(rng, config) for _ in range(n)]
    return pd.DataFrame(records)


@log_operation("synthetic_data_generation_main")
def main() -> None:
    """
    CLI entry point: generate a CSV file of synthetic survey data.

    The function respects command‑line arguments, falls back to configuration
    defaults, and records provenance information in ``modeling_log.yaml``.
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic survey data (fallback when real data cannot be fetched)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/survey_data.csv",
        help="Path to write the synthetic CSV file",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1000,
        help="Number of synthetic respondents to generate",
    )
    args = parser.parse_args()

    # Load optional overrides
    config = load_config()
    n = args.n if args.n is not None else config.get("n_respondents", 1000)
    random_seed = config.get("random_seed", 42)
    set_random_seed(random_seed)

    print(f"Generating {n} synthetic records with seed {random_seed}...")
    df = generate_synthetic_dataset(n, config)

    # Write CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Synthetic data written to {output_path}")

    # Log provenance metadata
    log_path = Path(get_config("modeling_log_path", "modeling_log.yaml"))
    provenance = {
        "source": "synthetic_fallback",
        "n_records": n,
        "random_seed": random_seed,
        "generation_timestamp": datetime.utcnow().isoformat(),
        "schema_version": "1.0",
        "note": "Synthetic data generated as a fallback when real data sources are unavailable.",
    }
    update_log_section("data_source_metadata", {"data_source_metadata": provenance}, log_path=log_path)
    print(f"Modeling log updated at {log_path}")


if __name__ == "__main__":
    main()
