import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path

# Import from existing sibling module
from primary_dimension_util import derive_primary_dimension_from_metadata, get_derivation_rule_hash, process_dataframe_primary_dimensions

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

def setup_directories(base_path: Path):
    """Ensure required directories exist."""
    (base_path / "data" / "processed").mkdir(parents=True, exist_ok=True)

def load_raw_data(base_path: Path):
    """Load the aligned raw data from parquet."""
    import pandas as pd
    raw_path = base_path / "data" / "processed" / "raw_data.parquet"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    return pd.read_parquet(raw_path)

def derive_primary_dimension(df, logger):
    """
    Derive primary_dimension for each row based on prompt_text.
    Rule: primary_dimension_index = int(hashlib.sha256(prompt_text.encode()).hexdigest(), 16) % 4
    """
    logger.info("Deriving primary dimension from prompt_text...")
    df = process_dataframe_primary_dimensions(df, logger)
    return df

def save_lineage_report(base_path: Path, df, logger):
    """
    Generate and save lineage_report.json.
    Entries: {sample_id, source_type, dimension, derivation_rule, derivation_rule_hash}
    """
    logger.info("Generating lineage report...")
    
    rule_string = "sha256_prompt_text_mod_4_v1"
    rule_hash = get_derivation_rule_hash(rule_string)

    lineage_entries = []
    for _, row in df.iterrows():
        entry = {
            "sample_id": row.get("sample_id", row.get("index")),
            "source_type": "metadata",
            "dimension": row["primary_dimension"],
            "derivation_rule": rule_string,
            "derivation_rule_hash": rule_hash
        }
        lineage_entries.append(entry)

    lineage_path = base_path / "data" / "processed" / "lineage_report.json"
    with open(lineage_path, "w") as f:
        json.dump(lineage_entries, f, indent=2)
    logger.info(f"Lineage report saved to {lineage_path}")

def save_exclusions_log(base_path: Path, df, logger):
    """
    Log exclusions (samples where primary_dimension is null/None) to exclusions_log.json.
    """
    logger.info("Checking for exclusions (null primary dimensions)...")
    
    if "primary_dimension" not in df.columns:
        logger.warning("primary_dimension column not found; no exclusions to log.")
        exclusions = []
    else:
        exclusions = df[df["primary_dimension"].isna()][["sample_id", "excluded_reason"]].to_dict(orient="records")
        # If excluded_reason isn't set, add a default
        for exc in exclusions:
            if "excluded_reason" not in exc:
                exc["excluded_reason"] = "missing_primary_dimension_derivation"

    exclusions_path = base_path / "data" / "processed" / "exclusions_log.json"
    with open(exclusions_path, "w") as f:
        json.dump(exclusions, f, indent=2)
    
    logger.info(f"Exclusions log saved to {exclusions_path} (count: {len(exclusions)})")

def parse_args():
    parser = argparse.ArgumentParser(description="Primary Dimension Identification (T014)")
    parser.add_argument("--base-path", type=str, default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
                        help="Base path of the project")
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    base_path = Path(args.base_path)

    logger.info(f"Starting T014: Primary Dimension Identification at {base_path}")

    setup_directories(base_path)

    try:
        df = load_raw_data(base_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    df = derive_primary_dimension(df, logger)

    # Save the updated dataframe back to raw_data.parquet or a new file?
    # The task says "Derive... Generate lineage report... Log exclusions".
    # It implies the dataframe now has the column. We should update raw_data.parquet 
    # or create a new one if the pipeline expects the column to persist.
    # Given T024 depends on T014 and reads raw_data.parquet, we update it.
    output_path = base_path / "data" / "processed" / "raw_data.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Updated raw_data.parquet with primary_dimension column.")

    save_lineage_report(base_path, df, logger)
    save_exclusions_log(base_path, df, logger)

    logger.info("T014 completed successfully.")

if __name__ == "__main__":
    main()
