"""Synthetic data generator for the agricultural survey.

This script creates a CSV file that conforms to the dataset schema
defined in ``specs/018-adoption-sustainable-agriculture/contracts/dataset.schema.yaml``.
It is used as a fallback when real data cannot be fetched from external APIs.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime
from pathlib import Path
from typing import List

# Logging utilities – tolerant implementation lives in ``code/logging_config.py``
from logging_config import log_operation, update_log_section
from config import ensure_directories

@log_operation
def generate_survey_response(seed: int | None = None) -> dict:
    """Generate a single realistic‑looking survey response.

    The fields are chosen to match the expected schema:
    - ``age``: integer 18‑80
    - ``education_years``: integer 0‑20
    - ``farm_size_ha``: float 0.1‑50 (hectares)
    - ``credit_access``: binary 0/1
    - ``adoption_binary``: binary 0/1 (any sustainable practice reported)
    - ``membership``: binary 0/1 (member of a farmer group)
    - ``extension_visits``: integer 0‑5 (times visited by extension agent)
    - ``collective_action``: binary 0/1 (participated in collective action)
    - ``knowledge_exchange``: integer 0‑10 (frequency of knowledge exchange)
    - ``engagement_score``: float 0‑1 (weighted composite)
    """
    if seed is not None:
        random.seed(seed)

    # Core demographic / farm variables
    age = random.randint(18, 80)
    education_years = random.randint(0, 20)
    farm_size_ha = round(random.uniform(0.1, 50.0), 2)
    credit_access = random.choice([0, 1])

    # Adoption indicator – at least one practice reported
    adoption_binary = random.choice([0, 1])

    # Engagement proxies
    membership = random.choice([0, 1])
    extension_visits = random.randint(0, 5)
    collective_action = random.choice([0, 1])
    knowledge_exchange = random.randint(0, 10)

    # Simple equal‑weight composite (scaled to 0‑1)
    proxy_sum = (
        membership
        + extension_visits / 5
        + collective_action
        + knowledge_exchange / 10
    )
    engagement_score = round(min(proxy_sum / 4, 1.0), 3)

    return {
        "age": age,
        "education_years": education_years,
        "farm_size_ha": farm_size_ha,
        "credit_access": credit_access,
        "adoption_binary": adoption_binary,
        "membership": membership,
        "extension_visits": extension_visits,
        "collective_action": collective_action,
        "knowledge_exchange": knowledge_exchange,
        "engagement_score": engagement_score,
    }

@log_operation
def generate_synthetic_dataset(
    n: int = 1000, seed: int | None = None
) -> List[dict]:
    """Create a list of ``n`` synthetic survey responses."""
    if seed is not None:
        random.seed(seed)
    dataset = [generate_survey_response() for _ in range(n)]
    return dataset

@log_operation
def write_csv(data: List[dict], output_path: Path) -> None:
    """Write the list of dictionaries to a CSV file."""
    if not data:
        raise ValueError("No data to write.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

@log_operation
def write_metadata(
    output_path: Path,
    n: int,
    seed: int | None,
    generation_time: str,
) -> None:
    """Write a small JSON metadata file next to the CSV."""
    meta = {
        "generated_at": generation_time,
        "rows": n,
        "seed": seed,
        "description": "Synthetic fallback dataset for agricultural survey",
    }
    meta_path = output_path.with_suffix(".metadata.json")
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

@log_operation
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic agricultural survey data."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/survey_data.csv",
        help="Path to the CSV file that will be created.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=1000,
        help="Number of synthetic respondents to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args()

    # Ensure standard project directories exist before writing files
    ensure_directories()

    output_path = Path(args.output)
    n = args.rows
    seed = args.seed

    generation_time = datetime.utcnow().isoformat()

    # Generate data
    data = generate_synthetic_dataset(n=n, seed=seed)

    # Persist CSV and accompanying metadata
    write_csv(data, output_path)
    write_metadata(output_path, n=n, seed=seed, generation_time=generation_time)

    # Record the operation in the modeling log
    update_log_section(
        section="synthetic_data_generation",
        data={
            "output_path": str(output_path),
            "rows": n,
            "seed": seed,
            "generated_at": generation_time,
        },
        path=None,
    )

    print(f"Synthetic dataset written to: {output_path}")

if __name__ == "__main__":
    main()
