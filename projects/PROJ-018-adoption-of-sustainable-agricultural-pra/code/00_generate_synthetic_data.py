"""
Synthetic Data Generator for Development and Testing (FALLBACK ONLY).

NOTE: This script generates synthetic data ONLY when real data sources
(World Bank LSMS, FAO FIES) are unavailable or explicitly requested via --synthetic.
It does NOT replace real data collection but serves as a fallback for pipeline
validation and development.

IMPORTANT: Per project constraints, this generator is the ONLY authorized source
for synthetic input data. All data must be clearly labeled as synthetic in metadata.
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from config import get_config, set_random_seed
from logging_config import update_log_section, log_operation


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML."""
    config = get_config()
    return config.to_dict() if config else {}


def generate_survey_response(seed_offset: int = 0) -> Dict[str, Any]:
    """Generate a single synthetic respondent record for testing."""
    cfg = load_config()
    base_seed = cfg.get("random_seed", 42) + seed_offset
    random.seed(base_seed)

    # Demographics
    age = random.randint(18, 75)
    education_years = random.randint(0, 18)
    farm_size_ha = round(random.uniform(0.1, 50.0), 2)
    income_level = random.choice(["low", "low", "low", "medium", "high"])

    # Engagement proxies (0-5 scale)
    membership = random.randint(0, 5)
    extension_visits = random.randint(0, 10)
    collective_action = random.randint(0, 5)
    knowledge_exchange = random.randint(0, 5)

    # Sustainable practices (binary: 0/1)
    organic_farming = random.randint(0, 1)
    crop_rotation = random.randint(0, 1)
    water_conservation = random.randint(0, 1)
    integrated_pest_management = random.randint(0, 1)

    # Credit access
    credit_access = random.choice([0, 1])

    return {
        "age": age,
        "education_years": education_years,
        "farm_size_ha": farm_size_ha,
        "income_level": income_level,
        "membership": membership,
        "extension_visits": extension_visits,
        "collective_action": collective_action,
        "knowledge_exchange": knowledge_exchange,
        "organic_farming": organic_farming,
        "crop_rotation": crop_rotation,
        "water_conservation": water_conservation,
        "integrated_pest_management": integrated_pest_management,
        "credit_access": credit_access,
        "timestamp": datetime.utcnow().isoformat()
    }


def generate_synthetic_dataset(n: int = 1000, seed: int = 42) -> pd.DataFrame:
    """Generate the full synthetic dataset."""
    set_random_seed(seed)
    records = []
    for i in range(n):
        record = generate_survey_response(seed_offset=i)
        records.append(record)

    df = pd.DataFrame(records)
    return df


@log_operation("synthetic_data_generation_main")
def main():
    """Generate and save synthetic data (FALLBACK ONLY)."""
    parser = argparse.ArgumentParser(description="Generate synthetic survey data")
    parser.add_argument("--n", type=int, default=1000, help="Number of records")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/raw/survey_data.csv", help="Output path")
    args = parser.parse_args()

    cfg = load_config()
    # Override with CLI args if provided
    n = args.n if args.n != 1000 else cfg.get("data", {}).get("n_respondents", 1000)
    seed = args.seed if args.seed != 42 else cfg.get("random_seed", 42)
    output_path = Path(args.output)

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Log start
    update_log_section("data_source_metadata", {
        "synthetic_fallback": {
            "status": "used",
            "reason": "Real data sources unavailable or --synthetic flag set",
            "n_records": n,
            "seed": seed
        }
    })

    # Generate
    df = generate_synthetic_dataset(n=n, seed=seed)

    # Save
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} synthetic records at {output_path}")

    # Log completion
    update_log_section("data_source_metadata", {
        "synthetic_fallback": {
            "status": "completed",
            "output_file": str(output_path),
            "rows": len(df)
        }
    })


if __name__ == "__main__":
    main()