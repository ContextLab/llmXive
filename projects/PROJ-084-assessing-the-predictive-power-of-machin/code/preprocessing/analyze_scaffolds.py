"""
Task T022a: Load and Analyze Scaffold Groups.

This script loads the scaffold groups generated in T010 and the batched reactions
from T021. It identifies scaffold IDs that appear in multiple reaction classes
(cross-class scaffolds) and logs them to a JSON file.

It does NOT exclude these scaffolds but prepares the data for the strict
scaffold-based split in T022b.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any

import pandas as pd

# Project root path handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Ensure output directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            DATA_RESULTS_DIR / f"scaffold_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
    ]
)
logger = logging.getLogger(__name__)

def load_scaffold_groups(path: Path) -> pd.DataFrame:
    """Load scaffold groups parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Scaffold groups file not found: {path}")
    logger.info(f"Loading scaffold groups from {path}")
    df = pd.read_parquet(path)
    required_cols = {"scaffold_id", "reaction_class"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Scaffold groups file missing required columns: {missing}")
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def load_batched_reactions(path: Path) -> pd.DataFrame:
    """Load batched reactions parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Batched reactions file not found: {path}")
    logger.info(f"Loading batched reactions from {path}")
    df = pd.read_parquet(path)
    if "reaction_class" not in df.columns:
        raise ValueError("Batched reactions file missing 'reaction_class' column")
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def analyze_cross_class_scaffolds(scaffold_df: pd.DataFrame, reactions_df: pd.DataFrame) -> List[str]:
    """
    Identify scaffold IDs that appear in multiple reaction_class values.

    The scaffold_df contains the mapping of reactions to scaffolds.
    We group by scaffold_id and count unique reaction_class values.
    """
    logger.info("Analyzing cross-class scaffolds...")

    # Ensure scaffold_id and reaction_class are strings for consistent grouping
    scaffold_df = scaffold_df.copy()
    scaffold_df["scaffold_id"] = scaffold_df["scaffold_id"].astype(str)
    scaffold_df["reaction_class"] = scaffold_df["reaction_class"].astype(str)

    # Group by scaffold_id and collect unique reaction classes
    scaffold_class_groups = scaffold_df.groupby("scaffold_id")["reaction_class"].apply(set).reset_index()
    scaffold_class_groups.columns = ["scaffold_id", "reaction_classes"]

    # Filter for scaffolds with more than one unique reaction class
    cross_class = scaffold_class_groups[scaffold_class_groups["reaction_classes"].apply(len) > 1]

    cross_class_ids = sorted(cross_class["scaffold_id"].tolist())
    logger.info(f"Found {len(cross_class_ids)} scaffold IDs appearing in multiple reaction classes.")

    if len(cross_class_ids) > 0:
        logger.info("Sample cross-class scaffold IDs: " + ", ".join(cross_class_ids[:5]))
        # Log the reaction classes for the first few cross-class scaffolds
        for sid in cross_class_ids[:3]:
            classes = scaffold_class_groups[scaffold_class_groups["scaffold_id"] == sid]["reaction_classes"].iloc[0]
            logger.info(f"  Scaffold {sid} appears in classes: {classes}")

    return cross_class_ids

def save_cross_class_scaffolds(cross_class_ids: List[str], output_path: Path) -> None:
    """Save the list of cross-class scaffold IDs to a JSON file."""
    logger.info(f"Saving cross-class scaffolds to {output_path}")
    output_data = {
        "count": len(cross_class_ids),
        "scaffold_ids": cross_class_ids,
        "generated_at": datetime.now().isoformat(),
        "note": "These scaffolds appear in multiple reaction classes. They will be assigned to a single split in T022b."
    }
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Saved {len(cross_class_ids)} cross-class scaffold IDs.")

def main():
    """Main entry point for T022a."""
    logger.info("Starting T022a: Load and Analyze Scaffold Groups")

    # Define paths
    scaffold_groups_path = DATA_PROCESSED_DIR / "scaffold_groups.parquet"
    batched_reactions_path = DATA_PROCESSED_DIR / "batched_reactions.parquet"
    output_path = DATA_PROCESSED_DIR / "cross_class_scaffolds.json"

    # Verify prerequisites exist
    if not scaffold_groups_path.exists():
        logger.error(f"Prerequisite file missing: {scaffold_groups_path}")
        logger.error("Please ensure T010 (scaffold.py) has completed successfully.")
        sys.exit(1)

    if not batched_reactions_path.exists():
        logger.error(f"Prerequisite file missing: {batched_reactions_path}")
        logger.error("Please ensure T021 (batch_processor.py) has completed successfully.")
        sys.exit(1)

    try:
        # Load data
        scaffold_df = load_scaffold_groups(scaffold_groups_path)
        reactions_df = load_batched_reactions(batched_reactions_path)

        # Analyze
        cross_class_ids = analyze_cross_class_scaffolds(scaffold_df, reactions_df)

        # Save results
        save_cross_class_scaffolds(cross_class_ids, output_path)

        logger.info("T022a completed successfully.")

    except Exception as e:
        logger.error(f"Error during T022a execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
