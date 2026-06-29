"""
Synthetic Data Generator for Sustainable Agriculture Adoption Study.

Generates a realistic synthetic dataset conforming to the project schema
to serve as a fallback when real API data (World Bank LSMS/FAO FIES) is unavailable.

Output:
    data/raw/synthetic_survey_data.csv
"""

import os
import random
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any

import pandas as pd
import numpy as np

# Ensure consistent randomness for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# Constants based on typical survey structures for this domain
COUNTRY_CODES = [
    "ETH", "KEN", "TZA", "UGA", "MWI", "ZMB", "MOZ", "NGA", "GHA", "BFA"
]

# Variable definitions aligned with data-model.md and schema
# 1. Demographics
AGE_MIN, AGE_MAX = 18, 75
EDUCATION_LEVELS = [0, 1, 2, 3, 4]  # None, Primary, Secondary, Tertiary, Post-grad
GENDER = [0, 1]  # 0: Female, 1: Male

# 2. Farm Characteristics
FARM_SIZE_MIN, FARM_SIZE_MAX = 0.1, 20.0  # Hectares
FARM_TYPE = ["crop", "livestock", "mixed"]

# 3. Socio-economic
INCOME_LEVELS = ["low", "medium", "high"]
CREDIT_ACCESS = [0, 1]  # 0: No, 1: Yes

# 4. Community Engagement Proxies (0-4 Likert scale or count)
# Membership in co-op
COOP_MEMBERSHIP = [0, 1]
# Extension visits (count per year)
EXTENSION_VISITS_MIN, EXTENSION_VISITS_MAX = 0, 12
# Collective action participation (0-4 scale)
COLLECTIVE_ACTION = [0, 1, 2, 3, 4]
# Knowledge exchange frequency (0-4 scale)
KNOWLEDGE_EXCHANGE = [0, 1, 2, 3, 4]

# 5. Sustainable Practices (Binary: 0: No, 1: Yes)
PRACTICES = [
    "organic_fertilizer",
    "crop_rotation",
    "conservation_tillage",
    "agroforestry",
    "drought_resistant_varieties",
    "integrated_pest_management"
]

# 6. Outcome
ADOPTION_BINARY = [0, 1]


def generate_survey_response(
    row_id: int,
    country_code: str,
    rng: np.random.Generator
) -> Dict[str, Any]:
    """Generate a single synthetic respondent record."""

    # Demographics
    age = rng.integers(AGE_MIN, AGE_MAX + 1)
    education = rng.choice(EDUCATION_LEVELS, p=[0.1, 0.4, 0.3, 0.15, 0.05])
    gender = rng.choice(GENDER, p=[0.45, 0.55])

    # Farm Characteristics
    farm_size = rng.uniform(FARM_SIZE_MIN, FARM_SIZE_MAX)
    farm_type = rng.choice(FARM_TYPE, p=[0.6, 0.2, 0.2])

    # Socio-economic
    # Correlate income with education and farm size slightly
    income_score = (education * 0.3) + (np.log1p(farm_size) * 0.2)
    income_prob = rng.random()
    if income_score + income_prob > 1.2:
        income = "high"
    elif income_score + income_prob > 0.6:
        income = "medium"
    else:
        income = "low"

    credit_access = 1 if (income != "low" and rng.random() > 0.3) else 0

    # Community Engagement
    # Membership
    coop_membership = rng.choice(COOP_MEMBERSHIP, p=[0.6, 0.4])

    # Extension visits (more likely for larger farms or higher income)
    base_visits = 1 if income == "low" else 3
    extension_visits = rng.poisson(base_visits + (farm_size * 0.2))
    extension_visits = min(extension_visits, EXTENSION_VISITS_MAX)

    # Collective action and Knowledge exchange (correlated with membership)
    if coop_membership == 1:
        collective_action = rng.choice(COLLECTIVE_ACTION, p=[0.1, 0.1, 0.2, 0.3, 0.3])
        knowledge_exchange = rng.choice(KNOWLEDGE_EXCHANGE, p=[0.1, 0.1, 0.2, 0.3, 0.3])
    else:
        collective_action = rng.choice(COLLECTIVE_ACTION, p=[0.4, 0.3, 0.2, 0.05, 0.05])
        knowledge_exchange = rng.choice(KNOWLEDGE_EXCHANGE, p=[0.4, 0.3, 0.2, 0.05, 0.05])

    # Sustainable Practices
    # Probability of adoption increases with engagement, education, and credit
    base_prob = 0.15
    prob_modifier = (
        (education * 0.05) +
        (coop_membership * 0.15) +
        (extension_visits * 0.02) +
        (credit_access * 0.1) +
        (collective_action * 0.02)
    )
    adoption_prob = min(base_prob + prob_modifier, 0.95)

    practices = {}
    for practice in PRACTICES:
        # Some practices are more correlated with specific factors
        p = adoption_prob
        if practice == "organic_fertilizer":
            p += 0.1 if income != "low" else -0.05
        elif practice == "drought_resistant_varieties":
            p += 0.1 if extension_visits > 2 else -0.05
        p = max(0.0, min(1.0, p))
        practices[practice] = 1 if rng.random() < p else 0

    # Adoption Binary: 1 if any practice is adopted
    adoption_binary = 1 if any(practices.values()) else 0

    return {
        "respondent_id": row_id,
        "country_code": country_code,
        "age": age,
        "gender": gender,
        "education_level": education,
        "farm_size_ha": round(farm_size, 2),
        "farm_type": farm_type,
        "income_level": income,
        "credit_access": credit_access,
        "coop_membership": coop_membership,
        "extension_visits_per_year": extension_visits,
        "collective_action_score": collective_action,
        "knowledge_exchange_score": knowledge_exchange,
        **practices,
        "adoption_binary": adoption_binary,
        "survey_date": (datetime.now() - timedelta(days=rng.integers(1, 365))).strftime("%Y-%m-%d")
    }


