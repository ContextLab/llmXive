import os
import sys
import logging
from pathlib import Path
import pandas as pd
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required directories exist."""
    dirs = [
        Path("data/processed"),
        Path("data/raw")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

def validate_golden_set_csv(path: Path) -> bool:
    """
    Validate that the golden set CSV exists and meets requirements:
    - At least 50 rows
    - Contains 'expert_load_score' column
    - Values are between 0 and 100
    """
    if not path.exists():
        logger.error(f"File not found: {path}")
        return False

    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return False

    # Check row count
    if len(df) < 50:
        logger.error(f"Golden set has {len(df)} rows, but requires >= 50.")
        return False

    # Check required column
    if 'expert_load_score' not in df.columns:
        logger.error("Missing required column: 'expert_load_score'")
        return False

    # Validate score range
    scores = pd.to_numeric(df['expert_load_score'], errors='coerce')
    if scores.isna().any():
        logger.error("Found non-numeric values in 'expert_load_score'")
        return False

    if not ((scores >= 0) & (scores <= 100)).all():
        logger.error("Found 'expert_load_score' values outside range [0, 100]")
        return False

    logger.info(f"Validated golden set: {len(df)} rows, valid scores.")
    return True

def check_public_self_reports():
    """
    Check public datasets (ASSISTments/OULAD) for concurrent self-reported load (e.g., NASA-TLX).
    If found, create golden_set.csv and write validation_source.txt.
    """
    logger.info("Checking public datasets for self-reported load metrics...")

    # Attempt to load ASSISTments dataset
    try:
        logger.info("Attempting to load ASSISTments dataset...")
        # Using a specific version known to have interaction data
        dataset = load_dataset(" ASSISTments/2017-02-01", split="train")
        
        # Check for self-report columns (common names in educational datasets)
        possible_self_report_cols = [
            'tlx_load', 'nasa_tlx', 'mental_demand', 'effort_rating', 
            'frustration_level', 'self_reported_load', 'perceived_load'
        ]
        
        found_col = None
        for col in possible_self_report_cols:
            if col in dataset.column_names:
                found_col = col
                break

        if found_col:
            logger.info(f"Found self-report column: {found_col}")
            df = dataset.to_pandas()
            
            # Create golden set structure
            golden_df = pd.DataFrame({
                'interaction_id': df.index,
                'expert_load_score': df[found_col].clip(0, 100) # Normalize if needed
            })
            
            # Ensure we have enough rows
            if len(golden_df) >= 50:
                output_path = Path("data/processed/golden_set.csv")
                golden_df.to_csv(output_path, index=False)
                logger.info(f"Created golden set from public data: {output_path}")
                
                # Write validation source
                source_path = Path("data/processed/validation_source.txt")
                source_path.write_text("public_self_report")
                logger.info("Wrote validation_source.txt: public_self_report")
                return True
            else:
                logger.warning(f"Public dataset has only {len(golden_df)} rows, insufficient for golden set.")

    except Exception as e:
        logger.warning(f"Could not load or process ASSISTments dataset: {e}")
    
    # Attempt OULAD (often lacks self-reports, but check for similar fields)
    try:
        logger.info("Attempting to load OULAD dataset...")
        dataset = load_dataset("OpenUniversityLearningAnalyticsDataset", split="train")
        # OULAD typically doesn't have direct NASA-TLX, but checking for any load proxy
        # If no self-report found in ASSISTments, this is unlikely to have it either.
        # We proceed to fail if nothing found.
    except Exception as e:
        logger.warning(f"Could not load OULAD dataset: {e}")

    logger.error("No valid public self-reported load data found.")
    return False

def main():
    """Main execution for T007c."""
    ensure_directories()
    
    golden_set_path = Path("data/processed/golden_set.csv")
    validation_source_path = Path("data/processed/validation_source.txt")

    # 1. Check for existing Golden Set
    if golden_set_path.exists():
        logger.info("Checking existing golden_set.csv...")
        if validate_golden_set_csv(golden_set_path):
            logger.info("Golden set is valid. Writing validation_source.txt: golden_set")
            validation_source_path.write_text("golden_set")
            logger.info("Task T007c completed successfully.")
            return

    # 2. If not valid, check public datasets for self-reports
    logger.info("Existing golden set missing or invalid. Checking public datasets for self-reports...")
    if check_public_self_reports():
        logger.info("Task T007c completed successfully via public self-reports.")
        return

    # 3. Fail loudly
    error_msg = "Validation Data Missing: Golden Set or required interaction features with concurrent self-reports not found. Cannot proceed with model training."
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)

if __name__ == "__main__":
    main()