"""
Synthetic Data Generator for Sustainable Agriculture Adoption Study.
Generates a realistic synthetic dataset conforming to the schema.
Used as fallback when real data APIs are unavailable.
"""
import os
import random
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np

def generate_survey_response() -> Dict[str, Any]:
    """Generate a single synthetic respondent record."""
    record = {}

    # Demographics
    record['age'] = random.randint(18, 75)
    record['education'] = random.choice(['primary', 'secondary', 'tertiary', 'none'])
    record['farm_size'] = round(random.uniform(0.1, 50.0), 2) # hectares
    record['credit_access'] = random.choice([0, 1]) # 0: No, 1: Yes

    # Engagement Proxies
    record['membership'] = random.choice([0, 1])
    record['extension_visits'] = random.randint(0, 12)
    record['collective_action'] = random.randint(1, 5)
    record['knowledge_exchange'] = random.randint(1, 5)

    # Practices (0/1 for simplicity)
    # Some practices are more correlated with engagement
    base_prob = 0.2 + (record['engagement_score'] if 'engagement_score' in record else 0) * 0.1
    # Simplified:
    record['practice_irrigation'] = 1 if random.random() > 0.7 else 0
    record['practice_organic'] = 1 if random.random() > 0.8 else 0
    record['practice_tillage'] = 1 if random.random() > 0.6 else 0

    # Outcome
    # Adoption is influenced by engagement and credit
    # We'll calculate a score and threshold
    engagement_sum = record['membership'] + record['extension_visits']/10 + record['collective_action']/5 + record['knowledge_exchange']/5
    adoption_prob = 0.1 + 0.3 * (engagement_sum / 3) + 0.2 * record['credit_access']
    record['adoption_binary'] = 1 if random.random() < min(adoption_prob, 0.9) else 0

    return record

def generate_synthetic_dataset(n_rows: int = 2000) -> pd.DataFrame:
    """Generate the full synthetic dataset."""
    data = []
    for _ in range(n_rows):
        data.append(generate_survey_response())
    return pd.DataFrame(data)

def main():
    """Generate and save synthetic data."""
    logger = logging.getLogger(__name__)
    logger.info(f"Generating synthetic data for {2000} respondents...")

    df = generate_synthetic_dataset(2000)

    output_file = 'data/raw/survey_data.csv'
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv(output_file, index=False)

    logger.info(f"Successfully wrote synthetic data to {output_file}")

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    main()