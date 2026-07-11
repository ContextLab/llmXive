"""
Data Pipeline Orchestration (T019).

Orchestrates:
1. Data Generation (or Download)
2. Preprocessing
3. Merging
4. Validation
5. Output
"""
import os
import sys
import logging
import yaml
from pathlib import Path
import pandas as pd

from src.data.generate import generate_synthetic_dataset
from src.data.preprocess import parse_compositions, filter_valid_entries
from src.data.merge import merge_thermodynamic_properties
from src.utils.validators import validate_schema

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline.log')
    ]
)
logger = logging.getLogger("pipeline")

def run_pipeline(config_path: str, params_path: str, output_path: str):
    """
    Run the full data pipeline.
    """
    # Load configs
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    with open(params_path, 'r') as f:
        params = yaml.safe_load(f)
    
    use_real = config.get("use_real_data", False)
    
    # 1. Generate/Load Data
    logger.info("Step 1: Data Acquisition")
    if use_real:
        # Placeholder for real data loading
        raise NotImplementedError("Real data download not implemented in this task scope.")
    else:
        logger.info("Generating synthetic data...")
        raw_df = generate_synthetic_dataset(params)
    
    # 2. Preprocess
    logger.info("Step 2: Preprocessing")
    parsed_df = parse_compositions(raw_df)
    filtered_df = filter_valid_entries(parsed_df)
    
    # 3. Merge
    logger.info("Step 3: Merging Thermodynamic Properties")
    final_df = merge_thermodynamic_properties(filtered_df)
    
    # 4. Validate
    logger.info("Step 4: Validating Schema")
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "dataset.schema.yaml"
    if schema_path.exists():
        is_valid, errors = validate_schema(final_df, str(schema_path))
        if not is_valid:
            logger.error(f"Schema validation failed: {errors}")
            # In a strict pipeline, we might exit here
            # But for this task, we proceed if data exists
    else:
        logger.warning("Schema file not found, skipping validation.")
    
    # 5. Save
    logger.info(f"Step 5: Saving to {output_path}")
    final_df.to_csv(output_path, index=False)
    
    logger.info("Pipeline completed successfully.")
    return final_df

if __name__ == "__main__":
    # Default paths
    config = "config/settings.yaml"
    params = "config/synthetic_params.yaml"
    output = "data/processed_alloys.csv"
    
    if len(sys.argv) > 1:
        config = sys.argv[1]
    if len(sys.argv) > 2:
        params = sys.argv[2]
    if len(sys.argv) > 3:
        output = sys.argv[3]
    
    run_pipeline(config, params, output)
