import os
from pathlib import Path
from typing import Dict, Any

def load_paths() -> Dict[str, Any]:
    """
    Returns a dictionary of data and code paths.
    """
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    code_dir = base_dir / "code"
    
    return {
        "raw_data": data_dir / "raw",
        "elemental_properties": data_dir / "elemental_properties",
        "processed": data_dir / "processed",
        "evaluation": data_dir / "evaluation",
        "logs_dir": data_dir / "logs",
        "figures": data_dir / "figures",
        "filtered_data": data_dir / "raw" / "mp-2020.12.1_filtered.csv",
        "computed_descriptors": data_dir / "processed" / "computed_descriptors.csv",
        "metrics_json": data_dir / "evaluation" / "model_metrics.json",
        "dataset_schema": data_dir / "contracts" / "dataset.schema.yaml",
        "model_schema": data_dir / "contracts" / "model_output.schema.yaml",
        "verification_json": data_dir / "evaluation" / "dataset_verification.json",
        "feature_ranking": data_dir / "evaluation" / "feature_ranking.json",
        "figures": data_dir / "figures"
    }

def load_env() -> None:
    """
    Loads environment variables from a .env file if present.
    """
    import dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        dotenv.load_dotenv(env_path)
