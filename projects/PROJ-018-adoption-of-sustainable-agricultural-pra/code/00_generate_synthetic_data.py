"""Synthetic Data Generator for Development and Testing Purposes.

NOTE: This is a FALLBACK mechanism ONLY when real data sources (World Bank LSMS, FAO FIES) are unavailable.
Per project specifications (FR-001, FR-002), this is a documented limitation and not the primary data source.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml

# Import logging
from logging_config import get_logger, log_operation, initialize_modeling_log, update_log_section


def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {"random_seed": 42, "n_respondents": 500}


def generate_survey_response(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a single synthetic respondent record for testing."""
    random.seed(seed)
    
    # Demographics
    age = random.randint(25, 65)
    education = random.choice([1, 2, 3, 4, 5])  # 1=No formal, 5=University
    
    # Farm characteristics
    farm_size = random.uniform(0.5, 50.0)
    farm_size_category = 1 if farm_size < 2 else (2 if farm_size < 10 else 3)
    
    # Economic factors
    credit_access = random.choice([0, 1])
    
    # Sustainable practices (binary indicators)
    organic_farming = random.randint(0, 1)
    compost_use = random.randint(0, 1)
    rotational_grazing = random.randint(0, 1)
    cover_crops = random.randint(0, 1)
    integrated_pest = random.randint(0, 1)
    conservation_tillage = random.randint(0, 1)
    
    # Community engagement proxies
    community_membership = random.randint(0, 3)
    extension_visits = random.randint(0, 5)
    collective_action = random.randint(0, 2)
    knowledge_sharing = random.randint(0, 3)
    training_hours = random.randint(0, 40)
    
    # Outcome variable (adoption)
    adoption = int(any([organic_farming, compost_use, rotational_grazing, cover_crops, integrated_pest, conservation_tillage]))
    
    # Correlations (make it realistic)
    if education > 3:
        adoption = max(adoption, 1) if random.random() > 0.3 else adoption
    if credit_access == 1:
        adoption = max(adoption, 1) if random.random() > 0.4 else adoption
        
    return {
        "age": age,
        "education": education,
        "farm_size": round(farm_size, 2),
        "farm_size_category": farm_size_category,
        "credit_access": credit_access,
        "organic_farming": organic_farming,
        "compost_use": compost_use,
        "rotational_grazing": rotational_grazing,
        "cover_crops": cover_crops,
        "integrated_pest": integrated_pest,
        "conservation_tillage": conservation_tillage,
        "community_membership": community_membership,
        "extension_visits": extension_visits,
        "collective_action": collective_action,
        "knowledge_sharing": knowledge_sharing,
        "training_hours": training_hours,
        "adoption": adoption
    }


def generate_synthetic_dataset(n_respondents: int, seed: int) -> pd.DataFrame:
    """Generate the full synthetic dataset."""
    records = []
    for i in range(n_respondents):
        record = generate_survey_response(seed + i, {})
        records.append(record)
    return pd.DataFrame(records)


@log_operation
def main():
    """Generate and save synthetic data (FALLBACK ONLY)."""
    logger = get_logger("synthetic_data")
    log_path = "modeling_log.yaml"
    
    if not os.path.exists(log_path):
        initialize_modeling_log(log_path)
    
    config = load_config()
    n_respondents = config.get("n_respondents", 500)
    seed = config.get("random_seed", 42)
    
    logger.log("synthetic_generation_start", {"n_respondents": n_respondents, "seed": seed})
    
    df = generate_synthetic_dataset(n_respondents, seed)
    
    output_path = "data/raw/survey_data.csv"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.log("synthetic_generation_complete", {"path": output_path, "rows": len(df)})
    update_log_section("data_source_metadata", {"synthetic_fallback": {"status": "used", "reason": "Real data sources unavailable"}})


if __name__ == "__main__":
    main()
