"""
Synthetic Data Generator (T005)

This script creates a synthetic agricultural survey dataset that conforms to the
project's data schema. It is intended as a *fallback* when real data sources
cannot be accessed. The generated CSV is written to the location supplied via
``--output`` (default: ``data/raw/survey_data.csv``) and provenance metadata is
recorded in ``modeling_log.yaml`` using the project's lightweight logging helper.
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

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _load_config_overrides() -> Dict[str, Any]:
    """
    Load optional configuration overrides from ``code/config.yaml``.
    Returns an empty dict if the file does not exist.
    """
    config_path = Path(get_config("config_path", "code/config.yaml"))
    if config_path.is_file():
        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def _generate_survey_response(rng: random.Random, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a single synthetic respondent record.

    The field names are deliberately aligned with the schema located at
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

def _assemble_dataset(n: int, cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    Build a full synthetic dataset with ``n`` respondents.
    """
    rng = random.Random(cfg.get("random_seed", 42))
    records: List[Dict[str, Any]] = [_generate_survey_response(rng, cfg) for _ in range(n)]
    return pd.DataFrame(records)

def _write_provenance(log_path: Path, provenance: Dict[str, Any]) -> None:
    """
    Append provenance information to ``modeling_log.yaml`` under the
    ``data_source_metadata`` key. If the file does not exist, it is created.
    """
    if log_path.is_file():
        with log_path.open("r", encoding="utf-8") as f:
            try:
                log_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                log_data = {}
    else:
        log_data = {}

    # Ensure the top‑level key exists
    log_data.setdefault("data_source_metadata", {})
    # Overwrite/extend with the new provenance entry
    log_data["data_source_metadata"] = provenance

    # Write back atomically
    temp_path = log_path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(log_data, f, default_flow_style=False, sort_keys=False)
    temp_path.replace(log_path)

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------

def main() -> None:
    """
    Generate a synthetic CSV file and record provenance.

    The command line interface mirrors the original specification:

    ``python code/00_generate_synthetic_data.py --output <path> --n <records>``
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

    # Load any configuration overrides (e.g., custom random seed)
    cfg = _load_config_overrides()
    n_records = args.n if args.n is not None else cfg.get("n_respondents", 1000)
    random_seed = cfg.get("random_seed", 42)
    set_random_seed(random_seed)

    print(f"Generating {n_records} synthetic respondents (seed={random_seed})...")
    df = _assemble_dataset(n_records, cfg)

    # Write the CSV
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
    _write_provenance(log_path, provenance)
    print(f"Provenance logged to: {log_path}")

if __name__ == "__main__":
    main()