def generate_synthetic_dataset(n_rows: int = 2000) -> pd.DataFrame:
    """
    Generate the full synthetic dataset.

    Args:
        n_rows: Total number of synthetic respondents to generate.

    Returns:
        pd.DataFrame: The generated dataset.
    """
    data = []
    rng = np.random.default_rng(RANDOM_SEED)

    # Distribute rows across countries
    rows_per_country = n_rows // len(COUNTRY_CODES)
    remainder = n_rows % len(COUNTRY_CODES)

    current_id = 1
    for i, country in enumerate(COUNTRY_CODES):
        count = rows_per_country + (1 if i < remainder else 0)
        for _ in range(count):
            record = generate_survey_response(current_id, country, rng)
            data.append(record)
            current_id += 1

    df = pd.DataFrame(data)
    return df


def main():
    """Main entry point for the script."""
    # Define output paths
    output_dir = "data/raw"
    output_file = os.path.join(output_dir, "synthetic_survey_data.csv")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generating synthetic data for {2000} respondents...")
    df = generate_synthetic_dataset(2000)

    # Validate basic schema constraints (non-null, types)
    assert df["respondent_id"].is_unique, "Respondent IDs must be unique"
    assert not df["country_code"].isna().any(), "Country codes cannot be null"
    assert df["adoption_binary"].isin([0, 1]).all(), "Adoption binary must be 0 or 1"

    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"Successfully wrote synthetic data to {output_file}")
    print(f"Total records: {len(df)}")
    print(f"Adoption rate: {df['adoption_binary'].mean():.2%}")

    # Log metadata
    metadata = {
        "source": "synthetic_generator",
        "script": "00_generate_synthetic_data.py",
        "timestamp": datetime.now().isoformat(),
        "seed": RANDOM_SEED,
        "n_records": len(df),
        "countries": COUNTRY_CODES,
        "limitations": [
            "Data is synthetically generated and does not reflect real-world distributions exactly.",
            "Correlations are heuristic approximations based on literature review.",
            "No real API data was fetched."
        ]
    }

    metadata_path = os.path.join("data", "metadata.yaml")
    with open(metadata_path, "w") as f:
        yaml.dump(metadata, f, default_flow_style=False)
    print(f"Metadata written to {metadata_path}")


if __name__ == "__main__":
    main()