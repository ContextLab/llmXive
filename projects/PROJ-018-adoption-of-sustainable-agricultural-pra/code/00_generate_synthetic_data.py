"""
Synthetic Data Generator for Sustainable Agriculture Adoption Study.

IMPORTANT: This generator creates a REALISTIC synthetic dataset for DEVELOPMENT
and TESTING purposes ONLY. In production, this should be replaced with actual
survey data from World Bank LSMS or FAO FIES APIs.

The generated data conforms to the schema defined in specs/018-adoption-sustainable-agriculture/contracts/dataset.schema.yaml
"""
import os
import random
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any

import pandas as pd

# Low-income country codes (for realistic filtering)
LOW_INCOME_COUNTRIES = ["ETH", "KEN", "UGA", "TZA", "MWI", "ZMW", "ZWE", "MDG", "MLI", "NER"]

# Sustainable practices (binary: 0=not adopted, 1=adopted)
PRACTICES = [
    "practice_organic",
    "practice_conservation",
    "practice_agroforestry",
    "practice_irrigation_efficient",
    "practice_integrated_pest"
]

# Engagement proxies (ordinal: 0-4 scale)
ENGAGEMENT_PROXIES = [
    "membership",       # Community organization membership (0-4)
    "extension",        # Extension service contact frequency (0-4)
    "collective",       # Collective action participation (0-4)
    "knowledge"         # Knowledge exchange frequency (0-4)
]

def generate_survey_response(country_code: str) -> Dict[str, Any]:
    """Generate a single synthetic respondent record."""
    # Demographics
    age = random.randint(25, 70)
    education = random.randint(0, 12)  # Years of education
    farm_size = round(random.uniform(0.5, 10.0), 2)  # Hectares
    
    # Economic factors
    credit = random.choice([0, 1])  # Access to credit
    income = round(random.uniform(500, 5000), 2)  # Annual income (USD)
    
    # Engagement proxies (correlated with education and farm size)
    engagement_base = min(4, max(0, int((education / 12) * 3 + (farm_size / 10) * 2)))
    membership = min(4, max(0, engagement_base + random.randint(-1, 1)))
    extension = min(4, max(0, engagement_base + random.randint(-1, 1)))
    collective = min(4, max(0, engagement_base + random.randint(-1, 1)))
    knowledge = min(4, max(0, engagement_base + random.randint(-1, 1)))
    
    # Sustainable practices (correlated with engagement)
    engagement_score = (membership + extension + collective + knowledge) / 4
    adoption_prob = 0.2 + (engagement_score / 4) * 0.6  # 20% base + up to 60% from engagement
    
    practices = {}
    for practice in PRACTICES:
        practices[practice] = 1 if random.random() < adoption_prob else 0
    
    # Community engagement level (derived)
    community_engagement = "high" if engagement_score >= 3 else "medium" if engagement_score >= 1.5 else "low"
    
    return {
        "country_code": country_code,
        "age": age,
        "education": education,
        "farm_size": farm_size,
        "credit": credit,
        "income": income,
        "membership": membership,
        "extension": extension,
        "collective": collective,
        "knowledge": knowledge,
        "community_engagement": community_engagement,
        **practices
    }

def generate_synthetic_dataset(n_respondents: int = 2000) -> pd.DataFrame:
    """Generate the full synthetic dataset."""
    records = []
    
    for _ in range(n_respondents):
        country = random.choice(LOW_INCOME_COUNTRIES)
        record = generate_survey_response(country)
        records.append(record)
    
    df = pd.DataFrame(records)
    
    # Add metadata
    df["generated_at"] = datetime.now().isoformat()
    df["source"] = "synthetic"
    
    return df

def main():
    """Generate and save synthetic data."""
    import logging
    from config import get_config
    from logging_config import get_logger

    logger = get_logger("synthetic_data")
    config = get_config()
    
    n_respondents = config.get("synthetic", {}).get("n_respondents", 2000)
    output_path = config["data"]["raw"]["survey_data"]
    
    logger.info(f"Generating synthetic data for {n_respondents} respondents...")
    
    df = generate_synthetic_dataset(n_respondents)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic data saved to {output_path}")
    
    # Save metadata
    metadata = {
        "source": "synthetic",
        "n_respondents": n_respondents,
        "countries": LOW_INCOME_COUNTRIES,
        "generated_at": datetime.now().isoformat(),
        "limitations": [
            "This is synthetic data for development and testing only.",
            "In production, replace with real survey data from World Bank LSMS or FAO FIES."
        ]
    }
    
    metadata_path = config["data"]["metadata"]
    with open(metadata_path, "w") as f:
        yaml.dump(metadata, f)
    
    logger.info(f"Metadata saved to {metadata_path}")

if __name__ == "__main__":
    main()