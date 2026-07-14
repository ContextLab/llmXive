"""
Synthetic Data Generator (T005)

Generates a synthetic survey dataset that conforms to the project's data
schema when real data sources are unavailable.  The script can be run
directly from the command line:

    python code/00_generate_synthetic_data.py --output data/raw/survey_data.csv --n 1000

The generated CSV is written to the specified ``--output`` path and a
provenance entry is added to ``modeling_log.yaml`` via the shared logging
utilities.
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml

# Project utilities
from config import get_config, set_random_seed

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    """Load optional overrides from ``code/config.yaml`` if it exists."""
    config_path = Path(get_config("config_path", "code/config.yaml"))
    if config_path.is_file():
        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def generate_survey_response(rng: random.Random, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a single synthetic respondent record.

    The fields are aligned with the schema defined in
    ``specs/018-adoption-sustainable-agriculture/contracts/dataset.schema.yaml``.
    """
    # Demographics
    age = rng.randint(20, 70)
    education_years = rng.choice([0, 4, 6, 8, 10, 12, 14, 16])
    farm_size_hectares = round(rng.uniform(0.1, 50.0), 2)
    household_size = rng.randint(1, 10)

    # Economic indicators
    annual_income_usd = round(rng.uniform(200, 10_000), 2)
    has_credit_access = rng.choice([0, 1])
    credit_amount_usd = round(rng.uniform(0, 5_000), 2) if has_credit_access else 0.0

    # Community‑engagement proxies (0‑4 scale)
    extension_visits_12m = rng.randint(0, 12)
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

    respondent_id = f"R{rng.randint(10000, 99999)}"

    record = {
        "respondent_id": respondent_id,
        "age": age,
        "education_years": education_years,
        "farm_size_hectares": farm_size_hectares,
        "household_size": household_size,
        "annual_income_usd": annual_income_usd,
        "has_credit_access": has_credit_access,
        "credit_amount_usd": credit_amount_usd,
        "extension_visits_12m": extension_visits_12m,
        "membership_count": membership_count,
        "collective_action_score": collective_action_score,
        "knowledge_exchange_score": knowledge_exchange_score,
        **practices,
        "adoption_binary": adoption_binary,
        "data_source": "synthetic",
        "generation_timestamp": datetime.utcnow().isoformat(),
    }
    return record

def generate_synthetic_dataset(n: int, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Build a full synthetic dataset with ``n`` respondents.
    """
    rng = random.Random(cfg.get("random_seed", 42))
    records: List[Dict[str, Any]] = [_generate_survey_response(rng, cfg) for _ in range(n)]
    return pd.DataFrame(records)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
@log_operation("synthetic_data_generation_main")
def main() -> None:
    """
    Generate a synthetic CSV file and record provenance metadata.
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic agricultural survey data (fallback when real data cannot be fetched)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/survey_data.csv",
        help="Destination CSV file for the synthetic dataset.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1000,
        help="Number of synthetic respondents to generate.",
    )
    args = parser.parse_args()

    # Load optional configuration overrides
    config_overrides = load_config()
    n = args.n if args.n is not None else config_overrides.get("n_respondents", 1000)
    random_seed = config_overrides.get("random_seed", 42)
    set_random_seed(random_seed)

    print(f"Generating {n} synthetic records with seed {random_seed}...")
    df = generate_synthetic_dataset(n, config_overrides)

    # Write the CSV file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Synthetic dataset written to: {output_path}")

    # Record provenance in the modeling log
    log_path = Path(get_config("modeling_log_path", "modeling_log.yaml"))
    provenance = {
        "source": "synthetic_fallback",
        "n_records": n_records,
        "random_seed": random_seed,
        "generation_timestamp": datetime.utcnow().isoformat(),
        "schema_version": "1.0",
        "note": "Synthetic data generated as a fallback when real data sources are unavailable.",
    }
    update_log_section(
        "data_source_metadata",
        {"data_source_metadata": provenance},
        log_path=log_path,
    )
    print(f"Modeling log updated at {log_path}")

if __name__ == "__main__":
    main()