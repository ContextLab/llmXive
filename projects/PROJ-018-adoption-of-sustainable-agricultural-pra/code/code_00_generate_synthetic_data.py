"""
Synthetic Data Generator for Sustainable Agriculture Study.

This module provides functions to generate realistic synthetic survey data
for development and testing purposes when real data sources are unavailable.

IMPORTANT: This is a FALLBACK mechanism only. Real research should use
actual survey data from World Bank LSMS or FAO FIES.

Exposed API:
  - load_config: Load configuration for data generation.
  - generate_survey_response: Generate a single respondent record.
  - generate_synthetic_dataset: Generate the full dataset.
  - main: CLI entry point.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml

# Configuration defaults
DEFAULT_CONFIG = {
    "n_respondents": 1000,
    "low_income_countries": ["ETH", "KEN", "TZA", "UGA", "MWI"],
    "random_seed": 42,
    "distributions": {
        "age": {"mean": 45, "std": 15, "min": 18, "max": 80},
        "farm_size_hectares": {"mean": 2.5, "std": 1.5, "min": 0.1, "max": 20},
        "education_years": {"mean": 6, "std": 3, "min": 0, "max": 18},
        "engagement_probability": 0.4,
        "adoption_probability_given_engagement": 0.7,
        "adoption_probability_given_no_engagement": 0.2
    }
}

def load_config(config_path: str | None = None) -> Dict[str, Any]:
    """Load configuration from YAML file or use defaults."""
    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG

def generate_survey_response(
    country: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a single synthetic respondent record.
    
    Creates a realistic profile based on the distributions in config.
    """
    dist = config["distributions"]
    
    # Demographics
    age = int(random.gauss(dist["age"]["mean"], dist["age"]["std"]))
    age = max(dist["age"]["min"], min(dist["age"]["max"], age))
    
    education = int(random.gauss(dist["education_years"]["mean"], dist["education_years"]["std"]))
    education = max(dist["education_years"]["min"], min(dist["education_years"]["max"], education))
    
    farm_size = random.gauss(dist["farm_size_hectares"]["mean"], dist["farm_size_hectares"]["std"])
    farm_size = max(dist["farm_size_hectares"]["min"], farm_size)
    
    # Community Engagement Proxies
    # Membership in cooperative
    membership = 1 if random.random() < 0.3 else 0
    # Extension contact (visited by agent)
    extension_contact = 1 if random.random() < 0.25 else 0
    # Collective action (participated in group activity)
    collective_action = 1 if random.random() < 0.35 else 0
    # Knowledge exchange (attended workshop)
    knowledge_exchange = 1 if random.random() < 0.20 else 0
    
    # Calculate Engagement Score (0-4)
    engagement_score = membership + extension_contact + collective_action + knowledge_exchange
    
    # Adoption of Sustainable Practices
    # Probability depends on engagement
    if engagement_score >= 2:
        adopt_prob = dist["adoption_probability_given_engagement"]
    else:
        adopt_prob = dist["adoption_probability_given_no_engagement"]
    
    adoption_binary = 1 if random.random() < adopt_prob else 0
    
    # Specific practices (if adopted)
    practices = []
    if adoption_binary:
        if random.random() < 0.6: practices.append("crop_rotation")
        if random.random() < 0.5: practices.append("organic_fertilizer")
        if random.random() < 0.4: practices.append("water_conservation")
        if random.random() < 0.3: practices.append("agroforestry")
    
    return {
        "country": country,
        "household_id": f"{country}-{random.randint(10000, 99999)}",
        "age": age,
        "education_years": education,
        "farm_size_hectares": round(farm_size, 2),
        "membership_cooperative": membership,
        "extension_contact": extension_contact,
        "collective_action": collective_action,
        "knowledge_exchange": knowledge_exchange,
        "engagement_score": engagement_score,
        "adoption_binary": adoption_binary,
        "practices_adopted": ",".join(practices) if practices else "",
        "timestamp": datetime.utcnow().isoformat()
    }

def generate_synthetic_dataset(n_respondents: int, config: Dict[str, Any] | None = None) -> pd.DataFrame:
    """
    Generate the full synthetic dataset.
    
    Returns a pandas DataFrame with N respondents.
    """
    if config is None:
        config = load_config()
    
    random.seed(config.get("random_seed", 42))
    
    countries = config["low_income_countries"]
    records = []
    
    for i in range(n_respondents):
        # Distribute respondents somewhat evenly across countries
        country = countries[i % len(countries)]
        record = generate_survey_response(country, config)
        records.append(record)
    
    df = pd.DataFrame(records)
    return df

def main() -> None:
    """Generate and save synthetic data."""
    import logging
    
    # Setup basic logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting synthetic data generation.")
    
    config = load_config()
    n = config.get("n_respondents", 1000)
    
    logger.info(f"Generating {n} synthetic records.")
    
    df = generate_synthetic_dataset(n, config)
    
    # Save to default location
    output_path = Path("data/raw/survey_data.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Synthetic data saved to {output_path}")
    logger.info(f"Shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")

if __name__ == "__main__":
    main()